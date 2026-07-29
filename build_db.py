"""
build_db.py — PsyScreen-RAG Knowledge Base Builder
====================================================
Run this script ONCE (or whenever you update the knowledge base) to:
1. Load all .txt files from data/knowledge_base/
2. Load any PDF files from data/uploaded_pdfs/
3. Chunk, embed, and store everything in ChromaDB

Usage:
    python build_db.py

Requirements:
    - GEMINI_API_KEY in your .env file
    - pip install -r requirements.txt
"""

import os
import sys
import glob
import time
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from dotenv import load_dotenv

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from google import genai
except ImportError:
    print("ERROR: google-genai package not installed. Run: pip install google-genai")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
# 1. Load API Key
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("[ERROR] GEMINI_API_KEY not found in .env file.")
    print("    Copy .env.example to .env and add your key from https://aistudio.google.com")
    sys.exit(1)

print("[INFO] API Key loaded.")


# ─────────────────────────────────────────────────────────────────────────────
# 2. Custom Embedding Function (with batch support)
# ─────────────────────────────────────────────────────────────────────────────
class GeminiEmbeddingFunction(EmbeddingFunction):
    def __init__(self, key: str):
        self.client = genai.Client(api_key=key)

    def __call__(self, input: Documents) -> Embeddings:
        all_embeddings = []
        batch_size = 90  # Safely below the 100-item API limit

        for i in range(0, len(input), batch_size):
            batch = input[i : i + batch_size]
            print(f"  -> Embedding batch {i // batch_size + 1} ({len(batch)} chunks)...")

            retries = 10
            success = False
            last_error = None
            while retries > 0:
                try:
                    response = self.client.models.embed_content(
                        model="gemini-embedding-001",
                        contents=batch,
                    )
                    all_embeddings.extend([e.values for e in response.embeddings])
                    success = True
                    break
                except Exception as e:
                    last_error = e
                    if "429" in str(e) or "quota" in str(e).lower() or "limit" in str(e).lower():
                        print("     [RATE LIMIT] Waiting 30 seconds before retrying...")
                        time.sleep(30)
                        retries -= 1
                    else:
                        raise e
            
            if not success:
                print("[ERROR] Failed to embed batch after 10 attempts.")
                if last_error:
                    raise last_error
                else:
                    raise Exception("Failed to embed batch")

            time.sleep(10)  # Sleep between batches to respect rate limits

        return all_embeddings


# ─────────────────────────────────────────────────────────────────────────────
# 3. Text Chunking Utility
# ─────────────────────────────────────────────────────────────────────────────
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Split text into overlapping chunks.
    Prefers splitting on paragraph boundaries (double newlines).
    Falls back to character-level chunking if paragraphs are too large.
    """
    chunks = []
    # First try to split by paragraphs
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    current_chunk = ""
    for para in paragraphs:
        # If adding this paragraph would exceed chunk_size, save current and start new
        if len(current_chunk) + len(para) + 2 > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            # Keep the overlap: last `overlap` characters of the current chunk
            current_chunk = current_chunk[-overlap:] + "\n\n" + para
        else:
            current_chunk = current_chunk + "\n\n" + para if current_chunk else para

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    # Handle any individual paragraphs longer than chunk_size
    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= chunk_size:
            final_chunks.append(chunk)
        else:
            # Character-level fallback for very long paragraphs
            for i in range(0, len(chunk), chunk_size - overlap):
                final_chunks.append(chunk[i : i + chunk_size])

    return [c for c in final_chunks if len(c) > 50]  # Filter very short chunks


# ─────────────────────────────────────────────────────────────────────────────
# 4. Load Documents
# ─────────────────────────────────────────────────────────────────────────────
def load_txt_file(filepath: str) -> tuple[str, dict]:
    """Load a .txt file and return (text, metadata)."""
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    filename = os.path.basename(filepath)
    category = filename.replace(".txt", "")
    return text, {"source": filename, "category": category, "type": "text"}


def load_pdf_file(filepath: str) -> tuple[str, dict]:
    """Load a PDF file using pypdf and return (text, metadata)."""
    if PdfReader is None:
        print(f"  ⚠️  pypdf not installed. Skipping PDF: {filepath}")
        return "", {}

    reader = PdfReader(filepath)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

    filename = os.path.basename(filepath)
    return text, {"source": filename, "category": "uploaded_pdf", "type": "pdf"}


# ─────────────────────────────────────────────────────────────────────────────
# 5. Main Build Process
# ─────────────────────────────────────────────────────────────────────────────
def build_database():
    print("\n[BUILDER] PsyScreen-RAG - Knowledge Base Builder")
    print("=" * 50)

    # Collect all documents
    all_chunks = []
    all_metadatas = []
    all_ids = []
    doc_count = 0

    # Load .txt files from knowledge base
    kb_dir = "data/knowledge_base"
    txt_files = glob.glob(os.path.join(kb_dir, "*.txt"))

    if not txt_files:
        print(f"[WARNING] No .txt files found in {kb_dir}/")
    else:
        print(f"\n[LOAD] Loading {len(txt_files)} knowledge base files...")
        for filepath in txt_files:
            print(f"  * {os.path.basename(filepath)}")
            text, metadata = load_txt_file(filepath)
            if text:
                chunks = chunk_text(text, chunk_size=500, overlap=50)
                for i, chunk in enumerate(chunks):
                    all_chunks.append(chunk)
                    all_metadatas.append(metadata)
                    all_ids.append(f"{metadata['category']}_chunk_{doc_count}_{i}")
                doc_count += 1
                print(f"      -> {len(chunks)} chunks created")

    # Load PDF files from uploaded_pdfs directory
    pdf_dir = "data/uploaded_pdfs"
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))

    if pdf_files:
        print(f"\n[LOAD] Loading {len(pdf_files)} PDF files...")
        for filepath in pdf_files:
            print(f"  * {os.path.basename(filepath)}")
            text, metadata = load_pdf_file(filepath)
            if text:
                chunks = chunk_text(text, chunk_size=500, overlap=50)
                for i, chunk in enumerate(chunks):
                    all_chunks.append(chunk)
                    all_metadatas.append(metadata)
                    all_ids.append(f"pdf_{doc_count}_{i}")
                doc_count += 1
                print(f"      -> {len(chunks)} chunks created")
    else:
        print(f"\n[INFO] No PDFs in {pdf_dir}/ - using built-in knowledge base only.")
        print("    (Drop CBT PDF books there and re-run build_db.py to expand the RAG)")

    if not all_chunks:
        print("[ERROR] No content to embed. Exiting.")
        sys.exit(1)

    print(f"\n[STATS] Total chunks to embed: {len(all_chunks)}")

    # ─── Initialize ChromaDB ───────────────────────────────────────────────
    print("\n[DB] Initializing ChromaDB...")
    embedder = GeminiEmbeddingFunction(key=api_key)
    db_client = chromadb.PersistentClient(path="./chroma_db")

    # Delete existing collection to rebuild fresh
    try:
        db_client.delete_collection(name="clinical_manuals")
        print("  * Old collection deleted. Rebuilding fresh...")
    except Exception:
        print("  * Creating new collection...")

    collection = db_client.create_collection(
        name="clinical_manuals",
        embedding_function=embedder,
        metadata={"hnsw:space": "cosine"},
    )

    # ─── Embed and Store ──────────────────────────────────────────────────
    print("\n[EMBED] Embedding and storing chunks...")
    batch_size = 90
    for i in range(0, len(all_chunks), batch_size):
        batch_chunks = all_chunks[i : i + batch_size]
        batch_meta = all_metadatas[i : i + batch_size]
        batch_ids = all_ids[i : i + batch_size]

        collection.add(
            documents=batch_chunks,
            metadatas=batch_meta,
            ids=batch_ids,
        )
        print(f"  [OK] Stored batch {i // batch_size + 1} ({len(batch_chunks)} chunks)")
        time.sleep(1)

    print(f"\n[DONE] {collection.count()} chunks stored in ChromaDB.")
    print("    Collection: 'clinical_manuals'")
    print("    Location:   ./chroma_db/")
    print("\n[RUN] Now run: streamlit run app.py")


if __name__ == "__main__":
    build_database()

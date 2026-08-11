# --- STREAMLIT CLOUD SQLITE PATCH (MUST be first) ---
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass  # Running locally with system sqlite3 — that's fine

import time as _time

import os
import re
import sys
import time
import streamlit as st
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from dotenv import load_dotenv

try:
    from google import genai
    from google.genai import types
except ImportError:
    st.error("❌ google-genai not installed. Run: pip install google-genai")
    st.stop()


# ═══════════════════════════════════════════════════════════════
# 1. PAGE CONFIG & CUSTOM CSS (Glassmorphism & Modern Design System)
# ═══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="PsyScreen-RAG | Mental Health Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

/* ── Global Theme & Reset ── */
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* ── CRITICAL READABILITY OVERRIDE ── */
.stApp, .stApp p, .stApp span, .stApp div, .stApp label,
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] div,
[data-testid="stMarkdownContainer"] li,
.stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown div, .stMarkdown li {
    color: #f8fafc !important;
    -webkit-text-fill-color: #f8fafc !important;
}

/* ── App Deep Mesh Gradient Background ── */
.stApp {
    background: 
        radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.15) 0%, transparent 40%),
        radial-gradient(circle at 90% 80%, rgba(168, 85, 247, 0.15) 0%, transparent 40%),
        radial-gradient(circle at 50% 50%, rgba(14, 165, 233, 0.08) 0%, transparent 60%),
        linear-gradient(135deg, #090d16 0%, #0f172a 50%, #1e1b4b 100%);
    background-attachment: fixed;
}

/* ── Main Container ── */
.block-container {
    padding: 1.8rem 2.5rem 3rem 2.5rem;
    max-width: 960px;
}

/* ── Custom Scrollbar ── */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}
::-webkit-scrollbar-track {
    background: rgba(15, 23, 42, 0.6);
}
::-webkit-scrollbar-thumb {
    background: rgba(99, 102, 241, 0.4);
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(129, 140, 248, 0.7);
}

/* ── Header Banner (Glassmorphic Hero) ── */
.header-banner {
    background: rgba(30, 41, 59, 0.55);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 20px;
    padding: 1.8rem 2rem;
    margin-bottom: 1.5rem;
    text-align: center;
    box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1);
    position: relative;
    overflow: hidden;
}
.header-banner::before {
    content: '';
    position: absolute;
    top: 0; left: -100%; width: 200%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.03), transparent);
    transform: skewX(-15deg);
}
.header-banner h1 {
    background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    margin: 0;
}
.header-banner p {
    color: #94a3b8;
    font-size: 0.9rem;
    margin: 0.4rem 0 0 0;
    font-weight: 400;
}
.header-tags {
    display: flex;
    justify-content: center;
    gap: 0.5rem;
    margin-top: 0.8rem;
    flex-wrap: wrap;
}
.tag-pill {
    background: rgba(99, 102, 241, 0.15);
    border: 1px solid rgba(129, 140, 248, 0.3);
    color: #c7d2fe;
    padding: 0.25rem 0.8rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.02em;
}

/* ── Chat Messages Styling (Solid Dark Slate & Crisp White Text) ── */
[data-testid="stChatMessage"] {
    border-radius: 16px !important;
    margin-bottom: 1rem !important;
    border: 1.5px solid rgba(129, 140, 248, 0.4) !important;
    background: #1e293b !important;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.4) !important;
    padding: 1.2rem 1.5rem !important;
}

[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] div,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] li {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-size: 0.98rem !important;
    line-height: 1.65 !important;
    font-weight: 500 !important;
}

/* ── Score Metric Cards ── */
.metric-card {
    background: rgba(30, 41, 59, 0.6);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(129, 140, 248, 0.25);
    border-radius: 18px;
    padding: 1.4rem 1.6rem;
    text-align: center;
    box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.4);
}
.metric-value {
    font-size: 2.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #38bdf8, #818cf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1;
}
.metric-label {
    font-size: 0.8rem;
    color: #94a3b8;
    margin-top: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-weight: 600;
}

/* ── Severity Badges ── */
.badge {
    display: inline-block;
    padding: 0.35rem 1rem;
    border-radius: 9999px;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    margin-top: 0.5rem;
}
.badge-minimal { background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(74, 222, 128, 0.4); }
.badge-mild    { background: rgba(234, 179, 8, 0.15);  color: #facc15; border: 1px solid rgba(250, 204, 21, 0.4); }
.badge-moderate{ background: rgba(249, 115, 22, 0.15); color: #fb923c; border: 1px solid rgba(251, 146, 60, 0.4); }
.badge-severe  { background: rgba(239, 68, 68, 0.15);  color: #f87171; border: 1px solid rgba(248, 113, 113, 0.4); }

/* ── Crisis Alert ── */
.crisis-alert {
    background: linear-gradient(135deg, rgba(153, 27, 27, 0.4), rgba(127, 29, 29, 0.5));
    backdrop-filter: blur(16px);
    border: 2px solid #f87171;
    border-radius: 18px;
    padding: 1.6rem 2rem;
    margin: 1.2rem 0;
    box-shadow: 0 0 35px rgba(239, 68, 68, 0.3);
    animation: pulse-glow 2.5s infinite alternate;
}
@keyframes pulse-glow {
    0% { border-color: #f87171; box-shadow: 0 0 20px rgba(239, 68, 68, 0.2); }
    100% { border-color: #fca5a5; box-shadow: 0 0 40px rgba(239, 68, 68, 0.5); }
}
.crisis-alert h3 {
    color: #fca5a5;
    margin: 0 0 0.8rem 0;
    font-weight: 800;
}

/* ── Progress Bar ── */
.progress-container {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 9999px;
    height: 10px;
    margin: 0.6rem 0;
    overflow: hidden;
    padding: 2px;
}
.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
    border-radius: 9999px;
    box-shadow: 0 0 12px rgba(129, 140, 248, 0.6);
    transition: width 0.4s ease;
}

/* ── CBT Card ── */
.cbt-card {
    background: rgba(30, 41, 59, 0.5);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(168, 85, 247, 0.3);
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    margin-top: 1rem;
}
.cbt-card h4 {
    color: #c084fc;
    margin: 0 0 0.6rem 0;
    font-weight: 700;
}

/* ── Sidebar Styling ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #090d16 0%, #0f172a 100%) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
}
section[data-testid="stSidebar"] .stMarkdown p {
    color: #94a3b8;
    font-size: 0.85rem;
}

/* ── Status Pill Badge ── */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: rgba(34, 197, 94, 0.1);
    border: 1px solid rgba(34, 197, 94, 0.3);
    color: #4ade80;
    padding: 0.3rem 0.8rem;
    border-radius: 9999px;
    font-size: 0.78rem;
    font-weight: 600;
}
.status-dot {
    width: 7px;
    height: 7px;
    background-color: #22c55e;
    border-radius: 50%;
    box-shadow: 0 0 8px #22c55e;
    animation: blink 2s infinite;
}
@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

/* ── Disclaimer Box ── */
.disclaimer {
    background: rgba(56, 189, 248, 0.08);
    border-left: 4px solid #38bdf8;
    border-radius: 0 12px 12px 0;
    padding: 0.8rem 1rem;
    font-size: 0.8rem;
    color: #bae6fd;
    line-height: 1.5;
    margin: 0.5rem 0;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
    color: white !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.2rem !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 4px 15px rgba(79, 70, 229, 0.3) !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(124, 58, 237, 0.4) !important;
    opacity: 0.95 !important;
}

/* ── Secondary / Option Pill Buttons ── */
.stButton button[kind="secondary"] {
    background: rgba(30, 41, 59, 0.6) !important;
    border: 1px solid rgba(129, 140, 248, 0.3) !important;
    color: #e2e8f0 !important;
    box-shadow: none !important;
}
.stButton button[kind="secondary"]:hover {
    background: rgba(99, 102, 241, 0.25) !important;
    border-color: #818cf8 !important;
    color: #ffffff !important;
}

/* ── Streamlit Header & Bottom Bar Reset ── */
header[data-testid="stHeader"] {
    background: transparent !important;
}

[data-testid="stBottom"],
[data-testid="stBottom"] > div,
.stChatFloatingInputContainer,
footer,
footer > div {
    background: transparent !important;
    background-color: transparent !important;
}

/* ── Chat Input Container Box ── */
[data-testid="stChatInput"],
.stChatInput,
[data-testid="stChatInput"] > div,
[data-baseweb="base-input"],
[data-baseweb="input"] {
    background: #ffffff !important;
    background-color: #ffffff !important;
    border: 1.5px solid rgba(99, 102, 241, 0.4) !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15) !important;
}

/* ── Chat Input Text Area & Input Element (Black Text) ── */
[data-testid="stChatInput"] textarea,
.stChatInput textarea,
[data-testid="stChatInput"] input,
textarea[data-testid="stChatInputTextArea"] {
    background: transparent !important;
    color: #0f172a !important;
    -webkit-text-fill-color: #0f172a !important;
    font-size: 0.98rem !important;
    font-weight: 600 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

/* ── Placeholder Text Color (Dark Slate - High Contrast) ── */
[data-testid="stChatInput"] textarea::placeholder,
.stChatInput textarea::placeholder,
[data-testid="stChatInput"] textarea::-webkit-input-placeholder,
textarea[data-testid="stChatInputTextArea"]::placeholder {
    color: #64748b !important;
    -webkit-text-fill-color: #64748b !important;
    opacity: 1 !important;
}

/* ── Chat Input Submit Button ── */
[data-testid="stChatInput"] button,
[data-testid="stChatInputSubmitButton"] {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4) !important;
    transition: all 0.2s ease !important;
}
[data-testid="stChatInput"] button svg {
    fill: #ffffff !important;
}
[data-testid="stChatInput"] button:hover {
    transform: scale(1.05) !important;
    box-shadow: 0 6px 16px rgba(139, 92, 246, 0.6) !important;
}

/* ── Selectbox ── */
div[data-baseweb="select"] > div {
    background: rgba(30, 41, 59, 0.6) !important;
    border-color: rgba(255, 255, 255, 0.12) !important;
    border-radius: 10px !important;
    color: #f1f5f9 !important;
}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# 2. API KEY LOADING
# ═══════════════════════════════════════════════════════════════
load_dotenv(override=True)
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        api_key = None

if not api_key:
    st.markdown("""
    <div class="header-banner">
        <h1>🧠 PsyScreen-RAG</h1>
        <p>Mental Health Screening & CBT Assistant</p>
    </div>
    """, unsafe_allow_html=True)
    st.error("🚨 **GEMINI_API_KEY not found!**")
    st.markdown("""
    **To set up your API key:**
    1. Get a **free** key from [Google AI Studio](https://aistudio.google.com/app/apikey)
    2. Create a `.env` file in this folder
    3. Add: `GEMINI_API_KEY=your_key_here`
    4. Restart the app
    
    *Or add it to Streamlit Cloud Secrets if deploying online.*
    """)
    st.stop()


# ═══════════════════════════════════════════════════════════════
# 3. CONSTANTS & CLINICAL DATA
# ═══════════════════════════════════════════════════════════════
PHQ9_QUESTIONS = [
    "Little interest or pleasure in doing things?",
    "Feeling down, depressed, or hopeless?",
    "Trouble falling or staying asleep, or sleeping too much?",
    "Feeling tired or having little energy?",
    "Poor appetite or overeating?",
    "Feeling bad about yourself — or that you are a failure or have let yourself or your family down?",
    "Trouble concentrating on things, such as reading the newspaper or watching television?",
    "Moving or speaking so slowly that other people could have noticed? Or the opposite — being so fidgety or restless that you have been moving around a lot more than usual?",
    "Thoughts that you would be better off dead or of hurting yourself in some way?",
]

GAD7_QUESTIONS = [
    "Feeling nervous, anxious, or on edge?",
    "Not being able to stop or control worrying?",
    "Worrying too much about different things?",
    "Trouble relaxing?",
    "Being so restless that it is hard to sit still?",
    "Becoming easily annoyed or irritable?",
    "Feeling afraid, as if something awful might happen?",
]

RESPONSE_OPTIONS = {
    "Not at all": 0,
    "Several days": 1,
    "More than half the days": 2,
    "Nearly every day": 3,
}

# Crisis keywords (English + Roman Urdu + Urdu transliterated)
CRISIS_KEYWORDS = [
    r'\bsuicid\b', r'\bself.?harm\b', r'\bhurt myself\b', r'\bkill myself\b',
    r'\bend my life\b', r'\btake my life\b', r'\bwant to die\b', r'\bwish i was dead\b',
    r'\bno reason to live\b', r'\bbetter off dead\b', r'\boverdose\b',
    # Roman Urdu
    r'khudkushi', r'khud.?kushi', r'marna chahta', r'marna chahti',
    r'zindagi khatam', r'jina nahi chahta', r'jina nahi chahti',
    r'apne aap ko hurt', r'maut ki tamanna', r'dunya se chala jana',
    r'apne aap ko nuksaan', r'khud ko nuksaan', r'khud ko takleef',
    # Urdu (romanized)
    r'khatam karna chahta', r'khatam karna chahti',
]

CRISIS_PATTERN = re.compile('|'.join(CRISIS_KEYWORDS), re.IGNORECASE)

SCORE_RESPONSE_MAP = {
    "not at all": 0, "bilkul nahi": 0, "nahi": 0, "no": 0, "na": 0,
    "several days": 1, "kuch din": 1, "kuch baar": 1, "kabhi kabhi": 1,
    "thoda": 1, "sometimes": 1, "kbhi kbhi": 1,
    "more than half the days": 2, "adhe se zyada": 2, "zyada tar": 2,
    "aksar": 2, "mostly": 2, "often": 2, "half": 2,
    "nearly every day": 3, "hamesha": 3, "har roz": 3, "roz": 3,
    "every day": 3, "always": 3, "baar baar": 3, "daily": 3,
    # Numeric shortcuts
    "0": 0, "1": 1, "2": 2, "3": 3,
}

PHQ9_SEVERITY = [
    (4,  "Minimal", "minimal", "✅"),
    (9,  "Mild", "mild", "🟡"),
    (14, "Moderate", "moderate", "🟠"),
    (19, "Moderately Severe", "severe", "🔴"),
    (27, "Severe", "severe", "🚨"),
]

GAD7_SEVERITY = [
    (4,  "Minimal", "minimal", "✅"),
    (9,  "Mild", "mild", "🟡"),
    (14, "Moderate", "moderate", "🟠"),
    (21, "Severe", "severe", "🔴"),
]


# ═══════════════════════════════════════════════════════════════
# 4. CUSTOM EMBEDDING FUNCTION
# ═══════════════════════════════════════════════════════════════
class GeminiEmbeddingFunction(EmbeddingFunction):
    def __init__(self, key: str):
        self.embed_client = genai.Client(api_key=key)

    def __call__(self, input: Documents) -> Embeddings:
        models_to_try = ["text-embedding-004", "gemini-embedding-001"]
        last_err = None
        for model_name in models_to_try:
            try:
                response = self.embed_client.models.embed_content(
                    model=model_name,
                    contents=input,
                )
                return [e.values for e in response.embeddings]
            except Exception as e:
                last_err = e
                if "404" in str(e) or "not found" in str(e).lower():
                    continue
                raise e
        if last_err:
            raise last_err


# ═══════════════════════════════════════════════════════════════
# 5. RAG — CHROMADB CONNECTION (Auto-builds if collection is missing)
# ═══════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner="🔗 Connecting to Clinical Knowledge Base...")
def get_chroma_collection(key: str):
    db_client = chromadb.PersistentClient(path="./chroma_db")
    embedder = GeminiEmbeddingFunction(key=key)
    try:
        return db_client.get_collection(name="clinical_manuals", embedding_function=embedder)
    except Exception:
        # Auto-build database if missing (ideal for Streamlit Cloud deployment)
        try:
            from build_db import build_database
            with st.spinner("⚙️ Building Knowledge Base for the first time... This will take a moment."):
                build_database(api_key=key)
            return db_client.get_collection(name="clinical_manuals", embedding_function=embedder)
        except Exception as build_err:
            raise build_err


try:
    collection = get_chroma_collection(api_key)
except Exception as e:
    st.error(f"""
    **🚨 Clinical Knowledge Base Error**
    
    Could not connect to or build the ChromaDB vector database.
    
    *Details:* `{e}`
    
    **Troubleshooting:**
    1. Ensure your `GEMINI_API_KEY` is valid (get a free key at [Google AI Studio](https://aistudio.google.com/app/apikey)).
    2. If deploying to **Streamlit Community Cloud**, add your API key in **App Settings -> Secrets**:
       ```toml
       GEMINI_API_KEY = "AIzaSy..."
       ```
    """)
    st.stop()


# ═══════════════════════════════════════════════════════════════
# 6. HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════
def rag_retrieve(query: str, n_results: int = 4) -> str:
    """Retrieve top-k relevant clinical chunks from ChromaDB."""
    try:
        results = collection.query(query_texts=[query], n_results=n_results)
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        context_parts = []
        for doc, meta in zip(docs, metas):
            source = meta.get("source", "knowledge_base")
            context_parts.append(f"[Source: {source}]\n{doc}")
        return "\n\n---\n\n".join(context_parts)
    except Exception:
        return ""


def check_crisis(text: str) -> bool:
    """Return True if the text contains any crisis keyword."""
    return bool(CRISIS_PATTERN.search(text))


def parse_score_from_response(response_text: str) -> int | None:
    """Attempt to extract a 0-3 score from a free-text response."""
    text_lower = response_text.lower().strip()

    # Direct key match
    for key, val in SCORE_RESPONSE_MAP.items():
        if key in text_lower:
            return val

    # Regex for standalone digits
    match = re.search(r'\b([0-3])\b', text_lower)
    if match:
        return int(match.group(1))

    return None


def get_severity(score: int, scale: str) -> tuple[str, str, str]:
    """Return (label, css_class, emoji) for a given score and scale."""
    thresholds = PHQ9_SEVERITY if scale == "PHQ9" else GAD7_SEVERITY
    for max_score, label, css, emoji in thresholds:
        if score <= max_score:
            return label, css, emoji
    return "Unknown", "minimal", "❓"


def get_cbt_recommendations(phq9_score: int | None, gad7_score: int | None) -> str:
    """Build CBT recommendation text based on scores."""
    recs = []

    if phq9_score is not None:
        if phq9_score <= 4:
            recs.append("🏃 **Depression (PHQ-9 Minimal):** Maintain healthy routine habits — regular sleep schedule, outdoor activity, and positive social connection. Monitor mood weekly.")
        elif phq9_score <= 9:
            recs.append("📝 **Depression (PHQ-9 Mild):** Practice **Behavioral Activation** — schedule 2-3 enjoyable or productive activities daily. Use a Thought Record to reframe negative self-talk.")
        elif phq9_score <= 14:
            recs.append("🧠 **Depression (PHQ-9 Moderate):** Structured CBT is recommended. Focus on **Behavioral Activation** and **Cognitive Restructuring**. Consider professional counseling support.")
        elif phq9_score <= 19:
            recs.append("🩺 **Depression (PHQ-9 Moderately Severe):** Active treatment recommended. Seek a qualified CBT practitioner. Evaluation for pharmacotherapy may also be helpful.")
        else:
            recs.append("🚨 **Depression (PHQ-9 Severe):** Please consult a mental health professional immediately. Combined CBT and medical evaluation is strongly recommended.")

    if gad7_score is not None:
        if gad7_score <= 4:
            recs.append("🧘 **Anxiety (GAD-7 Minimal):** Practice daily **diaphragmatic breathing** and box breathing (4-4-4-4) to maintain baseline calm.")
        elif gad7_score <= 9:
            recs.append("⏰ **Anxiety (GAD-7 Mild):** Use **Worry Postponement** (schedule a daily 15-min 'worry time'). Utilize the **5-4-3-2-1 Grounding Technique** during anxious moments.")
        elif gad7_score <= 14:
            recs.append("🛡️ **Anxiety (GAD-7 Moderate):** Structured CBT for anxiety recommended. Work on building an **Exposure Hierarchy** and identifying cognitive distortions. Consult a specialist.")
        else:
            recs.append("🚨 **Anxiety (GAD-7 Severe):** Please consult a doctor or therapist urgently. Combined CBT + clinical evaluation is strongly advised.")

    return "\n\n".join(recs) if recs else "Continue monitoring your mental wellbeing."


def render_crisis_alert(lang: str = "English"):
    """Render the crisis alert UI block."""
    if lang in ["Roman Urdu", "اردو"]:
        st.markdown("""
        <div class="crisis-alert">
        <h3>🆘 فوری مدد درکار ہے</h3>
        <p><strong>Aap akele nahi hain. Abhi yeh helplines par call karein:</strong></p>
        <ul>
            <li>📞 <strong>Umang Pakistan:</strong> 0317-4288665 (24/7)</li>
            <li>📞 <strong>Rozan Counseling:</strong> 051-2890505</li>
            <li>📞 <strong>Rescue Emergency:</strong> 1122</li>
            <li>📞 <strong>Edhi Foundation:</strong> 115</li>
        </ul>
        <p>Agar aap abhi khud ko nuqsaan pahunchane wale hain, toh nazdiki hospital emergency room jayein ya 1122 call karein.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="crisis-alert">
        <h3>🆘 Crisis Support — You Are Not Alone</h3>
        <p><strong>Please reach out to these emergency helplines immediately:</strong></p>
        <ul>
            <li>📞 <strong>Umang Pakistan:</strong> 0317-4288665 (24/7)</li>
            <li>📞 <strong>Rozan Counseling:</strong> 051-2890505</li>
            <li>📞 <strong>Rescue Emergency:</strong> 1122</li>
            <li>📞 <strong>Edhi Foundation:</strong> 115</li>
        </ul>
        <p>If you are in immediate danger, please go to your nearest emergency room or call <strong>1122</strong>.</p>
        </div>
        """, unsafe_allow_html=True)


def generate_final_report(name: str, phq9_scores: list, gad7_scores: list, lang: str) -> str:
    """Generate a structured markdown report from collected scores."""
    lines = [
        "# 📋 PsyScreen-RAG — Clinical Assessment Report",
        f"**Patient Name:** {name}",
        f"**Language:** {lang}",
        f"**Date:** {_time.strftime('%Y-%m-%d %H:%M:%S')}",
        "---",
    ]

    if phq9_scores:
        total = sum(phq9_scores)
        label, _, emoji = get_severity(total, "PHQ9")
        lines += [
            "## PHQ-9 Depression Screening Result",
            f"| # | Question Summary | Score (0-3) |",
            f"|---|------------------|-------------|",
        ]
        for i, (q, s) in enumerate(zip(PHQ9_QUESTIONS, phq9_scores), 1):
            lines.append(f"| {i} | {q} | {s} |")
        lines += [
            f"| | **TOTAL SCORE** | **{total} / 27** |",
            f"\n**Severity Level:** {emoji} {label}",
            "",
        ]

    if gad7_scores:
        total = sum(gad7_scores)
        label, _, emoji = get_severity(total, "GAD7")
        lines += [
            "## GAD-7 Anxiety Screening Result",
            f"| # | Question Summary | Score (0-3) |",
            f"|---|------------------|-------------|",
        ]
        for i, (q, s) in enumerate(zip(GAD7_QUESTIONS, gad7_scores), 1):
            lines.append(f"| {i} | {q} | {s} |")
        lines += [
            f"| | **TOTAL SCORE** | **{total} / 21** |",
            f"\n**Severity Level:** {emoji} {label}",
            "",
        ]

    lines += [
        "---",
        "## CBT Psychoeducational Recommendations",
        get_cbt_recommendations(
            sum(phq9_scores) if phq9_scores else None,
            sum(gad7_scores) if gad7_scores else None,
        ),
        "",
        "---",
        "> ⚠️ **Medical Disclaimer:** This report is generated by an AI clinical research screening tool for academic/informational purposes only. It does NOT constitute a formal medical diagnosis. Please consult a licensed professional.",
        "> 📞 **Pakistan Helplines:** Umang: 0317-4288665 | Rozan: 051-2890505 | Rescue: 1122",
    ]
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# 7. SESSION STATE INITIALIZATION
# ═══════════════════════════════════════════════════════════════
def init_session():
    defaults = {
        "genai_client": genai.Client(api_key=api_key),
        "chat_history": [],            # [{role, content}]
        "state": "DISCLAIMER",         # state machine stage
        "patient_name": "",
        "language": "English",
        "selected_tests": ["PHQ9", "GAD7"],
        "current_test": None,          # "PHQ9" or "GAD7"
        "current_q_index": 0,
        "phq9_scores": [],
        "gad7_scores": [],
        "awaiting_score": False,
        "crisis_triggered": False,
        "report_generated": False,
        "report_text": "",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session()


# ═══════════════════════════════════════════════════════════════
# 8. LLM CALL WITH RAG CONTEXT
# ═══════════════════════════════════════════════════════════════
SYSTEM_PROMPT = """
You are "PsyScreen-RAG", a compassionate, empathetic clinical AI assistant developed for an MS Thesis research project on Mental Health Screening and CBT interventions.

Your primary role is to administer standardized mental health screenings (PHQ-9 for depression, GAD-7 for anxiety) strictly following the clinical manuals in the provided context.

CORE RULES:
1. You MUST follow the RAG context provided. Do not invent questions, scores, or clinical facts.
2. You are CONVERSATIONAL but CLINICAL. Validate each response warmly before moving on.
3. Ask EXACTLY ONE question at a time. Never ask multiple questions in one message.
4. You support English, Urdu (اردو), and Roman Urdu (Minglish). Match the user's language.
5. NEVER provide a diagnosis. Always include the disclaimer that this is a screening tool.
6. If the user seems confused, gently clarify. Never rush the patient.
7. Be warm but professional. Use phrases like "Thank you for sharing that" or "I understand."
8. For scoring: Map user responses to: Not at all=0, Several days=1, More than half the days=2, Nearly every day=3.

ROMAN URDU SCORING:
- "bilkul nahi" → 0, "kuch din/baar" → 1, "zyada tar/aksar" → 2, "hamesha/har roz" → 3

SAFETY: If ANY user message contains thoughts of self-harm or suicide, your ONLY response should be:
"I hear that you're in pain. Please know you are not alone. CRISIS_ALERT_TRIGGERED"
"""

_MODELS = ["gemini-2.5-flash", "gemini-3-flash-preview", "gemini-1.5-flash", "gemini-1.5-flash-8b", "gemini-1.0-pro"]

def llm_chat(user_message: str, extra_context: str = "") -> str:
    """Send a message to Gemini with RAG context injected. Retries on rate limit."""
    client = st.session_state.genai_client

    history = []
    for msg in st.session_state.chat_history[-10:]:
        role = "user" if msg["role"] == "user" else "model"
        history.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))

    full_prompt = f"{SYSTEM_PROMPT}\n\n"
    if extra_context:
        full_prompt += f"=== CLINICAL KNOWLEDGE BASE (RAG Context) ===\n{extra_context}\n\n=== END CONTEXT ===\n\n"
    full_prompt += f"User message: {user_message}"

    last_error = None
    for model_name in _MODELS:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=history + [types.Content(role="user", parts=[types.Part(text=full_prompt)])],
                )
                return response.text.strip()
            except Exception as e:
                last_error = e
                err_str = str(e)
                if "429" in err_str or "quota" in err_str.lower() or "exhausted" in err_str.lower():
                    wait = 15 * (attempt + 1)
                    _time.sleep(wait)
                elif "model" in err_str.lower() and ("not found" in err_str.lower() or "not supported" in err_str.lower()):
                    break
                else:
                    return f"I'm sorry, I encountered an error. Please try again. (Details: {err_str[:120]})"

    return f"Service temporarily unavailable due to API quota limits. Please wait a minute and try again.\n\nTip: Use a paid Gemini API key for unlimited access."


# ═══════════════════════════════════════════════════════════════
# 9. STATE MACHINE — ADVANCE TO NEXT STATE
# ═══════════════════════════════════════════════════════════════
def advance_state(user_input: str):
    """Process user input and advance the conversation state machine."""
    state = st.session_state.state

    # ── CRISIS CHECK ──────────────────────────────────────────
    if check_crisis(user_input):
        st.session_state.crisis_triggered = True
        st.session_state.state = "CRISIS"
        bot_msg = ("I hear that you are in pain right now, and I am deeply concerned about your safety. "
                   "Please know you are not alone. 💙\n\n"
                   "🆘 **Please contact a crisis helpline immediately:**\n"
                   "📞 Umang Pakistan: **0317-4288665** (24/7)\n"
                   "📞 Rescue Emergency: **1122**\n\n"
                   "The screening has been paused. Please reach out for support.")
        add_message("assistant", bot_msg)
        return

    # ── DISCLAIMER ─────────────────────────────────────────────
    if state == "DISCLAIMER":
        st.session_state.state = "COLLECT_NAME"
        rag_ctx = rag_retrieve("patient name language selection mental health screening")
        bot_msg = llm_chat(
            "The user has accepted the disclaimer. Greet them warmly, ask for their name, "
            "and ask which language they prefer (English, Roman Urdu, or Urdu). Keep it brief and friendly.",
            rag_ctx
        )
        add_message("assistant", bot_msg)

    # ── COLLECT NAME & LANGUAGE ────────────────────────────────
    elif state == "COLLECT_NAME":
        st.session_state.patient_name = user_input.strip() or "Patient"
        st.session_state.state = "SELECT_TEST"
        name = st.session_state.patient_name
        rag_ctx = rag_retrieve("PHQ-9 GAD-7 depression anxiety test selection")
        bot_msg = llm_chat(
            f"The patient's name is '{name}'. Now ask them which test(s) they want to take: "
            "PHQ-9 (depression screening), GAD-7 (anxiety screening), or both. "
            "Briefly explain what each test is for in 1-2 sentences.",
            rag_ctx
        )
        add_message("assistant", bot_msg)

    # ── TEST SELECTION ─────────────────────────────────────────
    elif state == "SELECT_TEST":
        inp = user_input.lower()
        if "phq" in inp and "gad" in inp or "both" in inp or "dono" in inp or "all" in inp:
            st.session_state.selected_tests = ["PHQ9", "GAD7"]
        elif "phq" in inp or "depression" in inp or "udaas" in inp:
            st.session_state.selected_tests = ["PHQ9"]
        elif "gad" in inp or "anxiety" in inp or "ghabrahat" in inp:
            st.session_state.selected_tests = ["GAD7"]
        else:
            st.session_state.selected_tests = ["PHQ9", "GAD7"]

        first_test = st.session_state.selected_tests[0]
        st.session_state.current_test = first_test
        st.session_state.current_q_index = 0
        st.session_state.state = "QUESTIONING"
        _ask_current_question()

    # ── QUESTIONING ────────────────────────────────────────────
    elif state == "QUESTIONING":
        score = parse_score_from_response(user_input)

        if score is None:
            rag_ctx = rag_retrieve("response options not at all several days")
            bot_msg = llm_chat(
                f"The patient said: '{user_input}'. I could not determine a clear 0-3 score from this. "
                "Empathetically ask them to clarify using the options: "
                "Not at all (0), Several days (1), More than half the days (2), Nearly every day (3).",
                rag_ctx
            )
            add_message("assistant", bot_msg)
            return

        test = st.session_state.current_test
        q_idx = st.session_state.current_q_index

        if test == "PHQ9":
            st.session_state.phq9_scores.append(score)
            questions = PHQ9_QUESTIONS
            if q_idx == 8 and score >= 1:
                st.session_state.crisis_triggered = True
                st.session_state.state = "CRISIS"
                bot_msg = ("I want to make sure you're safe. You mentioned having thoughts about self-harm. "
                           "I care about your wellbeing. 💙\n\n"
                           "🆘 **Please reach out to a helpline:**\n"
                           "📞 Umang Pakistan: **0317-4288665** (24/7)\n"
                           "📞 Rescue: **1122**\n\n"
                           "Please speak with someone you trust or contact a mental health professional.")
                add_message("assistant", bot_msg)
                return
        else:
            st.session_state.gad7_scores.append(score)
            questions = GAD7_QUESTIONS

        st.session_state.current_q_index += 1

        if st.session_state.current_q_index >= len(questions):
            _finish_current_test()
        else:
            _ask_current_question(prev_score=score, prev_q=questions[q_idx])

    # ── CBT CHAT (post-report free chat) ──────────────────────
    elif state == "CBT_CHAT":
        rag_ctx = rag_retrieve(user_input, n_results=5)
        bot_msg = llm_chat(
            f"The assessment is complete. The patient is asking: '{user_input}'. "
            "Answer their question about CBT techniques, coping strategies, or mental health "
            "using ONLY the provided RAG context. Be warm, practical, and encouraging.",
            rag_ctx
        )
        add_message("assistant", bot_msg)


def _ask_current_question(prev_score: int | None = None, prev_q: str | None = None):
    """Ask the next question in the current test."""
    test = st.session_state.current_test
    q_idx = st.session_state.current_q_index
    questions = PHQ9_QUESTIONS if test == "PHQ9" else GAD7_QUESTIONS
    test_name = "PHQ-9" if test == "PHQ9" else "GAD-7"

    current_q = questions[q_idx]
    total_qs = len(questions)

    rag_ctx = rag_retrieve(f"{test_name} question {q_idx + 1} {current_q}")

    if prev_q and prev_score is not None:
        prompt = (
            f"The patient answered question {q_idx} ('{prev_q}') with score {prev_score}. "
            f"Briefly validate their answer with empathy (1 sentence). "
            f"Then smoothly transition and ask question {q_idx + 1} of {total_qs} of the {test_name}: "
            f"'{current_q}' "
            f"Remind them of the 4 response options."
        )
    else:
        prompt = (
            f"Now begin the {test_name} screening. Tell the patient this covers the past 2 weeks. "
            f"Ask question 1 of {total_qs}: '{current_q}'. "
            f"Remind them of the 4 response options."
        )

    bot_msg = llm_chat(prompt, rag_ctx)
    add_message("assistant", bot_msg)


def _finish_current_test():
    """Called when a test is fully completed."""
    test = st.session_state.current_test
    tests = st.session_state.selected_tests
    current_idx = tests.index(test)

    if current_idx + 1 < len(tests):
        next_test = tests[current_idx + 1]
        st.session_state.current_test = next_test
        st.session_state.current_q_index = 0
        test_name = "GAD-7" if next_test == "GAD7" else "PHQ-9"

        rag_ctx = rag_retrieve(f"{test_name} screening questions anxiety")
        bot_msg = llm_chat(
            f"The patient has completed the {'PHQ-9' if test == 'PHQ9' else 'GAD-7'} test. "
            f"Acknowledge this warmly. Now transition to the {test_name} screening. "
            "Ask if they are ready to continue.",
            rag_ctx
        )
        add_message("assistant", bot_msg)
    else:
        _generate_and_display_report()


def _generate_and_display_report():
    """Generate final report and switch to CBT_CHAT state."""
    phq9 = st.session_state.phq9_scores
    gad7 = st.session_state.gad7_scores
    name = st.session_state.patient_name

    report_md = generate_final_report(name, phq9, gad7, st.session_state.language)
    st.session_state.report_text = report_md
    st.session_state.report_generated = True
    st.session_state.state = "CBT_CHAT"

    phq9_total = sum(phq9) if phq9 else None
    gad7_total = sum(gad7) if gad7 else None
    cbt = get_cbt_recommendations(phq9_total, gad7_total)

    rag_ctx = rag_retrieve("CBT recommendations depression anxiety treatment")

    summary_parts = []
    if phq9:
        label, _, emoji = get_severity(sum(phq9), "PHQ9")
        summary_parts.append(f"PHQ-9 score: {sum(phq9)}/27 ({emoji} {label})")
    if gad7:
        label, _, emoji = get_severity(sum(gad7), "GAD7")
        summary_parts.append(f"GAD-7 score: {sum(gad7)}/21 ({emoji} {label})")

    bot_msg = llm_chat(
        f"All screenings are complete. Summarize the results: {', '.join(summary_parts)}. "
        f"Provide the following CBT recommendations in a warm, actionable way: {cbt}. "
        "End with the medical disclaimer and an invitation to ask follow-up questions about CBT techniques.",
        rag_ctx
    )
    add_message("assistant", bot_msg)


def add_message(role: str, content: str):
    """Add a message to chat history."""
    st.session_state.chat_history.append({"role": role, "content": content})


# ═══════════════════════════════════════════════════════════════
# 10. SIDEBAR
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🧠 PsyScreen-RAG")
    
    # Active status badge
    st.markdown("""
    <div style="margin-bottom: 1rem;">
        <span class="status-pill">
            <span class="status-dot"></span> RAG System Active
        </span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<p style='font-size:0.8rem;color:#64748b;'>MS Thesis Project — Mental Health Screening & CBT Assistant</p>", unsafe_allow_html=True)
    
    st.divider()

    # Language selector
    lang_choice = st.selectbox(
        "🌐 Preferred Language / زبان",
        ["English", "Roman Urdu", "اردو"],
        key="language_select"
    )
    if lang_choice != st.session_state.language:
        st.session_state.language = lang_choice

    st.divider()

    # Progress display
    state = st.session_state.state
    if state == "QUESTIONING":
        test = st.session_state.current_test
        q_idx = st.session_state.current_q_index
        total = len(PHQ9_QUESTIONS) if test == "PHQ9" else len(GAD7_QUESTIONS)
        test_name = "PHQ-9" if test == "PHQ9" else "GAD-7"
        pct = int(q_idx / total * 100)
        
        st.markdown(f"**📊 {test_name} Assessment Progress**")
        st.markdown(f"""
        <div class="progress-container">
            <div class="progress-fill" style="width:{pct}%"></div>
        </div>
        <div style="display:flex;justify-content:space-between;color:#94a3b8;font-size:0.78rem;">
            <span>Question {q_idx} of {total}</span>
            <span>{pct}%</span>
        </div>
        """, unsafe_allow_html=True)
        st.divider()

    # Live score metrics
    if st.session_state.phq9_scores or st.session_state.gad7_scores:
        st.markdown("**📈 Live Assessment Scores**")
        
        if st.session_state.phq9_scores:
            total = sum(st.session_state.phq9_scores)
            label, css, emoji = get_severity(total, "PHQ9")
            st.markdown(f"""
            <div style="background:rgba(30,41,59,0.5);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:0.75rem 1rem;margin-bottom:0.5rem;">
                <div style="font-size:0.75rem;color:#94a3b8;">PHQ-9 Depression Score</div>
                <div style="font-size:1.2rem;font-weight:700;color:#38bdf8;display:flex;justify-content:space-between;align-items:center;">
                    <span>{total} / 27</span>
                    <span class="badge badge-{css}" style="margin:0;font-size:0.72rem;padding:0.2rem 0.6rem;">{emoji} {label}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        if st.session_state.gad7_scores:
            total = sum(st.session_state.gad7_scores)
            label, css, emoji = get_severity(total, "GAD7")
            st.markdown(f"""
            <div style="background:rgba(30,41,59,0.5);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:0.75rem 1rem;">
                <div style="font-size:0.75rem;color:#94a3b8;">GAD-7 Anxiety Score</div>
                <div style="font-size:1.2rem;font-weight:700;color:#c084fc;display:flex;justify-content:space-between;align-items:center;">
                    <span>{total} / 21</span>
                    <span class="badge badge-{css}" style="margin:0;font-size:0.72rem;padding:0.2rem 0.6rem;">{emoji} {label}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        st.divider()

    # Download Report Button
    if st.session_state.report_generated:
        st.download_button(
            label="📥 Download Clinical Report",
            data=st.session_state.report_text,
            file_name=f"psyscreen_report_{st.session_state.patient_name.replace(' ','_')}.md",
            mime="text/markdown",
            use_container_width=True,
        )
        st.divider()

    # Reset Button
    if st.button("🔄 Start New Session", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    st.divider()

    # Crisis Helplines (Always Visible)
    st.markdown("### 🆘 Crisis Helplines")
    st.markdown("""
    <div style="background:rgba(239,68,68,0.08);border:1px solid rgba(248,113,113,0.25);border-radius:12px;padding:0.8rem 1rem;">
        <p style="color:#fca5a5;font-size:0.82rem;margin:0;line-height:1.6;">
        📞 <strong>Umang:</strong> 0317-4288665 (24/7)<br>
        📞 <strong>Rozan:</strong> 051-2890505<br>
        📞 <strong>Rescue:</strong> 1122<br>
        📞 <strong>Edhi:</strong> 115
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("""
    <div class="disclaimer">
    ⚠️ <strong>Clinical Disclaimer:</strong> Research screening tool for academic evaluation. Not a diagnostic medical device.
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# 11. MAIN CHAT & INTERACTIVE UI
# ═══════════════════════════════════════════════════════════════

# Glassmorphic Header Banner
st.markdown("""
<div class="header-banner">
    <h1>🧠 PsyScreen-RAG</h1>
    <p>Retrieval-Augmented Mental Health Screening & CBT Assistant</p>
    <div class="header-tags">
        <span class="tag-pill">📋 PHQ-9 Depression</span>
        <span class="tag-pill">😰 GAD-7 Anxiety</span>
        <span class="tag-pill">🧘 CBT Interventions</span>
        <span class="tag-pill">🔗 Gemini + ChromaDB RAG</span>
        <span class="tag-pill">🌐 English · Roman Urdu · اردو</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Crisis State
if st.session_state.state == "CRISIS":
    render_crisis_alert(st.session_state.language)
    if st.button("✅ I am safe and wish to continue", use_container_width=True):
        st.session_state.crisis_triggered = False
        st.session_state.state = "CBT_CHAT"
        add_message("assistant", "I'm glad you're safe. 💙 The formal screening has been paused. "
                    "I'm here to talk. You can ask me anything about coping strategies, CBT techniques, or emotional wellbeing.")
        st.rerun()

# Disclaimer / Landing Screen
if st.session_state.state == "DISCLAIMER" and not st.session_state.chat_history:
    st.markdown("""
    <div style="background:rgba(30,41,59,0.6);backdrop-filter:blur(16px);border:1px solid rgba(129,140,248,0.25);
                border-radius:18px;padding:1.8rem 2.2rem;margin-bottom:1.5rem;box-shadow:0 10px 30px rgba(0,0,0,0.3);">
        <h3 style="color:#38bdf8;margin:0 0 1rem 0;font-weight:700;">📋 Informed Consent & Research Information</h3>
        <ul style="color:#cbd5e0;font-size:0.92rem;line-height:1.8;padding-left:1.2rem;">
            <li>This system administers standardized psychological screenings: <strong>PHQ-9</strong> (Depression) and <strong>GAD-7</strong> (Anxiety).</li>
            <li><strong>Privacy First:</strong> Data is processed locally in memory for your session and is not stored permanently.</li>
            <li><strong>Academic Tool:</strong> Developed as part of an MS Thesis research project. It is <strong>NOT</strong> a substitute for professional medical diagnosis or clinical treatment.</li>
            <li><strong>Safety Protocol:</strong> If distress or self-harm keywords are detected, the system immediately surfaces crisis helplines.</li>
            <li><strong>Multilingual Support:</strong> Full support for <strong>English</strong>, <strong>Roman Urdu</strong>, and <strong>Urdu (اردو)</strong>.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    if st.button("✨ Begin Assessment & Screening", use_container_width=True):
        add_message("user", "I accept the disclaimer and wish to begin.")
        advance_state("I accept the disclaimer and wish to begin.")
        st.rerun()

# Render Chat History
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"], avatar="🧠" if msg["role"] == "assistant" else "👤"):
        st.markdown(msg["content"])

# Interactive Quick Action Controls (Pill Buttons)
if st.session_state.state == "SELECT_TEST":
    st.markdown("<p style='color:#94a3b8;font-size:0.85rem;margin-bottom:0.5rem;'>⚡ <strong>Quick Select Test:</strong></p>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    if c1.button("📋 PHQ-9 (Depression)", use_container_width=True):
        add_message("user", "PHQ-9 Depression Screening")
        advance_state("PHQ-9 Depression Screening")
        st.rerun()
    if c2.button("😰 GAD-7 (Anxiety)", use_container_width=True):
        add_message("user", "GAD-7 Anxiety Screening")
        advance_state("GAD-7 Anxiety Screening")
        st.rerun()
    if c3.button("⚡ Both Screenings", use_container_width=True):
        add_message("user", "Both PHQ-9 and GAD-7 Screenings")
        advance_state("Both PHQ-9 and GAD-7 Screenings")
        st.rerun()

elif st.session_state.state == "QUESTIONING":
    st.markdown("<p style='color:#94a3b8;font-size:0.85rem;margin:0.5rem 0;'>👇 <strong>Click a quick response or type below:</strong></p>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    if col1.button("🟢 Not at all (0)", use_container_width=True):
        add_message("user", "Not at all")
        advance_state("Not at all")
        st.rerun()
        
    if col2.button("🟡 Several days (1)", use_container_width=True):
        add_message("user", "Several days")
        advance_state("Several days")
        st.rerun()
        
    if col3.button("🟠 More than half (2)", use_container_width=True):
        add_message("user", "More than half the days")
        advance_state("More than half the days")
        st.rerun()
        
    if col4.button("🔴 Nearly every day (3)", use_container_width=True):
        add_message("user", "Nearly every day")
        advance_state("Nearly every day")
        st.rerun()

# Report Expander Card (shown when report is generated)
if st.session_state.report_generated and st.session_state.state == "CBT_CHAT":
    with st.expander("📊 View Complete Assessment Report & Metrics", expanded=True):
        phq9 = st.session_state.phq9_scores
        gad7 = st.session_state.gad7_scores

        valid_scores = [x for x in [phq9, gad7] if x]
        if valid_scores:
            cols = st.columns(len(valid_scores))
            col_idx = 0

            if phq9:
                total = sum(phq9)
                label, css, emoji = get_severity(total, "PHQ9")
                with cols[col_idx]:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{total}</div>
                        <div class="metric-label">PHQ-9 Depression Score</div>
                        <span class="badge badge-{css}">{emoji} {label}</span>
                    </div>
                    """, unsafe_allow_html=True)
                col_idx += 1

            if gad7:
                total = sum(gad7)
                label, css, emoji = get_severity(total, "GAD7")
                with cols[col_idx]:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{total}</div>
                        <div class="metric-label">GAD-7 Anxiety Score</div>
                        <span class="badge badge-{css}">{emoji} {label}</span>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 🧘 Personalized CBT Recommendations")
        st.markdown(get_cbt_recommendations(
            sum(phq9) if phq9 else None,
            sum(gad7) if gad7 else None,
        ))

# Chat Input Box
if st.session_state.state not in ["DISCLAIMER", "CRISIS"]:
    placeholder_map = {
        "English": "Type your response or select an option above...",
        "Roman Urdu": "Yahan apna jawab likhein ya upar option select karein...",
        "اردو": "یہاں اپنا جواب لکھیں یا اوپر کا انتخاب کریں...",
    }
    placeholder = placeholder_map.get(st.session_state.language, "Type here...")

    if user_input := st.chat_input(placeholder):
        add_message("user", user_input)
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar="🧠"):
            with st.spinner("Thinking..."):
                advance_state(user_input)
                if st.session_state.chat_history:
                    last = st.session_state.chat_history[-1]
                    if last["role"] == "assistant":
                        st.markdown(last["content"])
        st.rerun()

# PsyScreen-RAG: Retrieval-Augmented Mental Health Screening & CBT Intervention System

PsyScreen-RAG is a RAG-based clinical assistant designed to administer standardized mental health screenings (PHQ-9 and GAD-7) and provide evidence-based Cognitive Behavioral Therapy (CBT) suggestions. It is built to support English, Urdu, and Roman Urdu (Minglish) inputs, and features a deterministic Crisis Safety Protocol tailored for low-resource regions like Pakistan.

---

## 🚀 Features

- **Standardized Questionnaires**: Fully implements **PHQ-9** (depression) and **GAD-7** (anxiety) question flows.
- **RAG-Grounded AI**: Vectorizes clinical manuals and CBT guides locally using ChromaDB and Google Gemini embeddings (`gemini-embedding-001`). Forces the LLM (`gemini-2.5-flash`) to generate answers based solely on verified literature.
- **Urdu & Roman Urdu Support**: A specialized linguistic processing layer understands everyday South Asian digital expressions (e.g., *"neend nahi aati"*, *"dil ghabra raha hai"*).
- **Rule-Based Crisis Filter**: Intercepts high-risk keywords (e.g., *"khudkushi"*, *"suicide"*) before they reach the LLM, halting tests and displaying localized Pakistani help resources (Umang, Rozan, Rescue 1122).
- **Session State Machine**: Dynamically manages the questionnaire progression and transition phases (Disclaimer → Test selection → PHQ-9 → GAD-7 → CBT Chat) inside Streamlit.
- **Interactive CBT Advisor**: Allows the patient to ask free-form questions about CBT strategies after completing the screening, fetching precise worksheets and explanations from the local database.

---

## 📁 Directory Structure

```
psyscreen_rag/
├── app.py                      # Main Streamlit UI and state machine
├── build_db.py                 # Vector database creation and loading script
├── requirements.txt            # Python library dependencies
├── .env.example                # Example environment file
├── chroma_db/                  # Local persistent ChromaDB storage (auto-generated)
└── data/
    ├── knowledge_base/         # Text guides ingested by RAG
    │   ├── phq9_manual.txt     # Scoring thresholds and administration instructions
    │   ├── gad7_manual.txt     # Cut-off points and interpretation rules
    │   ├── cbt_core_modules.txt# Foundation CBT model (Thoughts/Feelings/Behaviors)
    │   ├── cbt_depression.txt  # Behavioral Activation protocols
    │   ├── cbt_anxiety.txt     # Exposure therapies and worry management
    │   ├── cbt_distortions.txt # Comprehensive list of 15 cognitive distortions
    │   ├── roman_urdu_corpus.txt # Mapping from vernacular to clinical terms
    │   └── crisis_resources.txt# Pakistani national helplines and safety protocol
    └── uploaded_pdfs/          # Directory to drop CBT PDF books (auto-created)
```

---

## 🛠️ Setup Instructions

### 1. Prerequisites
Make sure you have Python 3.10+ installed.

### 2. Environment Configuration
1. Open the project folder `psyscreen-rag`.
2. Copy `.env.example` to a new file named `.env`:
   ```bash
   cp .env.example .env
   ```
3. Open `.env` and fill in your Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey):
   ```env
   GEMINI_API_KEY=your_key_here
   ```

### 3. Install Dependencies
Run the following command to install the required libraries:
```bash
pip install -r requirements.txt
```

### 4. Build the Vector Database
Before running the application, compile the clinical knowledge base into ChromaDB:
```bash
python build_db.py
```
*(Optional)*: If you want the system to reference specific clinical books/manuals in RAG, drop their PDF versions into `data/uploaded_pdfs/` before running `build_db.py`.

### 5. Run the Application
Start the Streamlit interface locally:
```bash
streamlit run app.py
```

---

## 🧠 Evaluation Plan (MS Thesis)

### A. Quantitative Benchmarking
- **Retrieval Accuracy (Golden Set)**: Top-k accuracy evaluation on 50 predefined medical queries (Target: > 90% retrieval accuracy).
- **Scoring Validity (MAE)**: Mean Absolute Error between manual clinical scoring and system-assigned scores on 100 test transcripts (Target: MAE < 0.5 points).

### B. Qualitative & Safety Audits
- **Urdu/Roman Urdu Likert Ratings**: Evaluated by bilingual assessors on 5 levels (1 = Poor, 5 = Native).
- **Red-Teaming False Negatives**: Safety audit using 20 self-harm variations to verify the crisis filter (Target: 0% False Negatives / 100% recall).

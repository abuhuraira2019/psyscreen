# PsyScreen-RAG: Trilingual Mental Health Screening with CBT Guidance and Clinician Review

PsyScreen-RAG is the screening assistant developed for the MS Data Science thesis *PsyScreen* (Abu Huraira, MSDSF23M027, University of the Punjab). It administers the **PHQ-9** (depression) and **GAD-7** (anxiety) together in **English, Roman Urdu or Urdu script**, scores them in code, gives **severity-banded CBT psychoeducational guidance**, and lets a clinical psychologist review each submitted report (**Clinical Validation**). A Gemini-based supportive chat is grounded in a clinical knowledge base through retrieval-augmented generation (RAG).

> ⚠️ Research screening tool for academic evaluation. Not an automated medical diagnostic device.

Live app: https://psyscreentool.streamlit.app/

---

## 🚀 Features

- **Deterministic questionnaire flow**: a state machine presents the 16 items one at a time in a fixed order (PHQ-9 items 1–9, then GAD-7 items 1–7) with fixed, pre-translated wording. Users answer with buttons or free text (digits 0–3, including Urdu/Arabic numerals, or a dictionary of English, Roman Urdu and Urdu expressions); unclear answers are asked again with the four standard options. The language model is not used to administer or score the questionnaires.
- **Scoring in code**: PHQ-9 (0–27) and GAD-7 (0–21) totals are summed in Python and banded separately (Minimal / Mild / Moderate / Moderately severe / Severe for PHQ-9; Minimal / Mild / Moderate / Severe for GAD-7). No composite score is formed.
- **Severity-banded CBT guidance**: after the last item, the user sees both totals with their bands and one CBT psychoeducational message per instrument, in the chosen language (see the table below). The same guidance is included in the PDF report and shown in the Doctor Dashboard.
- **PDF report**: report metadata, PHQ-9 and GAD-7 totals and bands, CBT guidance and, once reviewed, the psychologist's verdict and feedback (ReportLab).
- **Clinical Validation (human-in-the-loop review)**: the user submits the report to the chosen psychologist; it appears in the password-protected Doctor Dashboard with an eight-hour review target. The psychologist records a verdict (*Normal / Healthy* or *Consultation Recommended*) and a feedback note, which are e-mailed to the user with the PDF report attached. Users whose report is marked *Consultation Recommended* are offered an appointment-request button.
- **Crisis check on every input**: a case-insensitive regular expression of 26 patterns (11 English, 15 Roman Urdu) pauses the assessment and shows Pakistani helplines (Umang Pakistan 0317-4288665, Rozan Counseling 051-2890505, Rescue 1122). Any PHQ-9 item 9 answer above 0 shows the same helplines, and the assessment continues.
- **RAG supportive chat**: after the crisis screen, when the user confirms they are safe, Gemini answers using the top-5 chunks retrieved from the ChromaDB collection `clinical_manuals` and the last ten messages.

### CBT guidance by severity band

| Instrument | Score | Band | Guidance (screening support only) |
|---|---|---|---|
| PHQ-9 | 0–4 | Minimal | Maintain healthy routines: regular sleep, outdoor activity and social connection |
| PHQ-9 | 5–9 | Mild | Behavioural activation (2–3 pleasant activities daily) and a thought record |
| PHQ-9 | 10–14 | Moderate | Structured CBT: cognitive restructuring and activity scheduling |
| PHQ-9 | 15–27 | Moderately severe / Severe | Clinical consultation recommended alongside structured CBT |
| GAD-7 | 0–4 | Minimal | Diaphragmatic breathing and box breathing (4-4-4-4) |
| GAD-7 | 5–9 | Mild | Worry postponement (15-minute daily slot) and 5-4-3-2-1 grounding |
| GAD-7 | 10–14 | Moderate | Exposure hierarchy and cognitive reframing; anxiety-tolerance skills |
| GAD-7 | 15–21 | Severe | Urgent consultation with a qualified psychologist or physician |

### Conversation states

`COLLECT_LANG` → `COLLECT_NAME_EMAIL` → `SELECT_PSYCHOLOGIST` → `QUESTIONING` → `SUBMIT_OR_DOWNLOAD` → `SUBMITTED`, with `CRISIS` → `CBT_CHAT` reachable from any input.

### LLM and retrieval

- Chat models tried in order: `gemini-2.5-flash`, `gemini-3-flash-preview`, `gemini-1.5-flash`, `gemini-1.5-flash-8b`, `gemini-1.0-pro` (up to three retries per model on rate limits); API default generation parameters.
- Embeddings: `text-embedding-004`, fallback `gemini-embedding-001`.
- Knowledge base (`build_db.py`): `.txt` files and optional PDFs (read with `pypdf`), chunks of 500 characters with 50-character overlap (chunks of 50 characters or fewer discarded), embedded in batches of 90, stored in ChromaDB with cosine distance. The app builds the collection automatically if it does not exist.

### Data handling

All application state (conversation, answers, reports, verdicts, e-mail outbox) lives in the Streamlit session state and is lost when the session ends; nothing is written to a database. Questionnaire answers are scored locally and are not sent to the language model. Messages typed in the supportive chat, with up to the last ten messages of history, are sent to the Gemini API. The Doctor Dashboard uses a shared default password (`0000`), which is suitable only for a research demonstration.

---

## 📁 Directory Structure

```
psyscreen-rag/
├── app.py                      # Streamlit UI, state machine, scoring, CBT guidance, PDF, Doctor Dashboard
├── build_db.py                 # Knowledge-base (ChromaDB) build script
├── requirements.txt            # Python dependencies
├── .env.example                # Example environment file
├── chroma_db/                  # Pre-built persistent ChromaDB storage
└── data/
    ├── knowledge_base/         # Text guides ingested by RAG
    └── uploaded_pdfs/          # Optional PDF manuals (auto-created)
```

---

## 🛠️ Setup

1. Python 3.10+.
2. Copy `.env.example` to `.env` and set `GEMINI_API_KEY` (from [Google AI Studio](https://aistudio.google.com/app/apikey)). On Streamlit Cloud, add it under **Settings → Secrets**.
3. Optional, for real e-mail delivery: set `EMAIL_PASSWORD` (or `SMTP_PASSWORD`) to an app password for msdsf23m027@pucit.edu.pk; `SMTP_HOST` / `SMTP_PORT` default to `smtp.gmail.com` / `587`. Without it, review e-mails are shown only in the in-app outbox.
4. Install dependencies: `pip install -r requirements.txt`
5. (Re)build the knowledge base if needed: `python build_db.py`
6. Run: `streamlit run app.py`

---

## 🧠 Evaluation (as reported in the thesis)

- **Score concordance** (N = 130, chatbot first, then self-administered, same sitting): absolute-agreement ICC(A,1), Wilcoxon signed-rank test, Bland–Altman limits of agreement, weighted kappa for severity bands.
- **Post-interaction user-experience survey** (30 items adapted from HopeBot).
- **Crisis-detection test**: 150 author-labelled messages (50 English, 50 Roman Urdu, 50 Urdu script) run against the unchanged `check_crisis()` function.
- **Clinical Validation**: a random selection of about 20–30 study reports was reviewed by a consultant clinical psychologist through the Doctor Dashboard; no operational metrics were collected.

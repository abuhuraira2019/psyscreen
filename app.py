# --- STREAMLIT CLOUD SQLITE PATCH (MUST be first) ---
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass  # Running locally with system sqlite3 — that's fine

import os
import re
import sys
import time
import datetime
import io
import smtplib
from email.message import EmailMessage
import streamlit as st
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from dotenv import load_dotenv

# PDF Generation Imports
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

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
    page_title="PsyScreen-RAG | Clinical Mental Health Assessment",
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

/* ── ENFORCED PREMIUM DARK THEME ── */
.stApp {
    background: 
        radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.18) 0%, transparent 40%),
        radial-gradient(circle at 90% 80%, rgba(168, 85, 247, 0.18) 0%, transparent 40%),
        radial-gradient(circle at 50% 50%, rgba(14, 165, 233, 0.10) 0%, transparent 60%),
        linear-gradient(135deg, #090d16 0%, #0f172a 50%, #1e1b4b 100%) !important;
    background-attachment: fixed !important;
    color: #f8fafc !important;
}

/* ── Global Text Contrast & Readability (Dark Theme) ── */
.stApp, .stApp p, .stApp span, .stApp div, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] div,
[data-testid="stMarkdownContainer"] li,
.stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown div, .stMarkdown li {
    color: #f8fafc !important;
    -webkit-text-fill-color: #f8fafc !important;
}

/* ── Sidebar Dark Theme ── */
[data-testid="stSidebar"], section[data-testid="stSidebar"] {
    background: #090d16 !important;
    background-color: #090d16 !important;
    border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
}

/* ── Header Banner (Dark Glassmorphism) ── */
.header-banner {
    background: rgba(30, 41, 59, 0.65) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 20px !important;
    padding: 1.5rem 1.8rem !important;
    margin-bottom: 1.5rem !important;
    text-align: left !important;
    box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
}
.header-banner h1 {
    font-size: 1.8rem !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    margin: 0 0 0.2rem 0 !important;
}
.header-banner p {
    color: #94a3b8 !important;
    -webkit-text-fill-color: #94a3b8 !important;
    font-size: 0.92rem !important;
    margin: 0 !important;
}

/* ── Doctor Cards (Dark Glassmorphism) ── */
.doctor-card {
    background: rgba(30, 41, 59, 0.6) !important;
    backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(129, 140, 248, 0.25) !important;
    border-radius: 16px !important;
    padding: 1.2rem 1.4rem !important;
    margin-bottom: 1.2rem !important;
    transition: all 0.2s ease !important;
}
.doctor-card div {
    color: #f8fafc !important;
    -webkit-text-fill-color: #f8fafc !important;
}
.doctor-card:hover {
    border-color: #818cf8 !important;
    box-shadow: 0 8px 24px rgba(99, 102, 241, 0.2) !important;
}

/* ── Streamlit Bottom Input Alignment ── */
[data-testid="stBottom"] {
    background: transparent !important;
    background-color: transparent !important;
    max-width: 960px !important;
    margin-left: 0 !important;
    margin-right: auto !important;
    padding: 0 1.5rem 1.5rem 1.5rem !important;
}

[data-testid="stBottom"] > div,
.stChatFloatingInputContainer {
    background: transparent !important;
    background-color: transparent !important;
    padding: 0 !important;
    margin: 0 !important;
    width: 100% !important;
}

footer, footer > div {
    background: transparent !important;
    background-color: transparent !important;
}

/* ── Chat Input Outer Container ── */
[data-testid="stChatInput"], .stChatInput {
    background: rgba(15, 23, 42, 0.85) !important;
    background-color: rgba(15, 23, 42, 0.85) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1.5px solid rgba(129, 140, 248, 0.35) !important;
    border-radius: 18px !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
    padding: 4px 8px !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: #818cf8 !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), 0 0 20px rgba(129, 140, 248, 0.4) !important;
}
[data-testid="stChatInput"] textarea, .stChatInput textarea, textarea[data-testid="stChatInputTextArea"] {
    background: transparent !important;
    color: #f8fafc !important;
    -webkit-text-fill-color: #f8fafc !important;
    caret-color: #38bdf8 !important;
    font-size: 0.98rem !important;
    font-weight: 500 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    line-height: 1.5 !important;
}
[data-testid="stChatInput"] button, [data-testid="stChatInputSubmitButton"] {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
}
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
        <p>Clinical Assessment Portal</p>
    </div>
    """, unsafe_allow_html=True)
    st.error("🚨 **GEMINI_API_KEY not found in environment!**")
    st.markdown("""
    **To set up your API key:**
    1. Get a **free** key from [Google AI Studio](https://aistudio.google.com/app/apikey)
    2. Add `GEMINI_API_KEY=your_key_here` in `.env` file
    3. Restart the application.
    """)
    st.stop()


# ═══════════════════════════════════════════════════════════════
# 3. ACTUAL DOCTORS DIRECTORY (Loaded from verified JSON dataset)
# ═══════════════════════════════════════════════════════════════
PSYCHOLOGISTS = {
    "dr-amina-iftikhar-bhatti": {
        "id": "dr-amina-iftikhar-bhatti",
        "name": "Dr. Amina Iftikhar Bhatti",
        "title": "Consultant Clinical & Counseling Psychologist",
        "city": "Lahore",
        "country": "Pakistan",
        "experience_years": 16,
        "qualifications": [
            "PhD in Counseling Psychology (Universiti Utara Malaysia)",
            "MS in Clinical & Counseling Psychology (Kinnaird College)",
            "MSc in Psychology (University of the Punjab)",
            "MA in Special Education (AIOU)",
            "Certification in General Psychiatric Management for BPD (Harvard Medical School)"
        ],
        "specializations": [
            "Eating Disorders", "Anxiety & Mood Disorders", "Personality Disorders (BPD)",
            "Relationship & Marital Counseling", "Child Developmental Issues (ADHD)"
        ],
        "therapeutic_approaches": ["Cognitive Behavioral Therapy (CBT)", "Dialectical Behavior Therapy (DBT)", "Acceptance and Commitment Therapy (ACT)"],
        "contact": {
            "phone": "+92 42 34500888",
            "helpline_oladoc": "+92 42 38900939",
            "direct_booking": "+92 317 1777509 / +92 326 8473783"
        },
        "clinics": [
            {"name": "Evercare Hospital", "address": "NESPAK Housing Scheme, Lahore"},
            {"name": "Rainbow Obesity & Eating Disorder Centre", "address": "Shadman 1, Lahore"}
        ],
        "profile_urls": {
            "marham": "https://www.marham.pk/online-consultation/psychologist/lahore/dr-amina-iftikhar-bhatti",
            "oladoc": "https://oladoc.com/pakistan/lahore/psychologist/dr-amina-iftikhar-bhatti"
        },
        "picture_url": "https://staticconnect-new.marham.pk/assets/doctors/6771/dr-amina-iftikhar-bhatti-psychologist-lahore-53_450X450.webp",
        "bio": "Dr. Amina Iftikhar Bhatti is a renowned Senior Clinical Psychologist in Lahore with 16+ years of experience. She specializes in mood disorders, eating disorders, personality disorders, and relationship therapy using evidence-based CBT and DBT frameworks."
    },
    "dr-tahira-rubab-hafeez": {
        "id": "dr-tahira-rubab-hafeez",
        "name": "Dr. Tahira Rubab Hafeez",
        "title": "Consultant Clinical Psychologist & Sex Therapist",
        "city": "Lahore",
        "country": "Pakistan",
        "experience_years": 12,
        "qualifications": [
            "PhD Scholar (Clinical Psychology)",
            "MS in Clinical Psychology",
            "Certified Sex & Relationship Therapist"
        ],
        "specializations": [
            "Stress & Anxiety Management", "Depression & Trauma Recovery",
            "Sexual Wellness & Sex Therapy", "Marital & Family Counseling"
        ],
        "therapeutic_approaches": ["Psychotherapy", "Cognitive Behavioral Therapy (CBT)", "Couples & Sex Therapy"],
        "contact": {
            "phone": "+92 311 1714470",
            "alternate_phone": "+92 311 4482787"
        },
        "clinics": [
            {"name": "Tahira Rubab Clinic (Johar Town Branch)", "address": "Johar Town, Lahore"},
            {"name": "Tahira Rubab Clinic (Iqbal Town Branch)", "address": "Allama Iqbal Town, Lahore"}
        ],
        "profile_urls": {
            "website": "https://tahirarubabhafeez.com",
            "oladoc": "https://oladoc.com/pakistan/lahore/psychologist/dr-tahira-rubab",
            "marham": "https://www.marham.pk/online-consultation/psychologist/lahore/dr-tahira-rubab"
        },
        "picture_url": "https://tahirarubabhafeez.com/wp-content/uploads/2021/05/dr-tahira-rubab.jpg",
        "bio": "Dr. Tahira Rubab Hafeez is a consultant clinical psychologist and renowned sex therapist in Lahore. She provides holistic mental health support, trauma-informed therapy, and sexual wellness counseling."
    },
    "ms-shabila-sharif": {
        "id": "ms-shabila-sharif",
        "name": "Ms. Shabila Sharif",
        "title": "Clinical Psychologist",
        "city": "Lahore",
        "country": "Pakistan",
        "experience_years": 9,
        "patient_satisfaction": "100%",
        "qualifications": [
            "MS in Clinical Psychology (University of Central Punjab, Lahore)",
            "BS in Applied Psychology (GCUF)"
        ],
        "specializations": [
            "Adult Psychology & Psychotherapy", "Childhood Behavioral & Developmental Issues",
            "Autism Spectrum & ADHD Counseling", "Clinical Depression & OCD Therapy"
        ],
        "therapeutic_approaches": ["Behavioral Therapy", "Cognitive Behavioral Therapy (CBT)", "Child & Family Counseling"],
        "contact": {
            "marham_helpline": "+92 42 34500888",
            "booking_phone": "+92 311 1222398"
        },
        "clinics": [
            {"name": "Connect With Healing Souls", "address": "Lahore (Timings: Mon-Sat 11:00 AM - 8:00 PM)"},
            {"name": "MedCure Hospital", "address": "Johar Town, Lahore"}
        ],
        "profile_urls": {
            "marham": "https://www.marham.pk/online-consultation/psychologist/lahore/ms-shabila-sharif"
        },
        "picture_url": "https://img.marham.pk/doctors/22410/ms-shabila-sharif-psychologist-lahore-88_170x170.jpg",
        "bio": "Ms. Shabila Sharif is a top-rated Clinical Psychologist in Lahore with 9 years of clinical experience specializing in adult psychotherapy, OCD, depression, and child behavioral therapy."
    },
    "ms-tahira-maalik": {
        "id": "ms-tahira-maalik",
        "name": "Ms. Tahira Maalik",
        "title": "Consultant Clinical Psychologist & Hypnotherapist",
        "city": "Lahore",
        "country": "Pakistan",
        "experience_years": 10,
        "qualifications": [
            "MS in Clinical Psychology",
            "ADCP (Advanced Diploma in Clinical Psychology)",
            "MSc in Psychology",
            "Certified NLP Hypnotherapist"
        ],
        "specializations": [
            "Marital & Family Psychotherapy", "Addiction Counseling",
            "Behavioral Therapy", "Hypnotherapy & Mind Wellness"
        ],
        "therapeutic_approaches": ["Neuro-Linguistic Programming (NLP)", "Hypnotherapy", "Systemic Family Therapy"],
        "contact": {
            "phone": "+92 326 8473783",
            "booking_helpline": "+92 311 1222398"
        },
        "clinics": [
            {"name": "Friendz Table Guiding & Counselling Center", "address": "DHA, Lahore"}
        ],
        "profile_urls": {
            "marham": "https://www.marham.pk/online-consultation/psychologist/lahore/ms-tahira-maalik",
            "oladoc": "https://oladoc.com/pakistan/lahore/psychologist/ms-tahira-maalik"
        },
        "picture_url": "https://img.marham.pk/doctors/18502/ms-tahira-maalik-psychologist-lahore-15_170x170.jpg",
        "bio": "Ms. Tahira Maalik is an experienced Clinical Psychologist and certified Hypnotherapist based in DHA Lahore. She has 10+ years of expertise in family counseling, addiction recovery, and NLP hypnotherapy."
    }
}

PHQ9_QUESTIONS_LANG = {
    "English": [
        "Over the last 2 weeks, how often have you had little interest or pleasure in doing things?",
        "Over the last 2 weeks, how often have you felt down, depressed, or hopeless?",
        "Over the last 2 weeks, how often have you had trouble falling or staying asleep, or sleeping too much?",
        "Over the last 2 weeks, how often have you felt tired or had little energy?",
        "Over the last 2 weeks, how often have you had poor appetite or overeating?",
        "Over the last 2 weeks, how often have you felt bad about yourself or felt like a failure?",
        "Over the last 2 weeks, how often have you had trouble concentrating on things?",
        "Over the last 2 weeks, how often have you been moving/speaking slowly or being restless?",
        "Over the last 2 weeks, how often have you had thoughts that you would be better off dead or hurting yourself?",
    ],
    "Roman Urdu": [
        "Pichle 2 hafton mein, aapka kisi kaam mein dil ya khushi kitni baar nahi thi?",
        "Pichle 2 hafton mein, aap udaas, maayoos ya depressed kitna mehsoos kar rahe thay?",
        "Pichle 2 hafton mein, neend na aane ya ziyaada neend aane ka masla kitna tha?",
        "Pichle 2 hafton mein, aap thaka hua ya low energy kitna mehsoos kar rahe thay?",
        "Pichle 2 hafton mein, bhook na lagne ya ziyaada khaane ka masla kitna tha?",
        "Pichle 2 hafton mein, khud ko naakaam ya bura kitna mehsoos kar rahe thay?",
        "Pichle 2 hafton mein, dhyan ya focus lagane mein kitni mushkil hui?",
        "Pichle 2 hafton mein, bohot aahista chalne/bolne ya bechaini ka masla kitna tha?",
        "Pichle 2 hafton mein, khud ko nuksaan pahunchane ya marna chahne ke khayal kitni baar aaye?",
    ],
    "اردو": [
        "پچھلے 2 ہفتوں میں، آپ کا کسی کام میں دل یا خوشی کتنی بار نہیں تھی؟",
        "پچھلے 2 ہفتوں میں، آپ اداس، مایوس یا ڈیپریسڈ کتنا محسوس کر رہے تھے؟",
        "پچھلے 2 ہفتوں میں، نیند نہ آنے یا زیادہ نیند آنے کا مسئلہ کتنا تھا؟",
        "پچھلے 2 ہفتوں میں، آپ تھکا ہوا یا لو انرجی کتنا محسوس کر رہے تھے؟",
        "پچھلے 2 ہفتوں میں، بھوک نہ لگنے یا زیادہ کھانے کا مسئلہ کتنا تھا؟",
        "پچھلے 2 ہفتوں میں، خود کو ناکام یا برا کتنا محسوس کر رہے تھے؟",
        "پچھلے 2 ہفتوں میں، دھیان یا فوکس لگانے میں کتنی مشکل ہوئی؟",
        "پچھلے 2 ہفتوں میں، بہت آہستہ چلنے/بولنے یا بے چینی کا مسئلہ کتنا تھا؟",
        "پچھلے 2 ہفتوں میں، خود کو نقصان پہنچانے یا مرنا چاہنے کے خیال کتنی بار آئے؟",
    ]
}

GAD7_QUESTIONS_LANG = {
    "English": [
        "Over the last 2 weeks, how often have you felt nervous, anxious, or on edge?",
        "Over the last 2 weeks, how often have you been unable to stop or control worrying?",
        "Over the last 2 weeks, how often have you worried too much about different things?",
        "Over the last 2 weeks, how often have you had trouble relaxing?",
        "Over the last 2 weeks, how often have you been so restless that it's hard to sit still?",
        "Over the last 2 weeks, how often have you become easily annoyed or irritable?",
        "Over the last 2 weeks, how often have you felt afraid as if something awful might happen?",
    ],
    "Roman Urdu": [
        "Pichle 2 hafton mein, ghabrahat, anxiety ya tension kitni rehti thi?",
        "Pichle 2 hafton mein, soch aur fikr ko rokna kitna mushkil tha?",
        "Pichle 2 hafton mein, choti choti baaton ki ziyaada fikr kitni thi?",
        "Pichle 2 hafton mein, sukoon ya relax karna kitna mushkil tha?",
        "Pichle 2 hafton mein, bechaini ki wajah se ek jagah baithna kitna mushkil tha?",
        "Pichle 2 hafton mein, jaldi chidchidapan ya gussa kitna aata tha?",
        "Pichle 2 hafton mein, yeh darr kitna tha ke kuch bura hone wala hai?",
    ],
    "اردو": [
        "پچھلے 2 ہفتوں میں، گھبراہٹ، اینگزائٹی یا ٹینشن کتنی رہتی تھی؟",
        "پچھلے 2 ہفتوں میں، سوچ اور فکر کو روکنا کتنا مشکل تھا؟",
        "پچھلے 2 ہفتوں میں، چھوٹی چھوٹی باتوں کی زیادہ فکر کتنی تھی؟",
        "پچھلے 2 ہفتوں میں، سکون یا ریلیکس کرنا کتنا مشکل تھا؟",
        "پچھلے 2 ہفتوں میں، بے چینی کی وجہ سے ایک جگہ بیٹھنا کتنا مشکل تھا؟",
        "پچھلے 2 ہفتوں میں، جلدی چڑچڑاپن یا غصہ کتنا آتا تھا؟",
        "پچھلے 2 ہفتوں میں، یہ ڈر کتنا تھا کہ کچھ برا ہونے والا ہے؟",
    ]
}

SCORE_RESPONSE_MAP = {
    # English
    "not at all": 0, "no": 0, "none": 0,
    "several days": 1, "sometimes": 1, "some days": 1,
    "more than half the days": 2, "more than half": 2, "mostly": 2, "often": 2,
    "nearly every day": 3, "every day": 3, "always": 3, "daily": 3,
    
    # Roman Urdu
    "bilkul nahi": 0, "bilkul nhi": 0, "nahi": 0, "nhi": 0, "nahin": 0, "na": 0,
    "kuch din": 1, "kuchdin": 1, "kuch baar": 1, "kabhi kabhi": 1, "kbhi kbhi": 1, "thoda": 1, "kuch": 1, "kch": 1,
    "adhe se zyada": 2, "zyada tar": 2, "ziyada tar": 2, "zyadatar": 2, "ziyadatar": 2, "zyada": 2, "ziyada": 2, "aksar": 2, "half": 2,
    "hamesha": 3, "har roz": 3, "harroz": 3, "roz": 3, "baar baar": 3,
    
    # Urdu
    "بالکل نہیں": 0, "نہیں": 0, "نا": 0,
    "کچھ دن": 1, "کچھ بار": 1, "کبھی کبھی": 1, "تھوڑا": 1, "کچھ": 1,
    "زیادہ تر": 2, "آدھے سے زیادہ": 2, "اکثر": 2, "زیادہ": 2,
    "ہر روز": 3, "ہمیشہ": 3, "روز": 3, "بار بار": 3,

    "0": 0, "1": 1, "2": 2, "3": 3,
}

CRISIS_KEYWORDS = [
    r'\bsuicid\b', r'\bself.?harm\b', r'\bhurt myself\b', r'\bkill myself\b',
    r'\bend my life\b', r'\btake my life\b', r'\bwant to die\b', r'\bwish i was dead\b',
    r'\bno reason to live\b', r'\bbetter off dead\b', r'\boverdose\b',
    r'khudkushi', r'khud.?kushi', r'marna chahta', r'marna chahti',
    r'zindagi khatam', r'jina nahi chahta', r'jina nahi chahti',
    r'apne aap ko hurt', r'maut ki tamanna', r'dunya se chala jana',
    r'apne aap ko nuksaan', r'khud ko nuksaan', r'khud ko takleef',
    r'khatam karna chahta', r'khatam karna chahti',
]
CRISIS_PATTERN = re.compile('|'.join(CRISIS_KEYWORDS), re.IGNORECASE)

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
# 4. CUSTOM EMBEDDING FUNCTION & CHROMADB
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


@st.cache_resource(show_spinner="🔗 Connecting to Clinical Knowledge Base...")
def get_chroma_collection(key: str):
    db_client = chromadb.PersistentClient(path="./chroma_db")
    embedder = GeminiEmbeddingFunction(key=key)
    try:
        return db_client.get_collection(name="clinical_manuals", embedding_function=embedder)
    except Exception:
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
    err_str = str(e)
    if "401" in err_str or "UNAUTHENTICATED" in err_str or "invalid authentication" in err_str.lower():
        st.markdown("""
        <div class="header-banner">
            <h1>🧠 PsyScreen-RAG</h1>
            <p>Clinical Assessment Portal</p>
        </div>
        """, unsafe_allow_html=True)
        st.error("🚨 **Gemini API Key Authentication Error (401 Unauthenticated)**")
        st.markdown("""
        The `GEMINI_API_KEY` provided in environment / Streamlit Cloud secrets is invalid or expired.

        **How to fix on Streamlit Cloud:**
        1. Get a free API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
        2. Open your **Streamlit Cloud Dashboard**.
        3. Go to **Settings → Secrets**.
        4. Add your valid key:
           ```toml
           GEMINI_API_KEY = "AIzaSy..."
           ```
        5. Save and reload the app.
        """)
        st.stop()
    else:
        st.error(f"🚨 **Clinical Knowledge Base Error**: Could not connect to ChromaDB database. Details: `{e}`")
        st.stop()


# ═══════════════════════════════════════════════════════════════
# 5. PDF REPORT GENERATOR & EMAIL NOTIFIER
# ═══════════════════════════════════════════════════════════════
def clean_pdf_text(text: str) -> str:
    """Sanitize strings for ReportLab PDF generation to prevent Unicode encoding errors."""
    if not text:
        return ""
    str_val = str(text)
    if str_val == "اردو":
        return "Urdu (اردو)"
    cleaned = []
    for ch in str_val:
        if ord(ch) < 256:
            cleaned.append(ch)
        else:
            cleaned.append(f"&#{ord(ch)};")
    return "".join(cleaned)


def generate_pdf_report(report_data: dict) -> bytes:
    """Generate a clean, professional clinical PDF report using ReportLab."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e1b4b"),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
        spaceAfter=12
    )
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#4f46e5"),
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#1e293b")
    )
    
    story = []
    
    # Header Title
    story.append(Paragraph("<b>PsyScreen-RAG | Clinical Mental Health Assessment Report</b>", title_style))
    story.append(Paragraph("Confidential Clinical Evaluation Record • Developed for MS Thesis Research", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#6366f1"), spaceAfter=12))
    
    p_name = clean_pdf_text(report_data.get('patient_name', 'Patient'))
    p_email = clean_pdf_text(report_data.get('patient_email', 'N/A'))
    doc_name = clean_pdf_text(report_data.get('psychologist_name', 'N/A'))
    lang_txt = clean_pdf_text(report_data.get('language', 'English'))

    # Patient & Meta Information Table
    patient_info = [
        [Paragraph(f"<b>Patient Name:</b> {p_name}", body_style),
         Paragraph(f"<b>Report ID:</b> {report_data.get('id', 'N/A')}", body_style)],
        [Paragraph(f"<b>Patient Email:</b> {p_email}", body_style),
         Paragraph(f"<b>Assigned Doctor:</b> {doc_name}", body_style)],
        [Paragraph(f"<b>Assessment Date:</b> {report_data.get('timestamp', datetime.datetime.now()).strftime('%Y-%m-%d %H:%M')}", body_style),
         Paragraph(f"<b>Language:</b> {lang_txt}", body_style)]
    ]
    t_info = Table(patient_info, colWidths=[270, 270])
    t_info.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('PADDING', (0,0), (-1,-1), 6),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 10))
    
    # Assessment Summary Metrics Table
    story.append(Paragraph("Clinical Metrics & Severity Summary", heading_style))
    metrics_data = [
        [Paragraph("<b>Assessment Scale</b>", body_style), Paragraph("<b>Total Score</b>", body_style), Paragraph("<b>Severity Level</b>", body_style)],
        [Paragraph("PHQ-9 Mood Assessment", body_style), Paragraph(f"{report_data.get('phq9_total', 0)} / 27", body_style), Paragraph(f"{clean_pdf_text(report_data.get('phq9_sev', ('N/A',''))[0])}", body_style)],
        [Paragraph("GAD-7 Tension Assessment", body_style), Paragraph(f"{report_data.get('gad7_total', 0)} / 21", body_style), Paragraph(f"{clean_pdf_text(report_data.get('gad7_sev', ('N/A',''))[0])}", body_style)]
    ]
    t_metrics = Table(metrics_data, colWidths=[200, 140, 200])
    t_metrics.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e0e7ff")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#3730a3")),
        ('PADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
    ]))
    story.append(t_metrics)
    story.append(Spacer(1, 12))
    
    # CBT Recommendations
    story.append(Paragraph("CBT Psychoeducational Guidance", heading_style))
    cbt_text = get_cbt_recommendations(report_data.get('phq9_total'), report_data.get('gad7_total'))
    story.append(Paragraph(clean_pdf_text(cbt_text).replace("\n", "<br/>"), body_style))
    story.append(Spacer(1, 12))
    
    # Doctor Feedback if reviewed
    if report_data.get('psychologist_notes'):
        story.append(Paragraph("Attending Doctor Clinical Verdict & Notes", heading_style))
        story.append(Paragraph(f"<b>Status:</b> {clean_pdf_text(report_data.get('status'))}", body_style))
        story.append(Paragraph(f"<b>Doctor Feedback:</b> {clean_pdf_text(report_data.get('psychologist_notes'))}", body_style))
        story.append(Spacer(1, 12))

    # Disclaimer Footer
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#94a3b8"), spaceBefore=15, spaceAfter=8))
    disclaimer = ("⚠️ <b>Medical Disclaimer:</b> This report is generated by PsyScreen-RAG for clinical research evaluation. "
                  "It is intended for review by licensed mental health professionals and does not replace formal medical diagnosis.")
    story.append(Paragraph(disclaimer, ParagraphStyle('Disclaimer', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor("#64748b"))))
    
    doc.build(story)
    return buffer.getvalue()


def send_email_notification(recipient_email: str, patient_name: str, doc_name: str, verdict: str, notes: str) -> dict:
    """Send review notification email from msdsf23m027@pucit.edu.pk and log to session outbox."""
    sender_email = "msdsf23m027@pucit.edu.pk"
    
    subject = f"Psychologist Review Complete — PsyScreen-RAG ({doc_name})"
    body = (
        f"Dear {patient_name},\n\n"
        f"Your mental health assessment report has been reviewed by {doc_name}.\n\n"
        f"📌 Clinical Verdict: {verdict}\n"
        f"💬 Doctor Feedback: {notes}\n\n"
        f"You can view your full report and book a 1-on-1 consultation by visiting the PsyScreen-RAG Patient Portal.\n\n"
        f"Warm regards,\n"
        f"PsyScreen-RAG Clinical Team\n"
        f"Sender: {sender_email}"
    )

    email_obj = {
        "sender": sender_email,
        "recipient": recipient_email,
        "patient_name": patient_name,
        "doc_name": doc_name,
        "subject": subject,
        "body": body,
        "timestamp": datetime.datetime.now()
    }

    if "email_outbox" not in st.session_state:
        st.session_state.email_outbox = []
    st.session_state.email_outbox.insert(0, email_obj)

    smtp_pass = os.getenv("SMTP_PASSWORD") or os.getenv("EMAIL_PASSWORD")
    smtp_user = os.getenv("SMTP_USER") or sender_email

    if smtp_pass:
        try:
            # Attempt Gmail / Google Workspace SMTP
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg.set_content(body)

            smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))

            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            return {"success": True, "real_smtp": True, "error": None}
        except Exception as e:
            return {"success": True, "real_smtp": False, "error": str(e)}
    
    return {"success": True, "real_smtp": False, "error": "SMTP_PASSWORD not configured in .env"}


# ═══════════════════════════════════════════════════════════════
# 6. HELPER FUNCTIONS & LLM INTEGRATION
# ═══════════════════════════════════════════════════════════════
def rag_retrieve(query: str, n_results: int = 4) -> str:
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
    return bool(CRISIS_PATTERN.search(text))


def parse_score_from_response(response_text: str) -> int | None:
    text_lower = response_text.lower().strip()
    
    # Map Eastern/Western Arabic & Urdu numerals to ASCII digits
    urdu_digit_map = {
        '۰': '0', '۱': '1', '۲': '2', '۳': '3',
        '٠': '0', '١': '1', '٢': '2', '٣': '3'
    }
    for u_digit, ascii_digit in urdu_digit_map.items():
        text_lower = text_lower.replace(u_digit, ascii_digit)

    # First check explicit ASCII digit match
    match = re.search(r'\b([0-3])\b', text_lower)
    if match:
        return int(match.group(1))

    # Then check dictionary matches
    for key, val in SCORE_RESPONSE_MAP.items():
        if len(key) <= 2:
            if re.search(r'\b' + re.escape(key) + r'\b', text_lower):
                return val
        elif key in text_lower:
            return val

    return None


def get_severity(score: int, scale: str) -> tuple[str, str, str]:
    thresholds = PHQ9_SEVERITY if scale == "PHQ9" else GAD7_SEVERITY
    for max_score, label, css, emoji in thresholds:
        if score <= max_score:
            return label, css, emoji
    return "Unknown", "minimal", "❓"


def get_cbt_recommendations(phq9_score: int | None, gad7_score: int | None) -> str:
    recs = []
    if phq9_score is not None:
        if phq9_score <= 4:
            recs.append("🏃 **Behavioral Health (Low Mood):** Maintain healthy baseline routines — regular sleep schedule, outdoor activity, and social connection.")
        elif phq9_score <= 9:
            recs.append("📝 **Behavioral Activation:** Schedule 2-3 structured pleasant activities daily. Use a Thought Record to reframe automatic negative thoughts.")
        elif phq9_score <= 14:
            recs.append("🧠 **Cognitive Restructuring:** Structured CBT intervention is advised. Focus on identifying cognitive distortions and activity scheduling.")
        else:
            recs.append("🩺 **Clinical Consultation Recommended:** Comprehensive medical and clinical evaluation recommended alongside structured CBT.")

    if gad7_score is not None:
        if gad7_score <= 4:
            recs.append("🧘 **Anxiety Baseline:** Practice daily diaphragmatic breathing and box breathing (4-4-4-4).")
        elif gad7_score <= 9:
            recs.append("⏰ **Worry Management:** Implement scheduled 'Worry Postponement' (15 min daily worry slot) and 5-4-3-2-1 Grounding.")
        elif gad7_score <= 14:
            recs.append("🛡️ **Exposure & Cognitive Reframing:** Build an Exposure Hierarchy and work on anxiety tolerance skills.")
        else:
            recs.append("🩺 **Clinical Consultation Recommended:** Urgent consultation with a qualified psychologist or physician advised.")

    return "\n\n".join(recs) if recs else "Maintain baseline self-care practices."


def add_message(role: str, content: str):
    st.session_state.chat_history.append({"role": role, "content": content})


# ═══════════════════════════════════════════════════════════════
# 7. SESSION STATE INITIALIZATION
# ═══════════════════════════════════════════════════════════════
def init_session():
    now = datetime.datetime.now()
    
    sample_reports = [
        {
            "id": "RPT-8042",
            "patient_name": "Hamza Ali",
            "patient_email": "hamza.ali@example.com",
            "language": "Roman Urdu",
            "psychologist_id": "dr-amina-iftikhar-bhatti",
            "psychologist_name": "Dr. Amina Iftikhar Bhatti",
            "timestamp": now - datetime.timedelta(hours=2, minutes=15),
            "sla_deadline": now + datetime.timedelta(hours=5, minutes=45),
            "phq9_scores": [2, 3, 2, 2, 1, 2, 1, 1, 0],
            "gad7_scores": [2, 2, 3, 2, 1, 2, 1],
            "phq9_total": 14,
            "gad7_total": 13,
            "phq9_sev": ("Moderate", "moderate", "🟠"),
            "gad7_sev": ("Moderate", "moderate", "🟠"),
            "status": "Pending Review",
            "psychologist_notes": "",
            "reviewed_at": None,
        }
    ]

    defaults = {
        "genai_client": genai.Client(api_key=api_key),
        "app_mode": "patient",           # "patient" or "psychologist"
        "chat_history": [],              # [{role, content}]
        "state": "COLLECT_LANG",          # state machine stage
        "patient_name": "",
        "patient_email": "",
        "language": "English",
        "selected_psychologist": "dr-amina-iftikhar-bhatti",
        "current_test": None,
        "current_q_index": 0,
        "phq9_scores": [],
        "gad7_scores": [],
        "crisis_triggered": False,
        "active_patient_report_id": None,
        "reports_db": sample_reports,
        "doctor_authed": {},
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    if not st.session_state.chat_history:
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": (
                "Hello! 🧠 I am **PsyScreen-RAG**, your AI Mental Health Assessment Assistant.\n\n"
                "Please select your preferred language / اپنی زبان منتخب کریں:"
            )
        })

init_session()


# ═══════════════════════════════════════════════════════════════
# 8. LLM ENGINE (Gemini + RAG Context)
# ═══════════════════════════════════════════════════════════════
SYSTEM_PROMPT = """
You are "PsyScreen-RAG", a compassionate clinical AI assistant.
CORE RULES:
1. Follow RAG context provided.
2. Ask EXACTLY ONE question at a time.
3. Support English, Urdu (اردو), and Roman Urdu. Match user's language.
4. NEVER provide a direct psychiatric disease diagnosis to the patient.
5. If self-harm keywords appear, trigger CRISIS_ALERT_TRIGGERED immediately.
"""

_MODELS = ["gemini-2.5-flash", "gemini-3-flash-preview", "gemini-1.5-flash", "gemini-1.5-flash-8b", "gemini-1.0-pro"]

def llm_chat(user_message: str, extra_context: str = "") -> str:
    client = st.session_state.genai_client
    history = []
    for msg in st.session_state.chat_history[-10:]:
        role = "user" if msg["role"] == "user" else "model"
        history.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))

    full_prompt = f"{SYSTEM_PROMPT}\n\n"
    if extra_context:
        full_prompt += f"=== CLINICAL KNOWLEDGE BASE (RAG Context) ===\n{extra_context}\n\n=== END CONTEXT ===\n\n"
    full_prompt += f"User message: {user_message}"

    for model_name in _MODELS:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=history + [types.Content(role="user", parts=[types.Part(text=full_prompt)])],
                )
                return response.text.strip()
            except Exception as e:
                err_str = str(e)
                if "401" in err_str or "UNAUTHENTICATED" in err_str:
                    return "🚨 **Gemini API Key Error (401)**: Please check your `.env` file key."
                elif "429" in err_str or "quota" in err_str.lower():
                    time.sleep(2 * (attempt + 1))
                else:
                    break
    return "Service temporarily unavailable due to API quota limits. Please try again."


# ═══════════════════════════════════════════════════════════════
# 9. STATE MACHINE & ONBOARDING FLOW
# ═══════════════════════════════════════════════════════════════
def advance_state(user_input: str):
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
                   "The assessment has been paused. Please reach out for support.")
        add_message("assistant", bot_msg)
        return

    # ── 1. COLLECT LANGUAGE ───────────────────────────────────
    if state == "COLLECT_LANG":
        inp = user_input.lower().strip()
        if "roman" in inp or "minglish" in inp:
            lang = "Roman Urdu"
        elif "urdu" in inp or "اردو" in inp:
            lang = "اردو"
        else:
            lang = "English"

        st.session_state.language = lang
        st.session_state.state = "COLLECT_NAME_EMAIL"

        if lang == "Roman Urdu":
            bot_msg = "Shukriya! Aage barhne ke liye apna **Naam aur Email Address** enter karein:"
        elif lang == "اردو":
            bot_msg = "شکریہ! آگے بڑھنے کے لیے اپنا **نام اور ای میل ایڈریس** درج کریں:"
        else:
            bot_msg = "Thank you! Please enter your **Name and Email Address** to get started:"

        add_message("assistant", bot_msg)

    # ── 2. COLLECT NAME & EMAIL ───────────────────────────────
    elif state == "COLLECT_NAME_EMAIL":
        parts = user_input.split("|")
        name = parts[0].strip() if len(parts) > 0 else "Patient"
        email = parts[1].strip() if len(parts) > 1 else "patient@example.com"

        st.session_state.patient_name = name or "Patient"
        st.session_state.patient_email = email or "patient@example.com"
        st.session_state.state = "SELECT_PSYCHOLOGIST"

        lang = st.session_state.language
        if lang == "Roman Urdu":
            bot_msg = f"Khushamdeed, **{st.session_state.patient_name}**! 💙\n\nKripya apna preferred Doctor select karein jo aapki assessment report review karenge:"
        elif lang == "اردو":
            bot_msg = f"خوش آمدید، **{st.session_state.patient_name}**! 💙\n\nبرائے مہربانی اپنا ڈاکٹر منتخب کریں جو آپ کی رپورٹ دیکھیں گے:"
        else:
            bot_msg = f"Welcome, **{st.session_state.patient_name}**! 💙\n\nPlease select your preferred Clinical Psychologist / Doctor to review your assessment:"

        add_message("assistant", bot_msg)

    # ── 3. SELECT PSYCHOLOGIST ────────────────────────────────
    elif state == "SELECT_PSYCHOLOGIST":
        psych_key = user_input if user_input in PSYCHOLOGISTS else "dr-amina-iftikhar-bhatti"
        st.session_state.selected_psychologist = psych_key
        st.session_state.state = "START_QUESTIONS"
        
        psych = PSYCHOLOGISTS[psych_key]
        lang = st.session_state.language

        if lang == "Roman Urdu":
            bot_msg = f"Aapne **{psych['name']}** ko select kar liya hai. ✅\n\nAb hum **Wellbeing Survey** shuru karte hain. Main aap se pichle 2 hafton ke bare mein simple questions poochon ga."
        elif lang == "اردو":
            bot_msg = f"آپ نے **{psych['name']}** کا انتخاب کر لیا ہے۔ ✅\n\nاب ہم **ویلبیئنگ سروے** شروع کرتے ہیں۔ میں آپ سے پچھلے 2 ہفتوں کے بارے میں کچھ سادہ سوالات پوچھوں گا۔"
        else:
            bot_msg = f"You have selected **{psych['name']}**. ✅\n\nWe will now begin the **Wellbeing Survey**. I will ask you a few simple questions about your feelings over the past 2 weeks."

        add_message("assistant", bot_msg)
        
        # Start first question
        st.session_state.current_test = "PHQ9"
        st.session_state.current_q_index = 0
        st.session_state.state = "QUESTIONING"
        _ask_current_question()

    # ── 4. QUESTIONING ─────────────────────────────────────────
    elif state == "QUESTIONING":
        score = parse_score_from_response(user_input)
        lang = st.session_state.language

        if score is None:
            if lang == "Roman Urdu":
                bot_msg = "Kripya in options mein se select karein: 0 (Bilkul nahi), 1 (Kuch din), 2 (Zyada tar), 3 (Har roz)."
            elif lang == "اردو":
                bot_msg = "برائے مہربانی ان میں سے منتخب کریں: 0 (بالکل نہیں)، 1 (کچھ دن)، 2 (زیادہ تر)، 3 (ہر روز)۔"
            else:
                bot_msg = "Please select from: 0 (Not at all), 1 (Several days), 2 (More than half), 3 (Nearly every day)."
            add_message("assistant", bot_msg)
            return

        test = st.session_state.current_test
        q_idx = st.session_state.current_q_index
        questions_dict = PHQ9_QUESTIONS_LANG if test == "PHQ9" else GAD7_QUESTIONS_LANG
        q_list = questions_dict.get(lang, questions_dict["English"])

        if test == "PHQ9":
            st.session_state.phq9_scores.append(score)
            if q_idx == 8 and score >= 1:
                st.session_state.crisis_triggered = True
                bot_msg = ("🆘 **Safety Notice & Support Helplines:**\n"
                           "You indicated experiencing thoughts of self-harm or distress. Please know support is available 24/7:\n"
                           "📞 Umang Pakistan: **0317-4288665** | Rescue: **1122**\n\n"
                           "We are continuing the assessment so your assigned Clinical Psychologist receives your complete 16-question report.")
                add_message("assistant", bot_msg)
        else:
            st.session_state.gad7_scores.append(score)

        st.session_state.current_q_index += 1

        if st.session_state.current_q_index >= len(q_list):
            if test == "PHQ9":
                st.session_state.current_test = "GAD7"
                st.session_state.current_q_index = 0
                _ask_current_question()
            else:
                # All questions complete -> Present Submit & Download options!
                st.session_state.state = "SUBMIT_OR_DOWNLOAD"
                _present_completion_options()
        else:
            _ask_current_question()

    # ── 5. CBT CHAT (Post-Assessment Free Chat) ────────────────
    elif state == "CBT_CHAT":
        rag_ctx = rag_retrieve(user_input, n_results=5)
        bot_msg = llm_chat(
            f"The patient (Language: {st.session_state.language}) is asking: '{user_input}'. "
            f"Respond in {st.session_state.language} using ONLY the provided RAG context. Be concise, warm, and helpful.",
            rag_ctx
        )
        add_message("assistant", bot_msg)


def _ask_current_question():
    test = st.session_state.current_test
    q_idx = st.session_state.current_q_index
    lang = st.session_state.language

    questions_dict = PHQ9_QUESTIONS_LANG if test == "PHQ9" else GAD7_QUESTIONS_LANG
    q_list = questions_dict.get(lang, questions_dict["English"])
    total_qs = 16
    current_q_number = q_idx + 1 if test == "PHQ9" else 9 + q_idx + 1
    current_q = q_list[q_idx]

    if lang == "Roman Urdu":
        options_str = "0: Bilkul nahi | 1: Kuch din | 2: Zyada tar | 3: Har roz"
        header = f"**Question {current_q_number}/{total_qs}:**"
    elif lang == "اردو":
        options_str = "0: بالکل نہیں | 1: کچھ دن | 2: زیادہ تر | 3: ہر روز"
        header = f"**سوال {current_q_number}/{total_qs}:**"
    else:
        options_str = "0: Not at all | 1: Several days | 2: More than half | 3: Nearly every day"
        header = f"**Question {current_q_number}/{total_qs}:**"

    bot_msg = f"{header}\n{current_q}\n\n*({options_str})*"
    add_message("assistant", bot_msg)


def _present_completion_options():
    lang = st.session_state.language
    psych_id = st.session_state.selected_psychologist
    psych = PSYCHOLOGISTS[psych_id]

    if lang == "Roman Urdu":
        bot_msg = (
            f"✨ **Wellbeing Assessment Mukammal ho gayi hai!**\n\n"
            f"Aap niche diye gaye options mein se select kar sakte hain:\n"
            f"1. 🚀 **Submit Report to {psych['name']}** (Doctor 8 ghante ke andar review karke email bhejenge).\n"
            f"2. 📥 **Download Assessment Report (PDF)**"
        )
    elif lang == "اردو":
        bot_msg = (
            f"✨ **ویلبیئنگ سروے مکمل ہو گیا ہے!**\n\n"
            f"آپ نیچے دیے گئے اختیارات میں سے منتخب کر سکتے ہیں:\n"
            f"1. 🚀 **رپورٹ ڈاکٹر کو بھیجیں ({psych['name']})**\n"
            f"2. 📥 **پی ڈی ایف رپورٹ ڈاؤن لوڈ کریں (PDF)**"
        )
    else:
        bot_msg = (
            f"✨ **Assessment Completed!**\n\n"
            f"Please choose your next step below:\n"
            f"1. 🚀 **Submit Assessment Report to {psych['name']}** (Your doctor will review within 8 hours and email you).\n"
            f"2. 📥 **Download Assessment Report (PDF)**"
        )

    add_message("assistant", bot_msg)


def _dispatch_report_to_psychologist():
    phq9 = st.session_state.phq9_scores
    gad7 = st.session_state.gad7_scores
    name = st.session_state.patient_name
    email = st.session_state.patient_email
    lang = st.session_state.language
    psych_id = st.session_state.selected_psychologist
    psych = PSYCHOLOGISTS[psych_id]

    now = datetime.datetime.now()
    rpt_num = len(st.session_state.reports_db) + 8045
    rpt_id = f"RPT-{rpt_num}"

    phq9_total = sum(phq9) if phq9 else 0
    gad7_total = sum(gad7) if gad7 else 0

    new_report = {
        "id": rpt_id,
        "patient_name": name,
        "patient_email": email,
        "language": lang,
        "psychologist_id": psych_id,
        "psychologist_name": psych["name"],
        "timestamp": now,
        "sla_deadline": now + datetime.timedelta(hours=8),
        "phq9_scores": phq9,
        "gad7_scores": gad7,
        "phq9_total": phq9_total,
        "gad7_total": gad7_total,
        "phq9_sev": get_severity(phq9_total, "PHQ9"),
        "gad7_sev": get_severity(gad7_total, "GAD7"),
        "status": "Pending Review",
        "psychologist_notes": "",
        "reviewed_at": None,
    }

    st.session_state.reports_db.insert(0, new_report)
    st.session_state.active_patient_report_id = rpt_id
    st.session_state.state = "SUBMITTED"

    if lang == "Roman Urdu":
        bot_msg = (
            f"✅ **Report Dispatched Successfully!**\n\n"
            f"Aapki complete assessment report **{psych['name']}** ko submit kar di gayi hai.\n\n"
            f"📩 Doctor review ke baad aapko **{email}** par email miley gi (From: `msdsf23m027@pucit.edu.pk`).\n"
            f"⏱️ **8-Hour SLA Review Active**: Doctor 8 ghante ke andar aap ki report review karenge."
        )
    elif lang == "اردو":
        bot_msg = (
            f"✅ **رپورٹ ڈاکٹر کو بھیج دی گئی ہے!**\n\n"
            f"آپ کی رپورٹ **{psych['name']}** کو بھیج دی گئی ہے۔\n\n"
            f"📩 ڈاکٹر کے معائنے کے بعد آپ کو **{email}** پر ای میل موصول ہوگی (از طرف: `msdsf23m027@pucit.edu.pk`)۔"
        )
    else:
        bot_msg = (
            f"✅ **Report Dispatched Successfully!**\n\n"
            f"Your clinical assessment report has been securely submitted to **{psych['name']}**.\n\n"
            f"📩 You will receive an email update at **{email}** after doctor review (From: `msdsf23m027@pucit.edu.pk`).\n"
            f"⏱️ **8-Hour SLA Active**: Your doctor will review your report within 8 hours."
        )

    add_message("assistant", bot_msg)


# ═══════════════════════════════════════════════════════════════
# 10. SIDEBAR — ROLE SWITCHER & DOCTOR AUTHENTICATION
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🧠 PsyScreen-RAG")
    
    mode = st.radio(
        "📌 Select Portal Mode:",
        ["👤 Patient Portal", "🩺 Doctor Dashboard"],
        key="app_mode_radio"
    )
    st.session_state.app_mode = "patient" if "Patient" in mode else "psychologist"

    st.divider()

    if st.session_state.app_mode == "patient":
        langs_list = ["English", "Roman Urdu", "اردو"]
        curr_lang = st.session_state.get("language", "English")
        curr_idx = langs_list.index(curr_lang) if curr_lang in langs_list else 0

        lang_choice = st.selectbox(
            "🌐 Preferred Language / زبان",
            langs_list,
            index=curr_idx,
            key=f"sidebar_lang_select_{curr_lang}"
        )
        if lang_choice != st.session_state.language:
            st.session_state.language = lang_choice
            st.rerun()

        st.divider()
        if st.button("🔄 Start New Assessment", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.state = "COLLECT_LANG"
            st.session_state.phq9_scores = []
            st.session_state.gad7_scores = []
            st.session_state.active_patient_report_id = None
            st.rerun()

    else:
        st.markdown("### 🔒 Authorized Doctor Login")
        selected_psych = st.selectbox(
            "👨‍⚕️ Select Doctor Account:",
            options=list(PSYCHOLOGISTS.keys()),
            format_func=lambda k: PSYCHOLOGISTS[k]["name"],
            key="psych_login_select"
        )
        st.session_state.logged_in_psych = selected_psych

        # Doctor Password Authentication (Default: 0000)
        doc_password = st.text_input(
            "🔑 Enter Doctor Password:",
            type="password",
            placeholder="Default: 0000",
            key=f"pwd_input_{selected_psych}"
        )
        
        if doc_password == "0000":
            st.session_state.doctor_authed[selected_psych] = True
            st.success("✅ Password Verified! Doctor Workspace Unlocked.")
        elif doc_password:
            st.error("❌ Incorrect Password. Default password is `0000`.")
            st.session_state.doctor_authed[selected_psych] = False
        else:
            st.warning("🔒 Enter password `0000` to access portal.")

    st.divider()
    st.markdown("""
    <div style="background:rgba(30,41,59,0.5);border-radius:10px;padding:0.8rem;border:1px solid rgba(255,255,255,0.08);">
        <p style="color:#94a3b8;font-size:0.75rem;margin:0;">
        ⚠️ <strong>Clinical Disclaimer:</strong> Research screening tool for academic evaluation. Not an automated medical diagnostic device.
        </p>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# 11. PATIENT PORTAL UI
# ═══════════════════════════════════════════════════════════════
if st.session_state.app_mode == "patient":

    st.markdown("""
    <div class="header-banner">
        <h1>🧠 PsyScreen-RAG</h1>
        <p>Public Mental Health Assessment & Clinical Evaluation Portal</p>
    </div>
    """, unsafe_allow_html=True)

    # Crisis Alert
    if st.session_state.state == "CRISIS":
        st.markdown("""
        <div style="background:rgba(239,68,68,0.15);border:1.5px solid rgba(239,68,68,0.4);border-radius:16px;padding:1.5rem;margin-bottom:1rem;">
            <h3 style="color:#fca5a5;margin:0 0 0.5rem 0;">🆘 Urgent Crisis Support</h3>
            <p style="color:#f8fafc;font-size:0.9rem;">Please reach out to emergency helplines immediately:</p>
            <ul style="color:#fca5a5;font-size:0.9rem;line-height:1.8;">
                <li>📞 <strong>Umang Pakistan:</strong> 0317-4288665 (24/7)</li>
                <li>📞 <strong>Rozan Counseling:</strong> 051-2890505</li>
                <li>📞 <strong>Rescue Emergency:</strong> 1122</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("✅ I am safe and wish to continue", use_container_width=True):
            st.session_state.state = "CBT_CHAT"
            add_message("assistant", "I am glad you are safe. 💙 How can I help you with emotional wellbeing today?")
            st.rerun()

    # Render History
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"], avatar="🧠" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])

    # ── Onboarding & Interactive Buttons ──
    if st.session_state.state == "COLLECT_LANG":
        st.markdown("<p style='color:#94a3b8;font-size:0.85rem;margin-bottom:0.5rem;'>🌐 <strong>Select Preferred Language:</strong></p>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        if c1.button("🇬🇧 English", use_container_width=True):
            add_message("user", "English")
            advance_state("English")
            st.rerun()
        if c2.button("🇵🇰 Roman Urdu", use_container_width=True):
            add_message("user", "Roman Urdu")
            advance_state("Roman Urdu")
            st.rerun()
        if c3.button("🇵🇰 Urdu (اردو)", use_container_width=True):
            add_message("user", "Urdu (اردو)")
            advance_state("Urdu")
            st.rerun()

    elif st.session_state.state == "COLLECT_NAME_EMAIL":
        with st.form("name_email_form"):
            st.markdown("### 👤 Patient Information")
            p_name = st.text_input("Full Name:", value=st.session_state.patient_name, placeholder="e.g. Huraira")
            p_email = st.text_input("Email Address (for Doctor review notifications):", value=st.session_state.patient_email, placeholder="e.g. patient@example.com")
            submit_info = st.form_submit_button("🚀 Continue to Select Doctor", use_container_width=True)
            if submit_info:
                if p_name.strip() and p_email.strip():
                    combined = f"{p_name.strip()}|{p_email.strip()}"
                    add_message("user", f"Name: {p_name.strip()} | Email: {p_email.strip()}")
                    advance_state(combined)
                    st.rerun()
                else:
                    st.error("Please enter both Name and Email to continue.")

    elif st.session_state.state == "SELECT_PSYCHOLOGIST":
        st.markdown("<p style='color:#94a3b8;font-size:0.9rem;margin-bottom:1rem;'>👨‍⚕️ <strong>Select Your Preferred Doctor / Psychologist:</strong></p>", unsafe_allow_html=True)
        
        for p_key, p_info in PSYCHOLOGISTS.items():
            st.markdown(f"""
            <div class="doctor-card">
                <div style="display:flex;gap:15px;align-items:flex-start;">
                    <img src="{p_info['picture_url']}" style="width:75px;height:75px;border-radius:12px;object-fit:cover;border:2px solid #818cf8;">
                    <div style="flex-grow:1;">
                        <div style="font-weight:700;font-size:1.1rem;color:#38bdf8;">{p_info['name']}</div>
                        <div style="font-size:0.85rem;color:#c084fc;font-weight:600;">{p_info['title']} • {p_info['experience_years']} Yrs Exp</div>
                        <div style="font-size:0.8rem;color:#94a3b8;margin-top:2px;">📍 {p_info['city']}, {p_info['country']} | Clinics: {', '.join([c['name'] for c in p_info['clinics']])}</div>
                        <div style="font-size:0.82rem;color:#cbd5e0;margin-top:6px;">{p_info['bio']}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Select {p_info['name']}", key=f"btn_select_{p_key}", use_container_width=True):
                add_message("user", f"Selected {p_info['name']}")
                advance_state(p_key)
                st.rerun()

    elif st.session_state.state == "QUESTIONING":
        lang = st.session_state.language
        if lang == "Roman Urdu":
            b_labels = ["🟢 Bilkul nahi (0)", "🟡 Kuch din (1)", "🟠 Zyada tar (2)", "🔴 Har roz (3)"]
            b_vals = ["Bilkul nahi", "Kuch din", "Zyada tar", "Har roz"]
            header_txt = "👇 <strong>Jawab select karein:</strong>"
        elif lang == "اردو":
            b_labels = ["🟢 بالکل نہیں (0)", "🟡 کچھ دن (1)", "🟠 زیادہ تر (2)", "🔴 ہر روز (3)"]
            b_vals = ["بالکل نہیں", "کچھ دن", "زیادہ تر", "ہر روز"]
            header_txt = "👇 <strong>جواب منتخب کریں:</strong>"
        else:
            b_labels = ["🟢 Not at all (0)", "🟡 Several days (1)", "🟠 More than half (2)", "🔴 Nearly every day (3)"]
            b_vals = ["Not at all", "Several days", "More than half the days", "Nearly every day"]
            header_txt = "👇 <strong>Select your response:</strong>"

        st.markdown(f"<p style='color:#94a3b8;font-size:0.85rem;margin:0.5rem 0;'>{header_txt}</p>", unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        q_key = f"q_{st.session_state.current_test}_{st.session_state.current_q_index}"

        if col1.button(b_labels[0], key=f"{q_key}_0", use_container_width=True):
            add_message("user", b_vals[0])
            advance_state(b_vals[0])
            st.rerun()
        if col2.button(b_labels[1], key=f"{q_key}_1", use_container_width=True):
            add_message("user", b_vals[1])
            advance_state(b_vals[1])
            st.rerun()
        if col3.button(b_labels[2], key=f"{q_key}_2", use_container_width=True):
            add_message("user", b_vals[2])
            advance_state(b_vals[2])
            st.rerun()
        if col4.button(b_labels[3], key=f"{q_key}_3", use_container_width=True):
            add_message("user", b_vals[3])
            advance_state(b_vals[3])
            st.rerun()

    # ── Completion Options: Submit vs Download PDF ──
    elif st.session_state.state == "SUBMIT_OR_DOWNLOAD":
        psych_id = st.session_state.selected_psychologist
        psych = PSYCHOLOGISTS[psych_id]
        
        st.markdown("### 📋 Choose Action:")
        c_sub, c_pdf = st.columns(2)
        
        with c_sub:
            if st.button(f"🚀 Submit Report to {psych['name']}", use_container_width=True):
                _dispatch_report_to_psychologist()
                st.rerun()

        with c_pdf:
            # Generate PDF data
            temp_report_data = {
                "id": "DRAFT-REPORT",
                "patient_name": st.session_state.patient_name,
                "patient_email": st.session_state.patient_email,
                "language": st.session_state.language,
                "psychologist_name": psych['name'],
                "timestamp": datetime.datetime.now(),
                "phq9_total": sum(st.session_state.phq9_scores),
                "gad7_total": sum(st.session_state.gad7_scores),
                "phq9_sev": get_severity(sum(st.session_state.phq9_scores), "PHQ9"),
                "gad7_sev": get_severity(sum(st.session_state.gad7_scores), "GAD7"),
            }
            pdf_bytes = generate_pdf_report(temp_report_data)
            
            st.download_button(
                label="📥 Download Assessment Report (PDF)",
                data=pdf_bytes,
                file_name=f"psyscreen_assessment_{st.session_state.patient_name.replace(' ','_')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    # ── Submitted Patient Status & Email Toast ──
    if st.session_state.active_patient_report_id:
        rpt_id = st.session_state.active_patient_report_id
        matching_rpts = [r for r in st.session_state.reports_db if r["id"] == rpt_id]
        if matching_rpts:
            rpt = matching_rpts[0]
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("📋 Your Submitted Assessment Status", expanded=True):
                c_status, c_sla = st.columns(2)
                with c_status:
                    if rpt["status"] == "Pending Review":
                        st.markdown("**Status:** <span class='badge badge-mild'>⏳ Pending Doctor Review</span>", unsafe_allow_html=True)
                    elif "Normal" in rpt["status"]:
                        st.markdown("**Status:** <span class='badge badge-minimal'>🟢 Healthy / Normal Coping</span>", unsafe_allow_html=True)
                    else:
                        st.markdown("**Status:** <span class='badge badge-moderate'>🟠 Consultation Recommended</span>", unsafe_allow_html=True)

                with c_sla:
                    now = datetime.datetime.now()
                    rem_sec = (rpt["sla_deadline"] - now).total_seconds()
                    if rem_sec > 0 and rpt["status"] == "Pending Review":
                        hrs = int(rem_sec // 3600)
                        mins = int((rem_sec % 3600) // 60)
                        st.markdown(f"<div class='sla-badge'>⏱️ Review Expected Within: {hrs}h {mins}m</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div class='sla-badge' style='background:rgba(34,197,94,0.15);color:#4ade80;border-color:rgba(34,197,94,0.4);'>✅ Review Complete</div>", unsafe_allow_html=True)

                st.markdown("---")
                st.markdown(f"**Assigned Doctor:** {rpt['psychologist_name']}")
                st.markdown(f"**Registered Email:** `{rpt['patient_email']}`")

                if rpt["psychologist_notes"]:
                    st.markdown("### 💬 Doctor Clinical Feedback:")
                    st.info(f"\"{rpt['psychologist_notes']}\"")

                    # Live Received Email Inbox Card
                    patient_emails = [e for e in st.session_state.get("email_outbox", []) if e["recipient"] == rpt["patient_email"]]
                    if patient_emails:
                        latest_email = patient_emails[0]
                        st.markdown(f"""
                        <div style="background:rgba(99,102,241,0.12);border:1px solid rgba(129,140,248,0.3);border-radius:14px;padding:1rem;margin:1rem 0;">
                            <div style="font-weight:700;color:#38bdf8;font-size:0.95rem;margin-bottom:0.4rem;">
                                📩 New Email Received in Inbox ({latest_email['recipient']})
                            </div>
                            <div style="font-size:0.8rem;color:#94a3b8;margin-bottom:0.6rem;">
                                <strong>From:</strong> {latest_email['sender']} | <strong>Time:</strong> {latest_email['timestamp'].strftime('%H:%M:%S')}
                            </div>
                            <div style="font-size:0.85rem;color:#f8fafc;background:rgba(15,23,42,0.6);padding:0.8rem;border-radius:8px;white-space:pre-wrap;font-family:sans-serif;">
                                <strong>Subject: {latest_email['subject']}</strong><br><br>
                                {latest_email['body']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.caption("📩 Notification email sent from: `msdsf23m027@pucit.edu.pk`")

                    if "Consultation" in rpt["status"]:
                        st.markdown("### 📅 Schedule 1-on-1 Consultation")
                        if st.button("📅 Book Appointment Now", use_container_width=True):
                            st.success(f"✅ Appointment request dispatched to {rpt['psychologist_name']}!")

                # PDF Download button for submitted report
                pdf_bytes_submitted = generate_pdf_report(rpt)
                st.download_button(
                    label="📥 Download Submitted Report (PDF)",
                    data=pdf_bytes_submitted,
                    file_name=f"psyscreen_report_{rpt['id']}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

    # Chat Input Box
    if st.session_state.state not in ["CRISIS"]:
        placeholder = "Type your message or response..."
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


# ═══════════════════════════════════════════════════════════════
# 12. DOCTOR DASHBOARD (Password Protected: 0000)
# ═══════════════════════════════════════════════════════════════
else:
    logged_psych_id = st.session_state.get("logged_in_psych", "dr-amina-iftikhar-bhatti")
    is_authed = st.session_state.doctor_authed.get(logged_psych_id, False)

    psych_info = PSYCHOLOGISTS[logged_psych_id]

    st.markdown(f"""
    <div class="header-banner" style="border-left: 4px solid #818cf8;">
        <h1>🩺 Doctor Workspace & Patient Queue</h1>
        <p>Logged in as <strong>{psych_info['name']}</strong> ({psych_info['title']})</p>
    </div>
    """, unsafe_allow_html=True)

    if not is_authed:
        st.warning("🔒 **Doctor Authentication Required**: Enter password in the sidebar (Default: `0000`) to unlock patient queue.")
    else:
        # Filter reports assigned to this doctor
        doc_reports = [r for r in st.session_state.reports_db if r["psychologist_id"] == logged_psych_id or r["psychologist_id"] == "dr_ayesha"]
        pending_rpts = [r for r in doc_reports if r["status"] == "Pending Review"]
        reviewed_rpts = [r for r in doc_reports if r["status"] != "Pending Review"]
        normal_rpts = [r for r in doc_reports if "Normal" in r["status"]]
        consult_rpts = [r for r in doc_reports if "Consultation" in r["status"]]

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("📊 Total Patient Reports", len(doc_reports))
        col_m2.metric("⏳ Pending Review (8h SLA)", len(pending_rpts))
        col_m3.metric("🟢 Normal / Healthy", len(normal_rpts))
        col_m4.metric("🟠 Consultation Advised", len(consult_rpts))

        st.divider()

        tab_pending, tab_reviewed = st.tabs([
            f"⏳ Pending SLA Queue ({len(pending_rpts)})",
            f"✅ Reviewed History ({len(reviewed_rpts)})"
        ])

        # ── PENDING QUEUE ──
        with tab_pending:
            if not pending_rpts:
                st.success("🎉 No pending patient reviews in your queue!")
            else:
                for idx, rpt in enumerate(pending_rpts):
                    now = datetime.datetime.now()
                    rem_sec = (rpt["sla_deadline"] - now).total_seconds()
                    hrs = int(rem_sec // 3600) if rem_sec > 0 else 0
                    mins = int((rem_sec % 3600) // 60) if rem_sec > 0 else 0

                    sla_txt = f"⏱️ SLA: {hrs}h {mins}m left" if rem_sec > 0 else "🚨 SLA OVERDUE"

                    with st.expander(f"👤 {rpt['patient_name']} — {rpt['id']} ({rpt.get('patient_email','N/A')}) | {sla_txt}", expanded=(idx==0)):
                        c_info1, c_info2 = st.columns(2)
                        with c_info1:
                            st.markdown(f"**Patient Name:** {rpt['patient_name']}")
                            st.markdown(f"**Patient Email:** `{rpt.get('patient_email','N/A')}`")
                            st.markdown(f"**Submitted:** {rpt['timestamp'].strftime('%Y-%m-%d %H:%M')}")
                        with c_info2:
                            phq_label, phq_css, phq_emo = rpt['phq9_sev']
                            gad_label, gad_css, gad_emo = rpt['gad7_sev']
                            st.markdown(f"**PHQ-9 Score:** {rpt['phq9_total']}/27 <span class='badge badge-{phq_css}'>{phq_emo} {phq_label}</span>", unsafe_allow_html=True)
                            st.markdown(f"**GAD-7 Score:** {rpt['gad7_total']}/21 <span class='badge badge-{gad_css}'>{gad_emo} {gad_label}</span>", unsafe_allow_html=True)

                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown("#### 🧘 RAG CBT Psychoeducational Guidance")
                        st.markdown(get_cbt_recommendations(rpt['phq9_total'], rpt['gad7_total']))

                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown("#### ✍️ Issue Clinical Verdict & Send Email Notification")

                        verdict = st.radio(
                            "Clinical Verdict:",
                            ["🟢 Normal / Healthy (No consultation needed)", "🟠 Consultation Recommended (Schedule session)"],
                            key=f"verdict_radio_{rpt['id']}"
                        )

                        default_note = "Your screening responses indicate healthy coping. Continue maintaining balanced routines." if "Normal" in verdict else "Based on your screening responses, a structured 1-on-1 CBT consultation is recommended."
                        
                        feedback_note = st.text_area(
                            "Clinical Feedback Note (Will be emailed to patient):",
                            value=default_note,
                            key=f"feedback_{rpt['id']}"
                        )

                        if st.button("🚀 Submit Review & Email Patient", key=f"btn_submit_{rpt['id']}", use_container_width=True):
                            status_val = "Normal / Healthy" if "Normal" in verdict else "Consultation Recommended"
                            rpt["status"] = status_val
                            rpt["psychologist_notes"] = feedback_note
                            rpt["reviewed_at"] = datetime.datetime.now()

                            # Dispatch email from msdsf23m027@pucit.edu.pk
                            res = send_email_notification(
                                recipient_email=rpt.get("patient_email", "patient@example.com"),
                                patient_name=rpt["patient_name"],
                                doc_name=psych_info["name"],
                                verdict=status_val,
                                notes=feedback_note
                            )

                            if res.get("real_smtp"):
                                st.success(f"✅ Review submitted & REAL email sent to `{rpt.get('patient_email')}` from `msdsf23m027@pucit.edu.pk`!")
                            else:
                                st.success(f"✅ Review submitted & Notification Email delivered to Patient Portal from `msdsf23m027@pucit.edu.pk`!")
                                st.info("ℹ️ *To enable real SMTP email delivery over the internet to real inboxes, add `EMAIL_PASSWORD=your_16_char_app_password` in `.env` file.*")
                            
                            st.rerun()

        # ── REVIEWED HISTORY ──
        with tab_reviewed:
            if not reviewed_rpts:
                st.info("No reviewed reports in history yet.")
            else:
                for rpt in reviewed_rpts:
                    with st.expander(f"✅ {rpt['patient_name']} — {rpt['id']} | Verdict: {rpt['status']}"):
                        st.markdown(f"**Patient Email:** `{rpt.get('patient_email','N/A')}`")
                        st.markdown(f"**Reviewed At:** {rpt['reviewed_at'].strftime('%Y-%m-%d %H:%M') if rpt['reviewed_at'] else 'Recently'}")
                        st.markdown(f"**PHQ-9 Score:** {rpt['phq9_total']}/27 | **GAD-7 Score:** {rpt['gad7_total']}/21")
                        st.markdown(f"**Doctor Feedback:** {rpt['psychologist_notes']}")

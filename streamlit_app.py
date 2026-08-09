"""
streamlit_app.py
EduHelp AI — Streamlit version.

Deploy on Streamlit Community Cloud:
  1. Push this repo to GitHub.
  2. On share.streamlit.io, create a new app, set "Main file path" to
     streamlit_app.py.
  3. In App settings -> Secrets, add OPENROUTER_API_KEY and the [auth]
     Google OAuth settings — see .streamlit/secrets.toml.example for the
     exact format and README.md for the full Google Cloud Console setup.
  4. Deploy.
"""

import os
import uuid

import streamlit as st

from utils.extract import full_text
import rag
import summary as summary_mod
import quiz as quiz_mod
import planner as planner_mod

st.set_page_config(
    page_title="EduHelp AI",
    page_icon="static/images/logo.png",
    layout="wide",
)

UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "docx", "ppt", "pptx", "txt"}
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------- Shared brand theme (mirrors static/css/style.css in the Flask app) ----------

THEMES = {
    "dark": {"paper": "#12131C", "ink": "#E8E9F3", "ink_soft": "#9A9DB5",
             "line": "#2A2C3D", "card": "#191B27"},
    "light": {"paper": "#EDEEF3", "ink": "#1B1E2B", "ink_soft": "#4A4D5E",
              "line": "#D6D8E2", "card": "#FFFFFF"},
}
ACCENTS = {
    "amber": "#F2A93B", "violet": "#5B6EF5", "coral": "#F2545B",
    "teal": "#14B8A6", "sky": "#3B9DF8",
}
# Same per-page accent mapping as templates/*.html {% block accent %} in Flask.
PAGE_ACCENT = {
    "Upload & Summary": "amber",
    "Chat with Notes": "violet",
    "Quiz Mode": "coral",
    "Flashcards": "teal",
    "Study Planner": "sky",
    "Dashboard": "amber",
}


def inject_theme(theme_name, accent_name):
    t = THEMES[theme_name]
    accent = ACCENTS[accent_name]
    on_accent = "#1B1E2B" if theme_name == "dark" else "#FFFFFF"
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"], .stMarkdown, p, span, label {{
        font-family: 'Inter', system-ui, sans-serif;
    }}
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
        font-family: 'Fraunces', serif !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em;
        color: {t['ink']} !important;
    }}

    /* ---- App shell ---- */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
        background-color: {t['paper']} !important;
        color: {t['ink']} !important;
    }}
    [data-testid="stHeader"] {{ background-color: transparent !important; }}
    .stMarkdown, .stMarkdown p, .stCaption, [data-testid="stCaptionContainer"] {{
        color: {t['ink_soft']} !important;
    }}

    /* ---- Sidebar ---- */
    section[data-testid="stSidebar"] {{
        background-color: {t['card']} !important;
        border-right: 1px solid {t['line']};
    }}
    section[data-testid="stSidebar"] * {{ color: {t['ink']} !important; }}
    section[data-testid="stSidebar"] .stCaption, section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{
        color: {t['ink_soft']} !important;
    }}

    /* ---- Sidebar nav radio: hide the bullet dot, style like a clean list ---- */
    section[data-testid="stSidebar"] [role="radiogroup"] label {{
        padding: 8px 10px;
        border-radius: 10px;
        margin-bottom: 2px;
    }}
    section[data-testid="stSidebar"] [role="radiogroup"] label:hover {{
        background-color: {accent}22;
    }}
    section[data-testid="stSidebar"] [role="radiogroup"] label[data-checked="true"],
    section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{
        background-color: {accent}33;
        font-weight: 600;
    }}

    /* ---- Buttons ---- */
    .stButton>button {{
        border-radius: 999px !important;
        border: 1px solid {t['line']} !important;
        color: {t['ink']} !important;
        background-color: {t['card']} !important;
        font-family: 'Inter', sans-serif !important;
    }}
    .stButton>button:hover {{ border-color: {accent} !important; color: {accent} !important; }}
    .stButton>button[kind="primary"] {{
        background-color: {accent} !important;
        border-color: {accent} !important;
        color: {on_accent} !important;
        font-weight: 600 !important;
    }}
    .stButton>button[kind="primary"]:hover {{ opacity: 0.9; color: {on_accent} !important; }}
    [data-testid="stMetricValue"] {{ color: {accent} !important; }}
    [data-testid="stMetricLabel"] {{ color: {t['ink_soft']} !important; }}
    a {{ color: {accent} !important; }}

    /* ---- Inputs ---- */
    .stTextInput input, .stNumberInput input, .stDateInput input,
    [data-testid="stChatInput"] textarea, .stTextArea textarea {{
        border-radius: 10px !important;
        border: 1px solid {t['line']} !important;
        background-color: {t['card']} !important;
        color: {t['ink']} !important;
    }}
    .stSelectbox > div > div, [data-baseweb="select"] > div {{
        border-radius: 10px !important;
        border: 1px solid {t['line']} !important;
        background-color: {t['card']} !important;
        color: {t['ink']} !important;
    }}
    [data-baseweb="popover"] li {{ background-color: {t['card']} !important; color: {t['ink']} !important; }}

    /* ---- File uploader ---- */
    [data-testid="stFileUploaderDropzone"] {{
        border-radius: 12px !important;
        border: 1.5px dashed {t['line']} !important;
        background-color: {t['card']} !important;
    }}
    [data-testid="stFileUploaderDropzone"] * {{ color: {t['ink']} !important; }}
    [data-testid="stFileUploaderDropzone"] button {{
        background-color: {accent} !important;
        color: {on_accent} !important;
        border: none !important;
        border-radius: 999px !important;
    }}
    [data-testid="stFileUploaderFile"] {{
        background-color: {t['card']} !important;
        color: {t['ink']} !important;
        border-radius: 8px !important;
    }}

    /* ---- Expander (used for flashcards / fill-blank answers) ---- */
    div[data-testid="stExpander"] {{
        border: 1px solid {t['line']} !important;
        border-radius: 14px !important;
        background: {t['card']} !important;
    }}
    div[data-testid="stExpander"] summary {{ color: {t['ink']} !important; }}

    /* ---- Alerts (info / success / warning / error) ---- */
    [data-testid="stAlert"] {{
        border-radius: 12px !important;
        background-color: {accent}1A !important;
        color: {t['ink']} !important;
        border: 1px solid {accent}55 !important;
    }}
    [data-testid="stAlert"] p {{ color: {t['ink']} !important; }}

    /* ---- Chat bubbles ---- */
    [data-testid="stChatMessage"] {{
        background-color: {t['card']} !important;
        border: 1px solid {t['line']} !important;
        border-radius: 14px !important;
    }}

    /* ---- Radio (quiz answers, style choice etc.) ---- */
    div[role="radiogroup"] label p {{ color: {t['ink']} !important; }}

    hr, [data-testid="stDivider"] {{ border-color: {t['line']} !important; }}

    .doc-row {{
        display: flex; align-items: center; justify-content: space-between;
        padding: 8px 14px; border: 1px solid {t['line']}; border-radius: 999px;
        background: {t['card']}; margin-bottom: 8px; font-size: 0.9rem;
    }}
    </style>
    """, unsafe_allow_html=True)


if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# ---------- Gmail sign-in (required) ----------
# Uses Streamlit's built-in OpenID Connect auth (st.login/st.user), configured
# via the [auth] section in .streamlit/secrets.toml (see secrets.toml.example).

if not st.user.is_logged_in:
    inject_theme(st.session_state.theme, "amber")
    t = THEMES[st.session_state.theme]
    st.markdown(f"""
    <style>
    .stApp {{
        background: radial-gradient(circle at 15% 20%, #F2A93B33, transparent 45%),
                    radial-gradient(circle at 85% 15%, #5B6EF533, transparent 45%),
                    radial-gradient(circle at 50% 85%, #3B9DF833, transparent 50%),
                    {t['paper']} !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    st.write("")
    st.write("")
    left, mid, right = st.columns([1, 1.3, 1])
    with mid:
        c1, c2, c3 = st.columns([1, 1, 1])
        with c2:
            st.image("static/images/logo.png", width=110)
        st.markdown(
            f"<h1 style='text-align:center; font-size:2.4rem; margin-top:14px;'>"
            f"Your notes, <span style='color:{ACCENTS['coral']}'>wide</span> "
            f"<span style='color:{ACCENTS['violet']}'>awake</span>.</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align:center; opacity:0.75;'>Sign in with your Gmail "
            "account to summarize, chat with, and quiz yourself on your notes.</p>",
            unsafe_allow_html=True,
        )
        st.write("")
        b1, b2, b3 = st.columns([1, 1.2, 1])
        with b2:
            try:
                if st.button("Sign in with Google", type="primary", use_container_width=True):
                    st.login()
            except Exception:
                st.error(
                    "Google sign-in is not configured yet. Add the [auth] section "
                    "to your .streamlit/secrets.toml — see secrets.toml.example "
                    "and README.md for setup steps."
                )
    st.stop()

if "docs" not in st.session_state:
    st.session_state.docs = {}  # doc_id -> {"filepath":.., "filename":..}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}  # doc_id -> list of (role, text, pages)


def save_uploaded_file(uploaded_file):
    ext = uploaded_file.name.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return None, "Unsupported file type."
    doc_id = uuid.uuid4().hex[:10]
    filepath = os.path.join(UPLOAD_DIR, f"{doc_id}_{uploaded_file.name}")
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return doc_id, filepath


def delete_document(doc_id):
    """Remove an uploaded document: its file, FAISS index, and session entry."""
    doc = st.session_state.docs.get(doc_id)
    if not doc:
        return
    filepath = doc["filepath"]
    if os.path.exists(filepath):
        os.remove(filepath)
    rag.delete_index(doc_id)
    st.session_state.docs.pop(doc_id, None)
    st.session_state.chat_history.pop(doc_id, None)


def render_doc_list():
    """Render the uploaded-documents list with a small remove (✕) button each."""
    if not st.session_state.docs:
        st.markdown(":gray[No documents uploaded yet.]")
        return
    for doc_id, d in list(st.session_state.docs.items()):
        c1, c2 = st.columns([10, 1])
        c1.markdown(f"📄 {d['filename']}")
        if c2.button("🗑️", key=f"remove_{doc_id}", help="Remove document"):
            delete_document(doc_id)
            st.rerun()


def doc_picker(label="Document", key="doc"):
    if not st.session_state.docs:
        st.info("Upload a document on the **Upload & Summary** page first.")
        return None
    options = {f"{d['filename']}": doc_id for doc_id, d in st.session_state.docs.items()}
    choice = st.selectbox(label, list(options.keys()), key=key)
    return options[choice]


# ---------- Sidebar navigation ----------
st.sidebar.image("static/images/logo.png", width=40)
st.sidebar.title("EduHelp AI")
page = st.sidebar.radio(
    "Navigate",
    ["Upload & Summary", "Chat with Notes", "Quiz Mode", "Flashcards",
     "Study Planner", "Dashboard"],
)
st.sidebar.divider()
st.sidebar.caption("Upload PDF, DOCX, PPTX, or TXT notes, then summarize, "
                    "chat, quiz, and plan your study time — all powered by OpenRouter.")

st.sidebar.divider()
if st.sidebar.button(
    "☀️ Day mode" if st.session_state.theme == "dark" else "🌙 Night mode",
    use_container_width=True,
):
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
    st.rerun()

st.sidebar.divider()
user_col1, user_col2 = st.sidebar.columns([1, 3])
if getattr(st.user, "picture", None):
    user_col1.image(st.user.picture, width=32)
user_col2.markdown(f"**{st.user.name}**")
if st.sidebar.button("Sign out", use_container_width=True):
    st.logout()

# Apply theme + this page's accent color (matches Flask's per-page accent blocks)
inject_theme(st.session_state.theme, PAGE_ACCENT.get(page, "amber"))

# ---------- Page: Upload & Summary ----------
if page == "Upload & Summary":
    st.header("Upload your notes")
    with st.container(border=True):
        uploaded_file = st.file_uploader(
            "Choose a file", type=["pdf", "docx", "ppt", "pptx", "txt"]
        )
        if uploaded_file is not None:
            already_indexed = any(
                d["filename"] == uploaded_file.name for d in st.session_state.docs.values()
            )
            if already_indexed:
                st.info(f"'{uploaded_file.name}' is already indexed. Remove it below first if you want to re-process it.")
            elif st.button("Process file", type="primary"):
                with st.spinner("Extracting and indexing document..."):
                    doc_id, filepath = save_uploaded_file(uploaded_file)
                    if doc_id is None:
                        st.error(filepath)
                    else:
                        try:
                            num_chunks = rag.build_index(filepath, doc_id)
                            st.session_state.docs[doc_id] = {
                                "filepath": filepath, "filename": uploaded_file.name
                            }
                            st.success(f"Indexed '{uploaded_file.name}' ({num_chunks} chunks).")
                        except Exception as e:
                            st.error(f"Failed to process file: {e}")

    if st.session_state.docs:
        st.subheader("Your documents")
        with st.container(border=True):
            render_doc_list()

    st.write("")
    st.header("Summarize")
    with st.container(border=True):
        doc_id = doc_picker(key="summary_doc")
        if doc_id:
            style = st.radio(
                "Style", ["100_words", "300_words", "bullet_points"],
                format_func=lambda s: {"100_words": "100 words", "300_words": "300 words",
                                        "bullet_points": "Bullet points"}[s],
                horizontal=True,
            )
            if st.button("Generate summary"):
                with st.spinner("Summarizing..."):
                    text = full_text(st.session_state.docs[doc_id]["filepath"])
                    try:
                        result = summary_mod.summarize(text, style=style)
                        st.session_state["last_summary"] = result
                        st.session_state["last_summary_doc"] = doc_id
                    except Exception as e:
                        st.error(str(e))

        if st.session_state.get("last_summary") and st.session_state.get("last_summary_doc") == doc_id:
            st.write(st.session_state["last_summary"])
            if st.button("Export as PDF"):
                filepath = summary_mod.export_summary_pdf(
                    st.session_state["last_summary"],
                    title=f"Summary - {st.session_state.docs[doc_id]['filename']}",
                    doc_id=doc_id,
                )
                with open(filepath, "rb") as f:
                    st.download_button("Download summary.pdf", f, file_name="summary.pdf")

# ---------- Page: Chat with Notes ----------
elif page == "Chat with Notes":
    st.header("Chat with your notes")
    doc_id = doc_picker(key="chat_doc")
    if doc_id:
        st.session_state.chat_history.setdefault(doc_id, [])
        for role, text, pages in st.session_state.chat_history[doc_id]:
            with st.chat_message(role):
                st.write(text)
                if pages:
                    st.caption(f"Source page(s): {', '.join(map(str, pages))}")

        question = st.chat_input("e.g. Explain Binary Tree")
        if question:
            st.session_state.chat_history[doc_id].append(("user", question, None))
            with st.chat_message("user"):
                st.write(question)
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        result = rag.ask(question, doc_id)
                        st.write(result["answer"])
                        if result["source_pages"]:
                            st.caption(f"Source page(s): {', '.join(map(str, result['source_pages']))}")
                        st.session_state.chat_history[doc_id].append(
                            ("assistant", result["answer"], result["source_pages"])
                        )
                    except Exception as e:
                        st.error(str(e))

# ---------- Page: Quiz Mode ----------
elif page == "Quiz Mode":
    st.header("Quiz mode")
    doc_id = doc_picker(key="quiz_doc")
    if doc_id:
        col1, col2 = st.columns(2)
        quiz_type = col1.selectbox("Type", ["Multiple Choice", "True / False", "Fill in the Blanks"])
        count = col2.number_input("Number of questions", min_value=1, max_value=20, value=5)

        if st.button("Generate quiz"):
            text = full_text(st.session_state.docs[doc_id]["filepath"])
            with st.spinner("Generating..."):
                try:
                    if quiz_type == "Multiple Choice":
                        st.session_state["quiz_items"] = quiz_mod.generate_mcqs(text, count)
                    elif quiz_type == "True / False":
                        st.session_state["quiz_items"] = quiz_mod.generate_true_false(text, count)
                    else:
                        st.session_state["quiz_items"] = quiz_mod.generate_fill_blanks(text, count)
                    st.session_state["quiz_type"] = quiz_type
                except Exception as e:
                    st.error(str(e))

        items = st.session_state.get("quiz_items")
        if items and st.session_state.get("quiz_type") == quiz_type:
            for i, item in enumerate(items, start=1):
                st.divider()
                if quiz_type == "Multiple Choice":
                    st.markdown(f"**{i}. {item['question']}**")
                    ans = st.radio("Choose one", item["options"], key=f"mcq_{i}", index=None)
                    if ans:
                        if ans.startswith(item["answer"]) or ans == item["answer"]:
                            st.success(f"Correct! {item.get('explanation', '')}")
                        else:
                            st.error(f"Not quite. Correct answer: {item['answer']}. {item.get('explanation', '')}")
                elif quiz_type == "True / False":
                    st.markdown(f"**{i}. {item['statement']}**")
                    ans = st.radio("Your answer", ["True", "False"], key=f"tf_{i}", index=None)
                    if ans:
                        correct = (ans == "True") == item["answer"]
                        if correct:
                            st.success(f"Correct! {item.get('explanation', '')}")
                        else:
                            st.error(f"Not quite. Correct answer: {item['answer']}. {item.get('explanation', '')}")
                else:
                    st.markdown(f"**{i}. {item['question']}**")
                    with st.expander("Reveal answer"):
                        st.write(item["answer"])

# ---------- Page: Flashcards ----------
elif page == "Flashcards":
    st.header("Flashcards")
    doc_id = doc_picker(key="fc_doc")
    if doc_id:
        count = st.number_input("Number of cards", min_value=1, max_value=30, value=10)
        if st.button("Generate flashcards"):
            text = full_text(st.session_state.docs[doc_id]["filepath"])
            with st.spinner("Generating..."):
                try:
                    st.session_state["flashcards"] = quiz_mod.generate_flashcards(text, count)
                except Exception as e:
                    st.error(str(e))

        cards = st.session_state.get("flashcards")
        if cards:
            cols = st.columns(2)
            for i, card in enumerate(cards):
                with cols[i % 2]:
                    with st.expander(f"Q: {card['question']}"):
                        st.write(card["answer"])

# ---------- Page: Study Planner ----------
elif page == "Study Planner":
    st.header("Study planner")
    exam_date = st.date_input("Exam date")
    hours_per_day = st.number_input("Available hours per day", min_value=1.0, max_value=16.0, value=4.0, step=0.5)

    st.subheader("Subjects")
    if "subjects" not in st.session_state:
        st.session_state.subjects = [{"name": "DSA", "priority": 3},
                                      {"name": "AI", "priority": 2},
                                      {"name": "Java", "priority": 2}]

    for i, subj in enumerate(st.session_state.subjects):
        c1, c2, c3 = st.columns([3, 1, 1])
        subj["name"] = c1.text_input("Subject", value=subj["name"], key=f"subj_name_{i}")
        subj["priority"] = c2.number_input("Priority", min_value=1, max_value=5, value=subj["priority"], key=f"subj_pri_{i}")
        if c3.button("Remove", key=f"subj_rm_{i}"):
            st.session_state.subjects.pop(i)
            st.rerun()

    if st.button("+ Add subject"):
        st.session_state.subjects.append({"name": "", "priority": 3})
        st.rerun()

    if st.button("Generate plan", type="primary"):
        subjects = [s for s in st.session_state.subjects if s["name"].strip()]
        if not subjects:
            st.warning("Add at least one subject.")
        else:
            try:
                plan = planner_mod.build_plan(exam_date.isoformat(), subjects, hours_per_day)
                st.session_state["plan"] = plan
            except Exception as e:
                st.error(str(e))

    if st.session_state.get("plan"):
        for day in st.session_state["plan"]:
            st.markdown(f"**Day {day['day']} · {day['date']}**")
            for s in day["sessions"]:
                st.markdown(f"- {s['subject']}: {s['hours']} hr")

# ---------- Page: Dashboard ----------
elif page == "Dashboard":
    st.header("Dashboard")
    st.metric("Documents uploaded", len(st.session_state.docs))
    if st.session_state.docs:
        st.subheader("Your documents")
        render_doc_list()
    else:
        st.info("No documents yet — head to Upload & Summary to add one.")
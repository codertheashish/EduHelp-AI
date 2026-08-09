# 🚀 EduHelp AI

Upload notes → summarize, chat, quiz, flashcard, and plan your study time — all powered by OpenRouter (any model — GPT, Claude, Gemini, Llama, etc.).

## Features

Both the **Streamlit app** (`streamlit_app.py`, the main deploy target) and
the **Flask app** (`flask_app.py`, an alternate custom-HTML frontend) have
full feature parity:

- **Gmail sign-in required** (Google OAuth) — every page is behind login
- Upload PDF, DOCX, PPTX, TXT notes
- Remove an uploaded document any time (✕ button next to it)
- AI summary (100 words / 300 words / bullet points), exportable as PDF
- Chat with notes (RAG over FAISS, with source page citations)
- MCQ / True-False / Fill-in-the-blank quiz generation
- Flashcard generation
- Study planner (exam date + subjects + daily hours → day-by-day timetable)
- Dashboard overview

## Set up Google sign-in (required)

Both apps require visitors to sign in with Gmail before using any feature,
but each uses a different mechanism:

- **Flask** (`flask_app.py`) uses `authlib` with its own `/login`,
  `/auth/google`, `/auth/callback` routes.
- **Streamlit** (`streamlit_app.py`) uses Streamlit's built-in OpenID
  Connect auth (`st.login()` / `st.user`), configured entirely through
  `.streamlit/secrets.toml`.

You can reuse the **same** Google OAuth Client for both — you just need to
register **both** redirect URIs on it.

1. Go to https://console.cloud.google.com/apis/credentials
2. Create a project (or pick an existing one).
3. Click **Create Credentials → OAuth client ID**.
   - Application type: **Web application**
   - Authorized redirect URIs — add all of these that apply to you:
     - `http://127.0.0.1:5000/auth/callback` (Flask, local)
     - `http://localhost:8501/oauth2callback` (Streamlit, local)
     - `https://your-app-name.streamlit.app/oauth2callback` (Streamlit, once deployed on Streamlit Cloud)
     - your Flask production domain + `/auth/callback`, once deployed
4. Copy the generated **Client ID** and **Client Secret**.

**For Flask**, paste them into your `.env` file:
```
GOOGLE_CLIENT_ID="your_client_id_here"
GOOGLE_CLIENT_SECRET="your_client_secret_here"
```
Restart `flask_app.py`. Visiting any page now redirects to `/login`.

**For Streamlit**, paste them into `.streamlit/secrets.toml` (local) or
into **App settings → Secrets** on Streamlit Community Cloud (deployed) —
see `.streamlit/secrets.toml.example` for the exact format:
```toml
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"   # or your deployed URL + /oauth2callback
cookie_secret = "a-long-random-string"                  # generate your own
client_id = "your_google_client_id_here"
client_secret = "your_google_client_secret_here"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```
Restart (or redeploy) the app. You'll now see a "Sign in with Google"
screen before any page loads.

## Deploy on Streamlit Community Cloud (easiest, free)

1. Push this repo to GitHub.
2. Go to https://share.streamlit.io -> **New app**.
3. Pick your repo/branch, set **Main file path** to `streamlit_app.py`.
4. Under **Advanced settings -> Secrets**, paste your full secrets — copy
   the format from `.streamlit/secrets.toml.example`, filling in your real
   `OPENROUTER_API_KEY` and the `[auth]` Google OAuth values (see above).
   Set `redirect_uri` to `https://<your-app-name>.streamlit.app/oauth2callback`.
5. Click **Deploy**. Done — no server, no Procfile needed.
6. Go back to Google Cloud Console and add that same
   `https://<your-app-name>.streamlit.app/oauth2callback` URL to your
   OAuth client's Authorized redirect URIs (step 3 above) — Google will
   reject the login otherwise.

Get an OpenRouter API key at https://openrouter.ai/keys.

## Run locally (Streamlit)

```bash
cd EduHelp-AI
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # fill in OPENROUTER_API_KEY + [auth] Google values
streamlit run streamlit_app.py
```

## Run locally (Flask version)

A Flask version also ships in this repo (`flask_app.py` + `templates/` + `static/`)
for reference / if you later want a custom HTML frontend instead.

```bash
pip install flask python-dotenv
cp .env.example .env       # add your OPENROUTER_API_KEY
python flask_app.py
```
Flask does **not** deploy on Streamlit Cloud — use Render/Railway for that version.

## Project structure

```
EduHelp-AI/
├── streamlit_app.py       # ⭐ main entry point for Streamlit Cloud
├── flask_app.py           # alternate Flask version (deploy on Render/Railway instead)
├── .streamlit/
│   ├── config.toml         # theme
│   └── secrets.toml.example
├── static/{css,js,images}/ # used only by the Flask version
├── templates/               # used only by the Flask version
├── uploads/                 # raw uploaded files
├── summaries/                # exported summary PDFs + FAISS indexes
├── utils/
│   ├── extract.py            # PDF/DOCX/PPTX/TXT text extraction
│   └── openrouter_client.py  # OpenRouter API wrapper (reads key from env or st.secrets)
├── rag.py                     # FAISS + sentence-transformers RAG pipeline
├── summary.py                  # summary generation + PDF export
├── quiz.py                      # MCQ / T-F / fill-blank / flashcard / answer generation
├── planner.py                    # study timetable builder
└── requirements.txt
```

## How the pieces fit together

1. **Upload** (`/api/upload`) — file is saved to `uploads/`, text is extracted
   page-by-page (`utils/extract.py`), chunked, embedded with
   `sentence-transformers` (local, free), and stored in a FAISS index per document.
2. **Summary** (`/api/summary`) — pulls the full document text and asks the OpenRouter model
   for a summary at the chosen length/style. Export to PDF via `reportlab`.
3. **Chat / RAG** (`/api/chat`) — embeds the question, retrieves the closest
   chunks from FAISS, and asks the OpenRouter model to answer using only that context —
   returning the source page numbers alongside the answer.
4. **Quiz / Flashcards / Answers** — prompts the model to return strict JSON,
   which the frontend renders as interactive UI.
5. **Planner** (`/api/planner`) — pure Python, no AI call: splits hours across
   subjects by priority weight, one row per day until the exam date.

## Notes for scaling this up
- Swap the in-memory `DOCS` dict / `st.session_state.docs` for a real database (SQLite/Postgres) — see `TEAM.md`, this is Ravi's task.
- Move FAISS indexes to a persistent vector DB (Pinecone/Weaviate) if you expect
  many concurrent users.
- Consider streaming model responses for the chat page for a snappier feel.

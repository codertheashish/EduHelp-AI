# 🚀 EduHelp AI

Upload notes → summarize, chat, quiz, flashcard, and plan your study time — all powered by OpenRouter (any model — GPT, Claude, Gemini, Llama, etc.).

## Features

- **Gmail sign-in required** (Google OAuth) — every page is behind login
- Upload PDF, DOCX, PPTX, TXT notes
- Remove an uploaded document any time (✕ button next to it)
- AI summary (100 words / 300 words / bullet points), exportable as PDF
- Chat with notes (RAG over FAISS, with source page citations)
- MCQ / True-False / Fill-in-the-blank / Short Answer / Long Answer quiz generation
- Flashcard generation
- Study planner (exam date + subjects + daily hours → day-by-day timetable)
- Dashboard overview

## Set up Google sign-in (required)

Every page redirects to `/login` until you sign in with Google. Flask
(`flask_app.py`) uses `authlib` with its own `/login`, `/auth/google`,
`/auth/callback` routes.

1. Go to https://console.cloud.google.com/apis/credentials
2. Create a project (or pick an existing one).
3. Click **Create Credentials → OAuth client ID**.
   - Application type: **Web application**
   - Authorized redirect URI: `http://127.0.0.1:5000/auth/callback`
4. Copy the generated **Client ID** and **Client Secret** into your `.env`:
```
GOOGLE_CLIENT_ID="your_client_id_here"
GOOGLE_CLIENT_SECRET="your_client_secret_here"
```
5. Restart `flask_app.py`. Visiting any page now redirects to `/login`.

Get an OpenRouter API key at https://openrouter.ai/keys.

## Run locally

```bash
cd "EduHelp AI"
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # add OPENROUTER_API_KEY, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
python flask_app.py
```

Open in your browser: **http://127.0.0.1:5000**

See `RUN_ME.md` for the short version of these steps.

## Project structure

```
EduHelp AI/
├── flask_app.py           # main entry point
├── static/{css,js,images}/
├── templates/
├── uploads/                 # raw uploaded files
├── summaries/                # exported summary PDFs + FAISS indexes
├── utils/
│   ├── extract.py            # PDF/DOCX/PPTX/TXT text extraction
│   └── openrouter_client.py  # OpenRouter API wrapper
├── rag.py                     # FAISS + sentence-transformers RAG pipeline
├── summary.py                  # summary generation + PDF export
├── quiz.py                      # MCQ / T-F / fill-blank / short/long answer / flashcard generation
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
- Swap the in-memory `DOCS` dict for a real database (SQLite/Postgres) — see `TEAM.md`, this is Ravi's task.
- Move FAISS indexes to a persistent vector DB (Pinecone/Weaviate) if you expect
  many concurrent users.
- Consider streaming model responses for the chat page for a snappier feel.

# EduHelp AI — Team & Branch Guide

This file maps each team member to their Git branch and the parts of the
codebase they own. Please only work on your branch, and only touch the
files listed under your role (cross-cutting changes go through the
Project Manager).

| Name    | Role                          | Branch           |
|---------|-------------------------------|-------------------|
| Ashish  | Project Manager               | `master` (merges everything) |
| Sonali  | Frontend Developer            | `frontend`        |
| Swayam  | Backend Developer              | `backend`         |
| Arpita  | AI Modules Developer          | `ai-modules`      |
| Ravi    | Database & Quiz Developer     | `database-quiz`   |
| Nirbhay | Testing & Documentation       | `testing-docs`    |

---

## Sonali — Frontend Developer (`frontend` branch)

Everything the user sees and clicks.

- `templates/` — all `.html` pages (`base.html`, `landing.html`, `login.html`,
  `index.html`, `chat.html`, `quiz.html`, `flashcards.html`, `planner.html`,
  `dashboard.html`)
- `static/css/` — styling (`style.css`, `landing.css`)
- `static/js/` — client-side behaviour (`main.js`)
- `static/images/` — logo and other assets

You call backend routes like `/api/summary`, `/api/chat`, `/api/quiz/mcq`,
etc. via `fetch()` — see `apiPost`, `apiUpload`, `apiDelete` in
`static/js/main.js` for the pattern already used. Don't rename these routes;
coordinate with Swayam (backend) if you need a new one.

## Swayam — Backend Developer (`backend` branch)

The Flask server: routing, auth, request/response handling.

- `flask_app.py` — all `@app.route(...)` endpoints, Google OAuth login
  (`/login`, `/auth/google`, `/auth/callback`, `/logout`), the
  `login_required` decorator, file upload handling
- `utils/extract.py` — text extraction from PDF/DOCX/PPTX/TXT

Keep route names and JSON response shapes stable — frontend, AI modules, and
quiz code all depend on them. If you must change a response shape, flag it
in the team channel first.

## Arpita — AI Modules Developer (`ai-modules` branch)

Everything that talks to the LLM.

- `utils/openrouter_client.py` — the OpenRouter API wrapper (`generate()`).
  This is the single place every AI call goes through — model choice,
  `max_tokens`, `temperature` all live here.
- `rag.py` — chunking, embeddings, FAISS index build/search, `ask()` for
  the "Chat with Notes" feature
- `summary.py` — summary generation + PDF export

Prompts, prompt formatting, and any RAG improvements (better chunking,
re-ranking, etc.) belong here.

## Ravi — Database & Quiz Developer (`database-quiz` branch)

Data persistence and the quiz/flashcard/planner logic.

- `quiz.py` — MCQ / True-False / Fill-in-the-blank / flashcard / short &
  long answer generation
- `planner.py` — study planner logic (exam date + subjects + hours →
  timetable)
- **Database migration**: the app currently stores documents in an
  in-memory Python dict (`DOCS` in `flask_app.py`) — this resets every time
  the server restarts. Your main task is replacing this with a real
  database (SQLite is a good starting point; use SQLAlchemy if you want an
  ORM) so documents, quiz results, and user history persist. Coordinate the
  `DOCS`-shaped interface with Swayam before changing it, since
  `flask_app.py`, `rag.py`, and `summary.py` all read from it.

## Nirbhay — Testing & Documentation (`testing-docs` branch)

Quality and clarity.

- `README.md`, `RUN_ME.md` — setup instructions, keep them in sync with
  whatever the other branches ship
- `tests/` — add this folder; write tests for `flask_app.py` routes
  (use Flask's `test_client()`, see the pattern used during development —
  fake a logged-in session with `client.session_transaction()`), and unit
  tests for `quiz.py` / `planner.py` / `rag.py` where they don't require a
  live OpenRouter key (mock `utils.openrouter_client.generate`)
- Also responsible for keeping `.env.example` accurate whenever a new
  environment variable is introduced by any branch

---

## Git workflow

1. Clone the repo, then check out your branch:
   ```bash
   git clone <repo-url>
   cd EduHelp-AI
   git checkout <your-branch-name>
   ```
2. Commit and push regularly to your own branch — never push directly to
   `master`.
3. When a feature is ready, open a Pull Request into `master`. Ashish
   (PM) reviews and merges.
4. Before starting new work, pull the latest `master` into your branch to
   stay in sync:
   ```bash
   git checkout master
   git pull origin master
   git checkout <your-branch-name>
   git merge master
   ```

## Shared setup (everyone needs this once)

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env            
# Fill in OPENROUTER_API_KEY, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
python flask_app.py
```

See `README.md` and `RUN_ME.md` for full details.

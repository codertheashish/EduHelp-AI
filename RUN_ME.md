# EduHelp AI

## How to run (Flask version)

```bash
cd "EduHelp AI"
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # open .env and paste your OPENROUTER_API_KEY
                                # and your GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET
python flask_app.py
```

Open in your browser: **http://127.0.0.1:5000**

Get an OpenRouter API key here: https://openrouter.ai/keys

**Gmail sign-in is required.** Every page redirects to `/login` until you
sign in with Google. To enable it, create OAuth credentials at
https://console.cloud.google.com/apis/credentials (Web application, redirect
URI `http://127.0.0.1:5000/auth/callback`) and put them in `.env` — see
README.md for the full walkthrough.

The AI-based features (summary, chat, quiz generation) only work once a
valid `OPENROUTER_API_KEY` is also set in `.env`.

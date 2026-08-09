"""
app.py
Main Flask application for EduHelp AI.
"""

import os
import uuid
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from werkzeug.utils import secure_filename
from authlib.integrations.flask_client import OAuth

from utils.extract import full_text
import rag
import summary as summary_mod
import quiz as quiz_mod
import planner as planner_mod

load_dotenv()

# Google's OAuth token exchange requires HTTPS by default. Allow plain HTTP
# only for local development (127.0.0.1 / localhost). Do NOT set this in
# production — deploy behind HTTPS instead.
if os.environ.get("FLASK_ENV") == "development":
    os.environ.setdefault("AUTHLIB_INSECURE_TRANSPORT", "1")

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "docx", "ppt", "pptx", "txt"}
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory map of doc_id -> {filepath, filename}. Swap for a real DB later.
DOCS = {}

# ---------- Google OAuth (Gmail sign-in) ----------

oauth = OAuth(app)
google_oauth = oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


def login_required(view_fn):
    """Redirect to the login page if there's no signed-in user in session."""
    @wraps(view_fn)
    def wrapped(*args, **kwargs):
        if not session.get("user"):
            return redirect(url_for("login", next=request.path))
        return view_fn(*args, **kwargs)
    return wrapped


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------- Auth routes ----------

@app.route("/login")
def login():
    if session.get("user"):
        return redirect(url_for("index"))
    if not os.environ.get("GOOGLE_CLIENT_ID"):
        return (
            "Google sign-in is not configured yet. Set GOOGLE_CLIENT_ID and "
            "GOOGLE_CLIENT_SECRET in your .env file (see README.md for setup steps).",
            500,
        )
    return render_template("login.html")


@app.route("/auth/google")
def auth_google():
    redirect_uri = url_for("auth_callback", _external=True)
    return google_oauth.authorize_redirect(redirect_uri)


@app.route("/auth/callback")
def auth_callback():
    token = google_oauth.authorize_access_token()
    user_info = token.get("userinfo")
    if not user_info:
        return redirect(url_for("login"))

    session["user"] = {
        "email": user_info.get("email"),
        "name": user_info.get("name") or user_info.get("email"),
        "picture": user_info.get("picture"),
    }

    next_path = request.args.get("next") or url_for("index")
    return redirect(next_path)


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("landing"))


# ---------- Pages ----------

@app.route("/")
def landing():
    if session.get("user"):
        return redirect(url_for("index"))
    return render_template("landing.html")


@app.route("/app")
@login_required
def index():
    return render_template("index.html", docs=DOCS)


@app.route("/chat")
@login_required
def chat_page():
    return render_template("chat.html", docs=DOCS)


@app.route("/quiz")
@login_required
def quiz_page():
    return render_template("quiz.html", docs=DOCS)


@app.route("/planner")
@login_required
def planner_page():
    return render_template("planner.html")


@app.route("/flashcards")
@login_required
def flashcards_page():
    return render_template("flashcards.html", docs=DOCS)


@app.route("/dashboard")
@login_required
def dashboard_page():
    return render_template("dashboard.html", docs=DOCS)


# ---------- Upload ----------

@app.route("/api/upload", methods=["POST"])
@login_required
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "" or not allowed_file(file.filename):
        return jsonify({"error": "Unsupported or missing file"}), 400

    filename = secure_filename(file.filename)
    doc_id = uuid.uuid4().hex[:10]
    filepath = os.path.join(UPLOAD_DIR, f"{doc_id}_{filename}")
    file.save(filepath)

    DOCS[doc_id] = {"filepath": filepath, "filename": filename}

    try:
        num_chunks = rag.build_index(filepath, doc_id)
    except Exception as e:
        return jsonify({"error": f"Failed to index document: {e}"}), 500

    return jsonify({"doc_id": doc_id, "filename": filename, "chunks_indexed": num_chunks})


@app.route("/api/documents/<doc_id>", methods=["DELETE"])
@login_required
def delete_document(doc_id):
    doc = DOCS.get(doc_id)
    if not doc:
        return jsonify({"error": "Unknown doc_id"}), 404

    filepath = doc["filepath"]
    if os.path.exists(filepath):
        os.remove(filepath)

    rag.delete_index(doc_id)
    DOCS.pop(doc_id, None)

    return jsonify({"deleted": doc_id})


# ---------- Summary ----------

@app.route("/api/summary", methods=["POST"])
@login_required
def api_summary():
    data = request.get_json()
    doc_id = data.get("doc_id")
    style = data.get("style", "300_words")

    doc = DOCS.get(doc_id)
    if not doc:
        return jsonify({"error": "Unknown doc_id"}), 404

    try:
        text = full_text(doc["filepath"])
        result = summary_mod.summarize(text, style=style)
    except Exception as e:
        return jsonify({"error": f"Summary generation failed: {e}"}), 500
    return jsonify({"summary": result})


@app.route("/api/summary/export", methods=["POST"])
@login_required
def api_summary_export():
    data = request.get_json()
    doc_id = data.get("doc_id")
    summary_text = data.get("summary_text")

    doc = DOCS.get(doc_id)
    if not doc:
        return jsonify({"error": "Unknown doc_id"}), 404

    filepath = summary_mod.export_summary_pdf(
        summary_text, title=f"Summary - {doc['filename']}", doc_id=doc_id
    )
    return send_file(filepath, as_attachment=True)


# ---------- Chat / RAG ----------

@app.route("/api/chat", methods=["POST"])
@login_required
def api_chat():
    data = request.get_json()
    doc_id = data.get("doc_id")
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "Question is required"}), 400
    if doc_id not in DOCS:
        return jsonify({"error": "Unknown doc_id"}), 404

    try:
        result = rag.ask(question, doc_id)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify(result)


# ---------- Quiz / Flashcards / Answers ----------

@app.route("/api/quiz/mcq", methods=["POST"])
@login_required
def api_quiz_mcq():
    return _quiz_response(quiz_mod.generate_mcqs)


@app.route("/api/quiz/true-false", methods=["POST"])
@login_required
def api_quiz_tf():
    return _quiz_response(quiz_mod.generate_true_false)


@app.route("/api/quiz/fill-blanks", methods=["POST"])
@login_required
def api_quiz_fill():
    return _quiz_response(quiz_mod.generate_fill_blanks)


@app.route("/api/flashcards", methods=["POST"])
@login_required
def api_flashcards():
    return _quiz_response(quiz_mod.generate_flashcards)


@app.route("/api/answers/short", methods=["POST"])
@login_required
def api_short_answers():
    return _quiz_response(quiz_mod.generate_short_answers)


@app.route("/api/answers/long", methods=["POST"])
@login_required
def api_long_answers():
    return _quiz_response(quiz_mod.generate_long_answers)


def _quiz_response(generator_fn):
    data = request.get_json()
    doc_id = data.get("doc_id")
    count = data.get("count", 5)

    doc = DOCS.get(doc_id)
    if not doc:
        return jsonify({"error": "Unknown doc_id"}), 404

    text = full_text(doc["filepath"])
    try:
        items = generator_fn(text, count)
    except Exception as e:
        return jsonify({"error": f"Generation failed: {e}"}), 500

    return jsonify({"items": items})


# ---------- Study Planner ----------

@app.route("/api/planner", methods=["POST"])
@login_required
def api_planner():
    data = request.get_json()
    try:
        plan = planner_mod.build_plan(
            exam_date_str=data["exam_date"],
            subjects=data["subjects"],
            hours_per_day=float(data["hours_per_day"]),
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"plan": plan})


if __name__ == "__main__":
    app.run(debug=True)

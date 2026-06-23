import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from utils.resume_parser import extract_text, ParseError
from utils.ats_score import calculate_ats_score
from utils.keyword_matcher import match_keywords

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {"pdf", "docx"}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'app.db')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

db = SQLAlchemy(app)


# ---------------------------------------------------------------- models --

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    analyses = db.relationship("Analysis", backref="user", lazy=True,
                                cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    ats_score = db.Column(db.Integer, nullable=False)
    match_score = db.Column(db.Integer, nullable=False)
    missing_keywords = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


with app.app_context():
    db.create_all()


# --------------------------------------------------------------- helpers --

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


def login_required(view):
    from functools import wraps

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


# ---------------------------------------------------------------- routes --

@app.route("/")
def home():
    return render_template("index.html", user=current_user())


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("All fields are required.", "error")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists. Try logging in.", "error")
            return render_template("register.html")

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Account created! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if user is None or not user.check_password(password):
            flash("Invalid email or password.", "error")
            return render_template("login.html")

        session["user_id"] = user.id
        session["username"] = user.username
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You've been logged out.", "success")
    return redirect(url_for("home"))


@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    analyses = (
        Analysis.query.filter_by(user_id=user.id)
        .order_by(Analysis.created_at.desc())
        .all()
    )
    return render_template("dashboard.html", user=user, analyses=analyses)


@app.route("/analyze", methods=["POST"])
def analyze():
    resume = request.files.get("resume")
    jd = request.form.get("job_description", "").strip()

    if not resume or resume.filename == "":
        flash("Please choose a resume file to upload.", "error")
        return redirect(url_for("home"))

    if not allowed_file(resume.filename):
        flash("Only PDF and DOCX files are supported.", "error")
        return redirect(url_for("home"))

    if not jd:
        flash("Please paste a job description to compare against.", "error")
        return redirect(url_for("home"))

    filename = secure_filename(resume.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    resume.save(filepath)

    try:
        resume_text = extract_text(filepath)
    except ParseError as exc:
        flash(str(exc), "error")
        return redirect(url_for("home"))
    finally:
        # Don't keep uploaded resumes around longer than needed for parsing.
        if os.path.exists(filepath):
            os.remove(filepath)

    ats_score, ats_breakdown = calculate_ats_score(resume_text)
    match_score, missing_keywords, matched_keywords = match_keywords(resume_text, jd)

    user = current_user()
    if user:
        analysis = Analysis(
            user_id=user.id,
            filename=filename,
            ats_score=ats_score,
            match_score=match_score,
            missing_keywords=", ".join(missing_keywords),
        )
        db.session.add(analysis)
        db.session.commit()

    return render_template(
        "report.html",
        filename=filename,
        ats_score=ats_score,
        ats_breakdown=ats_breakdown,
        match_score=match_score,
        missing_keywords=missing_keywords,
        matched_keywords=matched_keywords,
        user=user,
    )


@app.errorhandler(413)
def too_large(_e):
    flash("That file is too large. Please upload something under 5 MB.", "error")
    return redirect(url_for("home"))


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(debug=debug)

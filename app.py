from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import PyPDF2
import re

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secretkey123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///resume.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)

# =========================
# DATABASE MODELS
# =========================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

class Analysis(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id')
    )

    ats_score = db.Column(
        db.Integer
    )

    match_score = db.Column(
        db.Integer
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

# =========================
# HELPER FUNCTIONS
# =========================

def extract_text(pdf_path):

    text = ""

    with open(pdf_path, 'rb') as file:

        reader = PyPDF2.PdfReader(file)

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text

    return text.lower()

def calculate_ats_score(text):

    skills = [
        "python",
        "java",
        "sql",
        "mysql",
        "flask",
        "django",
        "html",
        "css",
        "javascript",
        "react",
        "git",
        "github",
        "api"
    ]

    score = 0

    for skill in skills:

        if skill in text:
            score += 8

    return min(score, 100)

def match_keywords(resume_text, jd_text):

    resume_words = set(
        re.findall(r'\w+', resume_text.lower())
    )

    jd_words = set(
        re.findall(r'\w+', jd_text.lower())
    )

    matched = resume_words.intersection(jd_words)

    if len(jd_words) == 0:
        return 0

    score = int(
        len(matched) / len(jd_words) * 100
    )

    return score

# =========================
# HOME
# =========================

@app.route('/')
def home():

    return render_template('index.html')

# =========================
# REGISTER
# =========================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        user_exists = User.query.filter_by(
            email=email
        ).first()

        if user_exists:

            flash("Email already exists")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(
            password
        )

        new_user = User(
            username=username,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Registration Successful")

        return redirect(url_for('login'))

    return render_template('register.html')

# =========================
# LOGIN
# =========================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            session['user_id'] = user.id
            session['username'] = user.username

            return redirect(url_for('dashboard'))

        flash("Invalid Credentials")

    return render_template('login.html')

# =========================
# LOGOUT
# =========================

@app.route('/logout')
def logout():

    session.clear()

    return redirect(url_for('home'))

# =========================
# DASHBOARD
# =========================

@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:

        return redirect(url_for('login'))

    analyses = Analysis.query.filter_by(
        user_id=session['user_id']
    ).order_by(
        Analysis.created_at.desc()
    ).all()

    return render_template(
        'dashboard.html',
        analyses=analyses
    )

# =========================
# ANALYZE RESUME
# =========================

@app.route('/analyze', methods=['POST'])
def analyze():

    if 'user_id' not in session:

        return redirect(url_for('login'))

    resume = request.files['resume']

    jd = request.form['job_description']

    filename = secure_filename(
        resume.filename
    )

    filepath = os.path.join(
        app.config['UPLOAD_FOLDER'],
        filename
    )
    UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

filepath = os.path.join(
    UPLOAD_FOLDER,
    resume.filename
)
    resume.save(filepath)

    resume_text = extract_text(filepath)

    ats_score = calculate_ats_score(
        resume_text
    )

    match_score = match_keywords(
        resume_text,
        jd
    )

    analysis = Analysis(
        user_id=session['user_id'],
        ats_score=ats_score,
        match_score=match_score
    )

    db.session.add(analysis)
    db.session.commit()

    return render_template(
        'report.html',
        ats_score=ats_score,
        match_score=match_score
    )

# =========================
# CREATE DATABASE
# =========================

with app.app_context():
    db.create_all()

# =========================
# RUN APP
# =========================

if __name__ == "__main__":

    app.run(debug=True)

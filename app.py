from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import os
app = Flask(__name__)
app.secret_key = "resume_analyzer_secret"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
def extract_text(filepath):
    return "Sample Resume Text"

def calculate_ats_score(resume_text):
    return 85

def match_keywords(resume_text, jd):
    return 75
@app.route('/')
def home():
    return render_template('index.html')
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        return redirect(url_for('login'))

    return render_template('register.html')
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        session['user'] = request.form['email']
        return redirect(url_for('dashboard'))

    return render_template('login.html')
@app.route('/dashboard')
def dashboard():

    if 'user' not in session:
        return redirect(url_for('login'))

    return render_template('dashboard.html')
@app.route('/analyze', methods=['POST'])
def analyze():

    resume = request.files['resume']
    jd = request.form['job_description']

    filename = secure_filename(resume.filename)

    filepath = os.path.join(
        app.config['UPLOAD_FOLDER'],
        filename
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

    return render_template(
        'report.html',
        ats_score=ats_score,
        match_score=match_score
    )
    @app.route('/logout')
    def logout():
    session.clear()
    return redirect(url_for('home'))
if __name__ == '__main__':
    app.run(debug=True)

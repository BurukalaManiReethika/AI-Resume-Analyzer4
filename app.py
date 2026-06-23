from flask import Flask, render_template, request
import os

from utils.resume_parser import extract_text
from utils.ats_score import calculate_ats_score
from utils.keyword_matcher import match_keywords

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():

    resume = request.files['resume']
    job_description = request.form['job_description']

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], resume.filename)
    resume.save(filepath)

    resume_text = extract_text(filepath)

    ats_score = calculate_ats_score(resume_text)

    match_score, missing_keywords = match_keywords(
        resume_text,
        job_description
    )

    return render_template(
        'index.html',
        ats_score=ats_score,
        match_score=match_score,
        missing_keywords=missing_keywords
    )

if __name__ == '__main__':
    app.run(debug=True)

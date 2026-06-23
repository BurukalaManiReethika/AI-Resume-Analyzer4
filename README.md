# AI Resume Analyzer

Upload a resume (PDF/DOCX) and a job description to get:

- **ATS Score** — a 7-point heuristic check (contact info, section headers,
  bullet points, quantified achievements, action verbs, resume length)
  modeled on common applicant-tracking-system pitfalls.
- **JD Match Score** — keyword overlap between your resume and the job
  description, with a ranked list of missing and matched terms.

Includes user accounts (hashed passwords, SQLite via SQLAlchemy) so logged-in
users can see their analysis history on a dashboard.

## Running locally

```bash
pip install -r requirements.txt
python app.py
```

Visit `http://127.0.0.1:5000`.

## Deploying

Configured for Render (or any platform supporting a `Procfile`):

```
web: gunicorn app:app
```

Set a `SECRET_KEY` environment variable in production. By default the app
uses a local SQLite file (`instance/app.db`); set `DATABASE_URL` to point at
Postgres or another SQLAlchemy-supported database for a persistent deploy
(Render's free-tier filesystem is ephemeral, so SQLite data won't survive
restarts there).

## Project structure

```
app.py                   # routes, models, auth
utils/resume_parser.py   # PDF/DOCX text extraction
utils/ats_score.py       # ATS heuristic scoring
utils/keyword_matcher.py # JD keyword matching
templates/               # Jinja2 templates
static/css/style.css     # styling
```

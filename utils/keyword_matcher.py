"""Compare resume text against a job description and score the overlap."""
import re

STOPWORDS = {
    "the", "and", "for", "are", "but", "not", "you", "all", "can", "her",
    "was", "one", "our", "out", "day", "get", "has", "him", "his", "how",
    "man", "new", "now", "old", "see", "two", "way", "who", "boy", "did",
    "its", "let", "put", "say", "she", "too", "use", "with", "this", "that",
    "from", "they", "have", "will", "your", "work", "what", "when", "make",
    "like", "time", "just", "know", "take", "into", "year", "good", "some",
    "could", "them", "other", "than", "then", "look", "only", "come",
    "over", "think", "also", "back", "after", "first", "well", "even",
    "want", "because", "these", "give", "most", "etc", "such", "job",
    "role", "team", "ability", "strong", "experience", "skills", "years",
    "including", "required", "preferred", "responsibilities", "qualifications",
}

# Words/phrases worth weighting higher when matching — common resume skill terms.
SKILL_HINTS = re.compile(
    r"\b(python|java|javascript|typescript|react|node|sql|aws|azure|gcp|"
    r"docker|kubernetes|flask|django|machine learning|ai|nlp|api|rest|"
    r"agile|scrum|excel|tableau|powerbi|git|html|css|c\+\+|c#|golang|rust)\b",
    re.IGNORECASE,
)


def _tokenize(text):
    return set(w for w in re.findall(r"[a-zA-Z][a-zA-Z+#.-]{1,}", text.lower()) if w not in STOPWORDS)


def match_keywords(resume_text, jd_text):
    """Return (score 0-100, missing_keywords list, matched_keywords list)."""
    resume_words = _tokenize(resume_text)
    jd_words = _tokenize(jd_text)

    if not jd_words:
        return 0, [], []

    matched = sorted(resume_words & jd_words)
    missing = sorted(jd_words - resume_words)

    # Surface high-signal skill terms first in the "missing" list.
    missing.sort(key=lambda w: (0 if SKILL_HINTS.match(w) else 1, w))

    score = int(len(matched) / len(jd_words) * 100)
    return score, missing[:20], matched[:30]

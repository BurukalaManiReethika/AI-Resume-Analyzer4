import re

def match_keywords(resume_text, jd_text):

    resume_words = set(
        re.findall(r'\w+', resume_text.lower())
    )

    jd_words = set(
        re.findall(r'\w+', jd_text.lower())
    )

    matched = resume_words.intersection(jd_words)

    score = int(
        len(matched) / len(jd_words) * 100
    ) if jd_words else 0

    missing = list(
        jd_words - resume_words
    )[:20]

    return score, missing

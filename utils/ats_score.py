def calculate_ats_score(text):

    score = 0

    keywords = [
        "python",
        "flask",
        "sql",
        "api",
        "javascript",
        "react",
        "machine learning"
    ]

    text = text.lower()

    for keyword in keywords:
        if keyword in text:
            score += 10

    return min(score, 100)

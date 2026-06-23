"""Heuristic ATS-friendliness score for a resume.

This isn't a real ATS engine (no vendor exposes one publicly) — it's a
rule-of-thumb check against things that commonly trip up automated
parsers and recruiters: missing contact info, no clear sections, no
quantifiable bullet points, walls of text, etc. Each check contributes
points, capped at 100.
"""
import re

SECTION_HEADERS = [
    "experience", "work experience", "employment",
    "education", "skills", "projects", "summary",
    "objective", "certifications", "achievements",
]

ACTION_VERBS = [
    "led", "built", "created", "developed", "designed", "managed",
    "implemented", "improved", "increased", "reduced", "launched",
    "achieved", "delivered", "optimized", "automated", "analyzed",
    "coordinated", "executed", "established", "streamlined",
]


def calculate_ats_score(text):
    """Return (score 0-100, list of (label, passed: bool, tip) breakdown)."""
    lower = text.lower()
    checks = []
    score = 0

    # 1. Contact info present (email)
    has_email = bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text))
    checks.append(("Email address found", has_email,
                    "Add a professional email address near the top of your resume."))
    score += 15 if has_email else 0

    # 2. Phone number present
    has_phone = bool(re.search(r"(\+?\d[\d\s().-]{7,}\d)", text))
    checks.append(("Phone number found", has_phone,
                    "Add a phone number so recruiters can reach you."))
    score += 10 if has_phone else 0

    # 3. Clear section headers
    found_sections = [s for s in SECTION_HEADERS if s in lower]
    has_sections = len(found_sections) >= 3
    checks.append((f"Clear section headers ({len(found_sections)} found)", has_sections,
                    "Use standard headers like Experience, Education, and Skills "
                    "so ATS software can categorize your content."))
    score += 20 if has_sections else (10 if found_sections else 0)

    # 4. Bullet points / structured content
    bullet_count = len(re.findall(r"(^|\n)\s*[•\-\*]\s+", text))
    has_bullets = bullet_count >= 3
    checks.append((f"Bullet points used ({bullet_count} found)", has_bullets,
                    "List achievements as bullet points rather than paragraphs."))
    score += 15 if has_bullets else 0

    # 5. Quantifiable results (numbers/%/$ near text)
    has_numbers = bool(re.search(r"\d+%|\$\d+|\d+\+|\b\d{2,}\b", text))
    checks.append(("Quantifiable achievements (numbers, %, $)", has_numbers,
                    "Add measurable results, e.g. 'increased sales by 20%'."))
    score += 15 if has_numbers else 0

    # 6. Action verbs
    verbs_found = [v for v in ACTION_VERBS if re.search(r"\b" + v + r"\b", lower)]
    has_verbs = len(verbs_found) >= 3
    checks.append((f"Strong action verbs ({len(verbs_found)} found)", has_verbs,
                    "Start bullet points with action verbs like 'Led', 'Built', 'Improved'."))
    score += 15 if has_verbs else (7 if verbs_found else 0)

    # 7. Reasonable length (not too short, not a wall of text)
    word_count = len(text.split())
    good_length = 250 <= word_count <= 1200
    checks.append((f"Resume length ({word_count} words)", good_length,
                    "Aim for roughly 400-800 words — enough detail without overwhelming a reader."))
    score += 10 if good_length else 0

    return min(score, 100), checks

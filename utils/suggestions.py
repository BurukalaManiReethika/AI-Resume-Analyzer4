"""Generate concrete, actionable rewrite suggestions for a resume.

Like ats_score.py and keyword_matcher.py, this is a transparent rule-based
engine (no external AI calls / API keys required) that flags common
resume-writing problems and shows a before/after style fix wherever
possible, so the suggestion is something the person can act on
immediately rather than a vague note.
"""
import re

MAX_BULLET_SUGGESTIONS = 6
MAX_LINE_WORDS = 28

# Phrase -> stronger opening verb it can usually be replaced with.
WEAK_PHRASES = [
    (r"\bresponsible for\b", "Managed"),
    (r"\bin charge of\b", "Directed"),
    (r"\bduties included\b", "Delivered"),
    (r"\bworked on\b", "Built"),
    (r"\bhelped with\b", "Contributed to"),
    (r"\bhelped to\b", "Contributed to"),
    (r"\bassisted with\b", "Supported"),
    (r"\binvolved in\b", "Drove"),
    (r"\btasked with\b", "Executed"),
]

CLICHES = [
    "hard worker", "team player", "detail oriented", "detail-oriented",
    "results driven", "results-oriented", "results-driven", "go-getter",
    "self-starter", "think outside the box", "outside the box", "synergy",
    "proactive", "fast learner", "excellent communication skills",
    "people person", "works well under pressure",
]

PASSIVE_RE = re.compile(r"\b(was|were|is|are|been|being)\s+\w+ed\b", re.IGNORECASE)
NUMBER_RE = re.compile(r"\d+%|\$\d+|\d+\+|\b\d{2,}\b")
BULLET_RE = re.compile(r"^\s*[•\-\*]\s+(.*)")


def _find_bullets(text):
    bullets = []
    for line in text.splitlines():
        m = BULLET_RE.match(line)
        if m:
            content = m.group(1).strip()
            if content:
                bullets.append(content)
    return bullets


def _weak_phrase_fix(bullet):
    working = bullet
    # Strip a leading passive helper ("Was tasked with...") so the matched
    # phrase always lands at the start of what we rewrite.
    lead = re.match(r"^(was|is|were|are)\s+", working, re.IGNORECASE)
    if lead:
        working = working[lead.end():]

    for pattern, replacement in WEAK_PHRASES:
        m = re.search(pattern, working, re.IGNORECASE)
        if not m:
            continue

        before_part = working[:m.start()]
        after_part = working[m.end():].lstrip()

        # Avoid a redundant verb, e.g. "Managed managing a team" — if the
        # phrase is immediately followed by a gerund and there's enough
        # left over to still make sense, drop the gerund.
        gerund = re.match(r"^(\w+ing)\s+(.*)", after_part)
        if gerund and not before_part.strip() and len(gerund.group(2).split()) >= 2:
            after_part = gerund.group(2)

        rewritten = f"{before_part}{replacement} {after_part}".strip()
        rewritten = re.sub(r"\s+", " ", rewritten)
        if rewritten:
            rewritten = rewritten[0].upper() + rewritten[1:]
        return m.group(0), rewritten

    return None, None


def generate_rewrite_suggestions(resume_text, missing_keywords=None):
    """Return a list of suggestion dicts:
    {category, issue, tip, before (optional), after (optional)}
    """
    missing_keywords = missing_keywords or []
    suggestions = []
    bullets = _find_bullets(resume_text)

    seen_categories_count = {"weak_phrase": 0, "cliche": 0, "passive": 0,
                              "no_metric": 0, "too_long": 0}

    for bullet in bullets:
        if len(suggestions) >= MAX_BULLET_SUGGESTIONS:
            break

        matched_phrase, rewritten = _weak_phrase_fix(bullet)
        if matched_phrase and seen_categories_count["weak_phrase"] < 2:
            suggestions.append({
                "category": "Weak phrasing",
                "issue": "Passive, filler opener instead of a strong action verb",
                "tip": "Cut phrases like \"responsible for\" or \"worked on\" and lead with what you actually did.",
                "before": bullet,
                "after": rewritten,
            })
            seen_categories_count["weak_phrase"] += 1
            continue

        cliche_hit = next((c for c in CLICHES if c in bullet.lower()), None)
        if cliche_hit and seen_categories_count["cliche"] < 2:
            suggestions.append({
                "category": "Generic buzzword",
                "issue": f'Vague self-description ("{cliche_hit}") with no evidence behind it',
                "tip": "Replace the buzzword with a specific example that proves the trait instead of naming it.",
                "before": bullet,
                "after": None,
            })
            seen_categories_count["cliche"] += 1
            continue

        if PASSIVE_RE.search(bullet) and seen_categories_count["passive"] < 2:
            suggestions.append({
                "category": "Passive voice",
                "issue": "Written in passive voice, which reads as less direct and less confident",
                "tip": "Rewrite in active voice: you as the subject, doing the action, not having it done.",
                "before": bullet,
                "after": None,
            })
            seen_categories_count["passive"] += 1
            continue

        if not NUMBER_RE.search(bullet) and seen_categories_count["no_metric"] < 2:
            suggestions.append({
                "category": "No measurable result",
                "issue": "No number, percentage, or scale attached to the impact",
                "tip": 'Add a metric wherever true, e.g. "...reducing page load time by 30%" '
                       'or "...for a team of 8" instead of leaving the result unquantified.',
                "before": bullet,
                "after": None,
            })
            seen_categories_count["no_metric"] += 1
            continue

        word_count = len(bullet.split())
        if word_count > MAX_LINE_WORDS and seen_categories_count["too_long"] < 1:
            suggestions.append({
                "category": "Bullet too long",
                "issue": f"This bullet runs {word_count} words — long bullets get skimmed, not read",
                "tip": "Split it into two bullets or cut it to one clear achievement, ideally under 20 words.",
                "before": bullet,
                "after": None,
            })
            seen_categories_count["too_long"] += 1
            continue

    # Keyword-weaving suggestion (not bullet-specific).
    if missing_keywords:
        top = missing_keywords[:5]
        suggestions.append({
            "category": "Missing keywords",
            "issue": "Several terms from the job description don't appear anywhere in your resume",
            "tip": "Only add these where they're genuinely true of your experience — don't force "
                   "keywords you can't back up in an interview. Try weaving 2-3 into existing "
                   f'bullets, e.g. "...using {top[0]} to accomplish X" rather than listing them separately.',
            "before": None,
            "after": None,
            "keywords": top,
        })

    if not bullets:
        suggestions.insert(0, {
            "category": "No bullet points detected",
            "issue": "Your experience section reads as paragraphs rather than bullet points",
            "tip": "Convert each responsibility/achievement into its own bullet starting with "
                   "\"•\" or \"-\" — ATS parsers and recruiters both scan bullets far faster than prose.",
            "before": None,
            "after": None,
        })

    return suggestions

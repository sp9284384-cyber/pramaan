"""Transparent study-type classifier for Scholar results.

Scholar returns only a title and a ~25-word snippet, so many results cannot
be classified. We say "unclassified" instead of guessing, and we record
whether a label came from the title (stronger) or the snippet (weaker).
"""
import re
from dataclasses import dataclass, field

I = re.IGNORECASE
SYSTEMATIC = re.compile(r"\b(systematic\s+review|meta[\s-]?analy(?:sis|ses)|umbrella\s+review)\b", I)
RCT = re.compile(r"\b(randomi[sz]ed|double[\s-]?blind|placebo[\s-]?controlled|(?-i:RCTs?))\b", I)
OBSERVATIONAL = re.compile(r"\b(cohort|case[\s-]?control|cross[\s-]?sectional|observational|retrospective|prospective|pilot\s+study)\b", I)
PRECLINICAL = re.compile(r"\b(rats?|mice|mouse|murine|wistar|albino|in\s+vitro|cell\s+lines?|animal\s+model)\b", I)
NARRATIVE = re.compile(r"(narrative\s+review|literature\s+review|scoping\s+review|comprehensive\s+review|\boverview\b|:\s*a\s+review\b|\ba\s+review\b)", I)
PREPRINT = re.compile(r"medrxiv|biorxiv|arxiv|ssrn|researchsquare|preprint", I)

LABELS = {
    "systematic_review": "Systematic review / meta-analysis",
    "rct": "Randomized controlled trial",
    "observational_or_pilot": "Observational / pilot (human)",
    "preclinical": "Preclinical (animal / in vitro)",
    "narrative_review": "Narrative review",
    "book": "Book (not peer-reviewed article)",
    "unclassified": "Unclassified (design not visible)",
}


@dataclass
class Classification:
    tier: str
    label: str
    basis: str            # "title", "snippet", "type-field", or "none"
    flags: list = field(default_factory=list)


def classify(title: str, snippet: str = "", venue: str = "",
             result_type: str = None) -> Classification:
    flags = ["preprint"] if PREPRINT.search(venue or "") else []

    def done(tier, basis):
        return Classification(tier, LABELS[tier], basis, flags)

    if result_type == "Book":
        return done("book", "type-field")

    # Title first. A title that says "review" beats trial wording in the snippet.
    if SYSTEMATIC.search(title):
        return done("systematic_review", "title")
    if NARRATIVE.search(title):
        return done("narrative_review", "title")
    if RCT.search(title):
        return done("rct", "title")
    if PRECLINICAL.search(title):
        return done("preclinical", "title")
    if OBSERVATIONAL.search(title):
        return done("observational_or_pilot", "title")

    # Snippet is weaker evidence; used only when the title is silent.
    if SYSTEMATIC.search(snippet):
        return done("systematic_review", "snippet")
    if RCT.search(snippet):
        return done("rct", "snippet")
    if PRECLINICAL.search(snippet):
        return done("preclinical", "snippet")
    if OBSERVATIONAL.search(snippet):
        return done("observational_or_pilot", "snippet")

    return done("unclassified", "none")

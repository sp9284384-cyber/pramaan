"""Claim normalization (English/Hinglish -> search queries) and snippet stance."""
import re
from dataclasses import dataclass, field

from .llm import LLMUnavailable, gemini_json

NORMALIZE_PROMPT = """You prepare search queries for a health-claim evidence checker.
The claim may be in English, Hindi, or Hinglish (Hindi written in Latin script).
Return JSON only, with exactly these keys:
{"language": "...", "claim_en": "...", "intervention": "...", "outcome": "...",
 "population": "...", "scholar_queries": ["..."], "news_query": "...", "web_query": "..."}
Rules:
- claim_en: one plain-English sentence with the same meaning. Add nothing.
- Queries: 2-5 plain words using standard English terms (for example haldi -> turmeric).
- Do NOT put study-design words (randomized, meta-analysis, trial, review) in any query.
- At most 2 scholar_queries.
- If something is unclear, keep it as written. Do not guess details.
Claim: """

STANCE_PROMPT = """Judge each source's stance toward the claim using ONLY the title and snippet shown.
Do not use outside knowledge.
supports: the text reports a finding that supports the claim.
opposes: the text reports a finding that contradicts the claim or reports no effect.
insufficient: the text states no finding about the claim (background, methods, general discussion).
Return JSON only:
{"stances": [{"i": 0, "stance": "supports|opposes|insufficient", "evidence": "short phrase copied exactly from the text, or empty"}]}
"""

STANCES = {"supports", "opposes", "insufficient"}


@dataclass
class NormalizedClaim:
    original: str
    claim_en: str
    scholar_queries: list
    news_query: str
    web_query: str
    language: str = "unknown"
    llm_used: bool = False


def _clean_queries(qs, fallback):
    qs = [q.strip() for q in (qs or []) if isinstance(q, str) and q.strip()]
    return qs[:2] or [fallback]


def normalize_claim(text: str, llm=gemini_json) -> NormalizedClaim:
    try:
        d = llm(NORMALIZE_PROMPT + text)
    except LLMUnavailable:
        return NormalizedClaim(text, text, [text], text, text, llm_used=False)
    claim_en = str(d.get("claim_en") or text)
    return NormalizedClaim(
        original=text, claim_en=claim_en,
        scholar_queries=_clean_queries(d.get("scholar_queries"), claim_en),
        news_query=str(d.get("news_query") or claim_en),
        web_query=str(d.get("web_query") or claim_en),
        language=str(d.get("language") or "unknown"), llm_used=True)


def _norm(s):
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def parse_stances(raw: dict, sources: list) -> list:
    """Validate LLM output. A supports/opposes call must quote the source text;
    otherwise it is downgraded to 'insufficient' (flagged ungrounded)."""
    by_i = {}
    for s in (raw or {}).get("stances", []):
        if isinstance(s, dict) and isinstance(s.get("i"), int):
            by_i[s["i"]] = s
    out = []
    for i, (title, snippet) in enumerate(sources):
        s = by_i.get(i, {})
        stance = s.get("stance") if s.get("stance") in STANCES else "insufficient"
        evidence = str(s.get("evidence") or "")
        grounded = True
        if stance != "insufficient":
            if not evidence or _norm(evidence) not in _norm(f"{title} {snippet}"):
                stance, grounded = "insufficient", False
        out.append({"stance": stance, "evidence": evidence if grounded else "",
                    "ungrounded": not grounded})
    return out


def classify_stances(claim_en: str, sources: list, llm=gemini_json) -> list:
    """sources: list of (title, snippet). One LLM call for the whole batch."""
    if not sources:
        return []
    lines = "\n".join(f"{i}. Title: {t} | Snippet: {s}" for i, (t, s) in enumerate(sources))
    try:
        raw = llm(f"{STANCE_PROMPT}Claim: {claim_en}\nSources:\n{lines}")
    except LLMUnavailable:
        raw = {}
    return parse_stances(raw, sources)


_RANK = ["systematic_review", "rct", "observational_or_pilot", "narrative_review", "unclassified"]


def summarize(items: list) -> dict:
    """items: [{'tier': ..., 'stance': ...}]. Reports conflict; never a verdict.
    Preclinical and book sources do not count toward human-evidence conflict."""
    def human(x):
        return x["tier"] not in ("preclinical", "book")
    sup = [x for x in items if x["stance"] == "supports"]
    opp = [x for x in items if x["stance"] == "opposes"]
    sup_h, opp_h = [x for x in sup if human(x)], [x for x in opp if human(x)]
    if sup_h and opp_h:
        status = "conflict"
    elif sup_h:
        status = "supported"
    elif opp_h:
        status = "opposed"
    elif sup:
        status = "preclinical_only_support"
    else:
        status = "insufficient"
    best = next((t for t in _RANK if any(x["tier"] == t for x in sup_h)), None)
    return {"status": status, "supports": len(sup), "opposes": len(opp),
            "insufficient": len(items) - len(sup) - len(opp),
            "strongest_supporting_tier": best, "n_total": len(items)}

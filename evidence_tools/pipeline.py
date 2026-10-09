"""check_claim: normalize -> Scholar search -> classify -> stance -> summarize."""
from .claims import classify_stances, normalize_claim, summarize
from .classify import classify
from .llm import gemini_json
from .scholar import search_scholar

MAX_SOURCES = 10  # bounds LLM input and keeps credits predictable


def check_claim(text: str, search=search_scholar, llm=gemini_json) -> dict:
    nc = normalize_claim(text, llm=llm)
    seen, results = set(), []
    for q in nc.scholar_queries:
        for r in search(q):
            key = (r.link or r.title).lower()
            if key not in seen:
                seen.add(key)
                results.append(r)
    results = results[:MAX_SOURCES]
    cls = [classify(r.title, r.snippet, r.venue, r.result_type) for r in results]
    stances = classify_stances(nc.claim_en, [(r.title, r.snippet) for r in results], llm=llm)
    items = [{"tier": c.tier, "stance": s["stance"]} for c, s in zip(cls, stances)]
    return {
        "claim": nc, "results": results, "classifications": cls,
        "stances": stances, "summary": summarize(items),
        "unclassified": sum(c.tier == "unclassified" for c in cls),
    }


DISCLAIMER = ("Not medical advice. This labels and compares evidence; "
              "it does not diagnose or recommend treatment.")


def result_to_dict(r: dict) -> dict:
    """JSON-serializable view of a check_claim() result (used by MCP, web, eval)."""
    from dataclasses import asdict
    sources = []
    for res, c, s in zip(r["results"], r["classifications"], r["stances"]):
        sources.append({
            "title": res.title, "snippet": res.snippet, "venue": res.venue,
            "year": res.year, "cited_by": res.cited_by, "link": res.link,
            "tier": c.tier, "label": c.label, "basis": c.basis, "flags": c.flags,
            "stance": s["stance"], "evidence": s["evidence"], "ungrounded": s["ungrounded"],
        })
    return {"claim": asdict(r["claim"]), "summary": r["summary"],
            "unclassified": r["unclassified"], "sources": sources,
            "disclaimer": DISCLAIMER}

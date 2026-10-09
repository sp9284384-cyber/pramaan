"""Shared fake check result (same shape as pipeline.result_to_dict)."""


def fake_result(status="supported", unclassified=1, llm_used=True):
    return {
        "claim": {"original": "x", "claim_en": "Turmeric lowers blood sugar.", "scholar_queries": ["turmeric blood sugar"],
                  "news_query": "n", "web_query": "w", "language": "en", "llm_used": llm_used},
        "summary": {"status": status, "supports": 1, "opposes": 0, "insufficient": 1,
                    "strongest_supporting_tier": "systematic_review", "n_total": 2},
        "unclassified": unclassified,
        "sources": [
            {"title": "A meta-analysis", "snippet": "s", "venue": "v", "year": 2023, "cited_by": 5, "link": "http://a",
             "tier": "systematic_review", "label": "Systematic review / meta-analysis", "basis": "title", "flags": [],
             "stance": "supports", "evidence": "glucose lowering", "ungrounded": False},
            {"title": "Other", "snippet": "t", "venue": "v", "year": 2020, "cited_by": 1, "link": "http://b",
             "tier": "unclassified", "label": "Unclassified (design not visible)", "basis": "none", "flags": [],
             "stance": "insufficient", "evidence": "", "ungrounded": False},
        ],
        "disclaimer": "Not medical advice.",
    }

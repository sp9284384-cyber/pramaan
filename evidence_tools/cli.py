"""Usage:
  python -m evidence_tools.cli --check "haldi se sugar control hoti hai"   # needs SERPAPI_API_KEY (+ GEMINI_API_KEY)
  python -m evidence_tools.cli "turmeric blood sugar"                      # search + classify only
  python -m evidence_tools.cli --fixture saved_response.json               # offline, 0 credits
"""
import argparse
import json
from collections import Counter

from .classify import classify
from .pipeline import check_claim
from .scholar import parse_scholar, search_scholar


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?")
    ap.add_argument("--fixture", help="path to a saved SerpApi JSON response")
    ap.add_argument("--check", metavar="CLAIM", help="full claim check (English or Hinglish)")
    a = ap.parse_args()

    if a.check:
        r = check_claim(a.check)
        nc = r["claim"]
        print(f"Claim (EN): {nc.claim_en}  [language={nc.language}, llm={nc.llm_used}]")
        print(f"Scholar queries: {nc.scholar_queries}\n")
        for res, c, s in zip(r["results"], r["classifications"], r["stances"]):
            flags = ",".join(c.flags + (["ungrounded"] if s["ungrounded"] else [])) or "-"
            print(f"{res.position:>2} {c.tier:<24} {s['stance']:<12} [{flags}] {res.title[:60]}")
        sm = r["summary"]
        print(f"\nStatus: {sm['status']}  supports={sm['supports']} opposes={sm['opposes']} "
              f"insufficient={sm['insufficient']}  strongest_support={sm['strongest_supporting_tier']}")
        print(f"Unclassified design: {r['unclassified']}/{len(r['results'])}")
        print("Not medical advice: this labels evidence; it does not give a verdict.")
        return

    if a.fixture:
        with open(a.fixture, encoding="utf-8") as f:
            results = parse_scholar(json.load(f))
    elif a.query:
        results = search_scholar(a.query)
    else:
        ap.error("give a query, --fixture, or --check")

    counts = Counter()
    for r in results:
        c = classify(r.title, r.snippet, r.venue, r.result_type)
        counts[c.tier] += 1
        flags = ",".join(c.flags) or "-"
        print(f"{r.position:>2} {c.tier:<24} {c.basis:<9} cited={r.cited_by:<5} [{flags}] {r.title[:70]}")
    n = len(results) or 1
    print(f"\nunclassified: {counts['unclassified']}/{len(results)} ({100 * counts['unclassified'] // n}%)")


if __name__ == "__main__":
    main()

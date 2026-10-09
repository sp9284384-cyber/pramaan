import unittest

from evidence_tools.claims import (classify_stances, normalize_claim,
                                   parse_stances, summarize)
from evidence_tools.llm import LLMUnavailable
from evidence_tools.pipeline import check_claim
from evidence_tools.scholar import ScholarResult


def no_llm(prompt):
    raise LLMUnavailable("no key")


class TestNormalize(unittest.TestCase):
    def test_offline_fallback_keeps_text(self):
        nc = normalize_claim("haldi se sugar control hoti hai", llm=no_llm)
        self.assertFalse(nc.llm_used)
        self.assertEqual(nc.scholar_queries, ["haldi se sugar control hoti hai"])

    def test_llm_output_is_cleaned_and_capped(self):
        fake = lambda p: {"language": "hinglish", "claim_en": "Turmeric lowers blood sugar.",
                          "scholar_queries": ["turmeric blood sugar", "curcumin glucose", "extra"],
                          "news_query": "turmeric diabetes", "web_query": ""}
        nc = normalize_claim("haldi se sugar kam hoti hai", llm=fake)
        self.assertTrue(nc.llm_used)
        self.assertEqual(len(nc.scholar_queries), 2)
        self.assertEqual(nc.web_query, "Turmeric lowers blood sugar.")  # empty -> fallback


class TestStance(unittest.TestCase):
    SRC = [("Turmeric and glucose", "no effect was seen in patients with normal baseline levels of blood sugar"),
           ("Background on curcumin", "curcumin is a polyphenol")]

    def test_grounded_stance_kept(self):
        raw = {"stances": [{"i": 0, "stance": "opposes", "evidence": "No effect was seen in patients"},
                           {"i": 1, "stance": "insufficient", "evidence": ""}]}
        out = parse_stances(raw, self.SRC)
        self.assertEqual(out[0]["stance"], "opposes")
        self.assertFalse(out[0]["ungrounded"])

    def test_ungrounded_stance_downgraded(self):
        raw = {"stances": [{"i": 0, "stance": "supports", "evidence": "this quote is not in the text"}]}
        out = parse_stances(raw, self.SRC)
        self.assertEqual(out[0]["stance"], "insufficient")
        self.assertTrue(out[0]["ungrounded"])

    def test_missing_or_invalid_defaults_to_insufficient(self):
        out = parse_stances({"stances": [{"i": 0, "stance": "banana"}]}, self.SRC)
        self.assertEqual([o["stance"] for o in out], ["insufficient", "insufficient"])

    def test_no_llm_gives_all_insufficient(self):
        out = classify_stances("claim", self.SRC, llm=no_llm)
        self.assertTrue(all(o["stance"] == "insufficient" for o in out))


class TestSummarize(unittest.TestCase):
    def S(self, *pairs):
        return summarize([{"tier": t, "stance": s} for t, s in pairs])

    def test_conflict_between_human_sources(self):
        r = self.S(("rct", "supports"), ("systematic_review", "opposes"))
        self.assertEqual(r["status"], "conflict")
        self.assertEqual(r["strongest_supporting_tier"], "rct")

    def test_preclinical_only_support_is_flagged_not_supported(self):
        r = self.S(("preclinical", "supports"), ("preclinical", "supports"), ("unclassified", "insufficient"))
        self.assertEqual(r["status"], "preclinical_only_support")

    def test_preclinical_support_vs_human_opposition_is_not_conflict(self):
        r = self.S(("preclinical", "supports"), ("rct", "opposes"))
        self.assertEqual(r["status"], "opposed")

    def test_insufficient(self):
        self.assertEqual(self.S(("unclassified", "insufficient"))["status"], "insufficient")


class TestPipeline(unittest.TestCase):
    def test_end_to_end_with_fakes(self):
        def fake_llm(prompt):
            if prompt.startswith("You prepare"):
                return {"language": "hinglish", "claim_en": "Turmeric lowers blood sugar.",
                        "scholar_queries": ["turmeric blood sugar"], "news_query": "n", "web_query": "w"}
            return {"stances": [{"i": 0, "stance": "supports", "evidence": "glucose lowering effect"},
                                {"i": 1, "stance": "insufficient", "evidence": ""}]}

        def fake_search(q):
            return [
                ScholarResult(1, "Effect of turmeric: a meta-analysis", "glucose lowering effect of turmeric", "A - J, 2023 - x", 2023, 10, "http://a", None, None),
                ScholarResult(2, "Efficacy of turmeric in diabetic albino rats", "rats", "B - J, 2002 - y", 2002, 5, "http://b", None, None),
                ScholarResult(3, "Effect of turmeric: a meta-analysis", "dup", "A - J, 2023 - x", 2023, 10, "http://a", None, None),  # duplicate link
            ]
        r = check_claim("haldi se sugar kam hoti hai", search=fake_search, llm=fake_llm)
        self.assertEqual(len(r["results"]), 2)  # duplicate removed
        self.assertEqual(r["summary"]["status"], "supported")
        self.assertEqual(r["summary"]["strongest_supporting_tier"], "systematic_review")


if __name__ == "__main__":
    unittest.main()

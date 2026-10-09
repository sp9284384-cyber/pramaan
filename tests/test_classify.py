import unittest

from evidence_tools.classify import classify
from evidence_tools.scholar import parse_scholar


class TestClassify(unittest.TestCase):
    # Titles/snippets taken from real SerpApi Scholar responses.
    def test_meta_analysis_title(self):
        c = classify("Effect of Curcuma longa rhizome extract on fasting blood sugar levels and HbA1C in type 2 diabetes mellitus: A meta-analysis")
        self.assertEqual((c.tier, c.basis), ("systematic_review", "title"))

    def test_umbrella_review_with_truncated_title(self):
        c = classify("Effects of turmeric (Curcuma longa) supplementation on glucose metabolism: An umbrella review and updated meta …")
        self.assertEqual(c.tier, "systematic_review")

    def test_rct_in_title(self):
        c = classify("Apple cider vinegar for weight management in Lebanese adolescents: a randomised, double-blind, placebo-controlled …")
        self.assertEqual(c.tier, "rct")

    def test_preclinical(self):
        self.assertEqual(classify("Efficacy of turmeric on blood sugar and polyol pathway in diabetic albino rats").tier, "preclinical")
        self.assertEqual(classify("Curcuminoids ... Suppress an Increase in Blood Glucose Level in Type 2 Diabetic KK-Ay Mice").tier, "preclinical")

    def test_narrative_review_beats_trial_words_in_snippet(self):
        c = classify("Vitamin D and COVID-19: A narrative review",
                     snippet="randomized controlled trials have examined ...")
        self.assertEqual(c.tier, "narrative_review")

    def test_book_type_field(self):
        self.assertEqual(classify("Apple Cider Vinegar for Weight Loss and Good Health", result_type="Book").tier, "book")

    def test_pilot_study_title(self):
        self.assertEqual(classify("Apple Cider Vinegar and Weight Loss: Insights from a Clinical Pilot Study").tier, "observational_or_pilot")

    def test_preprint_flag(self):
        c = classify("A systematic review and meta-analysis of curcumin", venue="DC Innocent - medRxiv, 2023 - medrxiv.org")
        self.assertIn("preprint", c.flags)

    def test_design_not_visible_stays_unclassified(self):
        # Honest "unclassified": no guessing when the design is not in title/snippet.
        for t in ["Evidence regarding vitamin D and risk of COVID-19 and its severity",
                  "Efficacy of turmeric as adjuvant therapy in type 2 diabetic patients",
                  "Beneficial effects of Apple Cider Vinegar on weight management in overweight or obese subjects receiving restricted calorie …"]:
            self.assertEqual(classify(t).tier, "unclassified", t)


class TestParse(unittest.TestCase):
    def test_missing_fields_do_not_crash(self):
        data = {"organic_results": [
            {"position": 1, "title": "T", "snippet": "s",
             "publication_info": {"summary": "A B - J, 2021 - x.org"},
             "inline_links": {"cited_by": {"total": 5, "cites_id": "9"}}},
            {"position": 2, "title": "No links", "inline_links": {}},
            {"position": 3, "title": "Nothing else"},
        ]}
        rs = parse_scholar(data)
        self.assertEqual((rs[0].year, rs[0].cited_by, rs[0].cites_id), (2021, 5, "9"))
        self.assertEqual(rs[1].cited_by, 0)
        self.assertEqual(len(rs), 3)


if __name__ == "__main__":
    unittest.main()

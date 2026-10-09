import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

from tests._fakes import fake_result

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("run_eval", ROOT / "evaluation" / "run_eval.py")
run_eval = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_eval)


class TestEval(unittest.TestCase):
    def test_claims_csv_shape(self):
        rows = run_eval.load_claims()
        self.assertEqual(len(rows), 20)
        langs = {r["language"] for r in rows}
        self.assertEqual(langs, {"en", "hinglish"})
        pairs = {}
        for r in rows:
            pairs.setdefault(r["pair"], []).append(r["language"])
        self.assertTrue(all(sorted(v) == ["en", "hinglish"] for v in pairs.values()))
        self.assertTrue(all(r["expected_status"] == "" for r in rows))  # labels are yours to fill

    def test_metrics_and_pair_consistency(self):
        rows = [{"id": "A-en", "pair": "A", "claim": "c1", "language": "en", "expected_status": "supported"},
                {"id": "A-hi", "pair": "A", "claim": "c2", "language": "hinglish", "expected_status": ""},
                {"id": "B-en", "pair": "B", "claim": "c3", "language": "en", "expected_status": ""},
                {"id": "B-hi", "pair": "B", "claim": "c4", "language": "hinglish", "expected_status": ""}]
        status = {"c1": "supported", "c2": "supported", "c3": "conflict", "c4": "insufficient"}
        recs = run_eval.evaluate(rows, check=lambda c: fake_result(status[c.__str__()], unclassified=1))
        m = run_eval.compute_metrics(recs)
        self.assertEqual(m["pairs"], 2)
        self.assertEqual(m["pairs_consistent"], 1)
        self.assertEqual(m["sources"], 8)
        self.assertAlmostEqual(m["unclassified_rate"], 4 / 8)
        self.assertEqual((m["labeled_claims"], m["status_correct"]), (1, 1))

    def test_errors_are_recorded_not_raised(self):
        def boom(c):
            raise TimeoutError("x")
        recs = run_eval.evaluate([{"id": "A", "pair": "", "claim": "c", "language": "en"}], check=boom)
        self.assertEqual(recs[0]["status"], "error")
        self.assertEqual(run_eval.compute_metrics(recs)["errors"], 1)

    def test_label_sheet_scoring_ignores_unlabeled(self):
        recs = run_eval.evaluate([{"id": "A", "pair": "", "claim": "c", "language": "en"}], check=lambda c: fake_result())
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "sheet.csv"
            run_eval.write_label_sheet(recs, p)
            rows = list(csv.DictReader(open(p, encoding="utf-8")))
            self.assertEqual(len(rows), 2)
            rows[0]["human_stance"] = "supports"      # model said supports -> correct
            rows[1]["human_stance"] = "opposes"       # model said insufficient -> wrong
            with open(p, "w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=rows[0].keys())
                w.writeheader()
                w.writerows(rows)
            s = run_eval.score_label_sheet(p)
        self.assertEqual((s["labeled"], s["correct"]), (2, 1))

    def test_results_md_is_generated(self):
        recs = run_eval.evaluate([{"id": "A", "pair": "", "claim": "c", "language": "en"}], check=lambda c: fake_result())
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "R.md"
            run_eval.write_results_md(recs, run_eval.compute_metrics(recs), path=p)
            self.assertIn("Unclassified", p.read_text(encoding="utf-8").title() if False else p.read_text(encoding="utf-8").replace("unclassified", "Unclassified"))


if __name__ == "__main__":
    unittest.main()

import json
import unittest
from pathlib import Path

from evidence_tools.classify import classify
from evidence_tools.scholar import parse_scholar

FIX = Path(__file__).parent / "fixtures"
FILES = sorted(FIX.glob("*.json"))


@unittest.skipUnless(FILES, "no saved Scholar JSON in tests/fixtures/")
class TestFixtures(unittest.TestCase):
    def test_real_responses_parse_and_classify(self):
        total = unc = 0
        for p in FILES:
            for r in parse_scholar(json.loads(p.read_text(encoding="utf-8"))):
                c = classify(r.title, r.snippet, r.venue, r.result_type)
                total += 1
                unc += c.tier == "unclassified"
                self.assertTrue(r.title)
        print(f"\n[fixtures] unclassified {unc}/{total}")
        self.assertGreater(total, 0)


if __name__ == "__main__":
    unittest.main()

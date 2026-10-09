import unittest

from evidence_tools.adapters import function_tool as ft


class TestAdapter(unittest.TestCase):
    def test_schemas_well_formed(self):
        for t in ft.TOOL_SCHEMAS:
            fn = t["function"]
            self.assertTrue(fn["name"] and fn["description"])
            self.assertEqual(fn["parameters"]["type"], "object")
            self.assertTrue(set(fn["parameters"]["required"]) <= set(fn["parameters"]["properties"]))

    def test_label_tool(self):
        out = ft.run_tool("label_study_design", {"title": "Rats and curcumin in diabetic Wistar rats"})
        self.assertEqual(out["tier"], "preclinical")

    def test_unknown_tool_and_bad_claim(self):
        with self.assertRaises(KeyError):
            ft.run_tool("nope", {})
        with self.assertRaises(ValueError):
            ft.run_tool("check_health_claim", {"claim": ""})


if __name__ == "__main__":
    unittest.main()

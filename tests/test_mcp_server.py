import asyncio
import unittest

try:
    from evidence_tools import mcp_server
    HAVE_MCP = True
except ImportError:
    HAVE_MCP = False

from tests._fakes import fake_result


@unittest.skipUnless(HAVE_MCP, "mcp SDK not installed")
class TestMcpServer(unittest.TestCase):
    def test_tools_are_registered(self):
        names = {t.name for t in asyncio.run(mcp_server.mcp.list_tools())}
        self.assertEqual(names, {"check_health_claim", "label_study_design"})

    def test_label_study_design(self):
        out = mcp_server.label_study_design("Effect of X: a meta-analysis")
        self.assertEqual(out["tier"], "systematic_review")

    def test_check_rejects_empty_and_long_claims(self):
        with self.assertRaises(ValueError):
            mcp_server.check_health_claim("   ")
        with self.assertRaises(ValueError):
            mcp_server.check_health_claim("x" * 501)

    def test_check_uses_pipeline(self):
        orig = mcp_server.check_claim, mcp_server.result_to_dict
        mcp_server.check_claim = lambda c: {"fake": c}
        mcp_server.result_to_dict = lambda r: fake_result()
        try:
            out = mcp_server.check_health_claim("turmeric lowers blood sugar")
        finally:
            mcp_server.check_claim, mcp_server.result_to_dict = orig
        self.assertEqual(out["summary"]["status"], "supported")


if __name__ == "__main__":
    unittest.main()

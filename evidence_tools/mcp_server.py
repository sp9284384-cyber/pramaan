"""MCP server exposing Pramaan to any MCP client (Claude Desktop, MCP Inspector, ...).

Run:  python -m evidence_tools.mcp_server      (stdio transport)
Needs SERPAPI_API_KEY (and GEMINI_API_KEY for Hinglish normalization and stance).
"""
from typing import Optional

try:                                                   # mcp >= 2
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:                                    # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server

from .classify import classify
from .pipeline import check_claim, result_to_dict

mcp = _Server("pramaan")


@mcp.tool()
def check_health_claim(claim: str) -> dict:
    """Check a health claim written in English or Hinglish.

    Retrieves Google Scholar evidence through SerpApi, labels each source's study design
    (or 'unclassified' when it is not visible), judges each source's stance from its
    snippet, and reports whether credible sources conflict. It never returns a single
    verdict. Not medical advice.
    """
    claim = (claim or "").strip()
    if not claim or len(claim) > 500:
        raise ValueError("claim must be 1-500 characters")
    return result_to_dict(check_claim(claim))


@mcp.tool()
def label_study_design(title: str, snippet: str = "", venue: str = "",
                       result_type: Optional[str] = None) -> dict:
    """Label the study design of one search result from its title/snippet (no API calls)."""
    c = classify(title, snippet, venue, result_type)
    return {"tier": c.tier, "label": c.label, "basis": c.basis, "flags": c.flags}


def main():
    import sys
    print(
        "Pramaan MCP server ready (stdio transport).\n"
        "Tools exposed: check_health_claim · label_study_design\n"
        "Waiting for an MCP client (Claude Desktop, MCP Inspector, ...)...",
        file=sys.stderr,
        flush=True,
    )
    mcp.run()


if __name__ == "__main__":
    main()

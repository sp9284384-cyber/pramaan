"""Framework-agnostic function-calling adapter.

Works with any framework that accepts JSON-schema function tools (OpenAI-style
chat/Agents tools, Gemini function calling, and similar):

    from evidence_tools.adapters.function_tool import TOOL_SCHEMAS, run_tool
    # pass TOOL_SCHEMAS as the tool list; when the model calls a tool:
    result = run_tool(name, arguments_dict)
"""
from ..classify import classify
from ..pipeline import check_claim, result_to_dict

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "check_health_claim",
            "description": ("Check a health claim (English or Hinglish) against Google Scholar via "
                            "SerpApi. Returns study-design labels, per-source stance, and a conflict "
                            "summary. Not medical advice."),
            "parameters": {
                "type": "object",
                "properties": {"claim": {"type": "string", "description": "The health claim, 1-500 chars"}},
                "required": ["claim"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "label_study_design",
            "description": "Label the study design of one search result from its title/snippet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "snippet": {"type": "string"},
                    "venue": {"type": "string"},
                },
                "required": ["title"],
            },
        },
    },
]


def run_tool(name: str, arguments: dict) -> dict:
    if name == "check_health_claim":
        claim = str(arguments.get("claim", "")).strip()
        if not claim or len(claim) > 500:
            raise ValueError("claim must be 1-500 characters")
        return result_to_dict(check_claim(claim))
    if name == "label_study_design":
        c = classify(arguments.get("title", ""), arguments.get("snippet", ""), arguments.get("venue", ""))
        return {"tier": c.tier, "label": c.label, "basis": c.basis, "flags": c.flags}
    raise KeyError(f"unknown tool: {name}")

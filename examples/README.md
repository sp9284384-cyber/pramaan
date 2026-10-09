# Connecting Pramaan to Claude Desktop

1. `pip install -e .` from the repository root (use the same Python that Claude Desktop will launch;
   if you use a virtualenv, put its full path to `python` in `command`).
2. Copy `claude_desktop_config.example.json` into your Claude Desktop config (Settings > Developer > Edit Config),
   replace the placeholders with your own keys, and restart Claude Desktop.
3. Never commit or screen-record the real config file: it contains your keys.

Alternative without Claude Desktop: `npx @modelcontextprotocol/inspector python -m evidence_tools.mcp_server`

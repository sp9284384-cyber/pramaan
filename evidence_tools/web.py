"""Minimal local web demo: serves web/index.html and POST /api/check. Standard library only.

Run:  python -m evidence_tools.web [port]     then open http://127.0.0.1:8000
Binds to localhost only. Run it from the repository root (it serves web/index.html).
"""
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .pipeline import check_claim, result_to_dict

INDEX = Path(__file__).resolve().parent.parent / "web" / "index.html"


def _default_check(text):
    return result_to_dict(check_claim(text))


CHECK = _default_check  # replaced in tests


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body: bytes, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj).encode("utf-8"))

    def do_GET(self):
        if self.path in ("/", "/index.html") and INDEX.exists():
            self._send(200, INDEX.read_bytes(), "text/html")
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/check":
            return self._json(404, {"error": "not found"})
        try:
            n = int(self.headers.get("Content-Length", 0))
            if n > 10_000:
                return self._json(413, {"error": "request too large"})
            claim = str(json.loads(self.rfile.read(n) or b"{}").get("claim", "")).strip()
        except (ValueError, AttributeError):
            return self._json(400, {"error": "invalid JSON"})
        if not claim or len(claim) > 500:
            return self._json(400, {"error": "claim must be 1-500 characters"})
        try:
            self._json(200, CHECK(claim))
        except Exception as e:  # never echo exception text (could contain URLs/keys)
            print(f"check failed: {type(e).__name__}", file=sys.stderr)
            self._json(500, {"error": f"check failed ({type(e).__name__}). See server log."})


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Pramaan demo on http://127.0.0.1:{port}  (Ctrl+C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

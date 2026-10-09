"""Tiny on-disk JSON cache so repeated queries never spend SerpApi credits."""
import hashlib
import json
from pathlib import Path


class DiskCache:
    def __init__(self, directory: str = ".cache/serpapi"):
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def key(params: dict) -> str:
        clean = {k: v for k, v in params.items() if k != "api_key"}
        blob = json.dumps(clean, sort_keys=True).encode()
        return hashlib.sha256(blob).hexdigest()[:24]

    def get(self, params: dict):
        path = self.dir / f"{self.key(params)}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return None

    def set(self, params: dict, data: dict) -> None:
        path = self.dir / f"{self.key(params)}.json"
        path.write_text(json.dumps(data), encoding="utf-8")

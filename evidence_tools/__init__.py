"""serpapi-evidence-tools: evidence-aware search over SerpApi."""
import os
from pathlib import Path


def _load_dotenv() -> None:
    for base in [Path.cwd(), Path(__file__).resolve().parent.parent]:
        env_file = base / ".env"
        if env_file.is_file():
            try:
                with open(env_file, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k, v = k.strip(), v.strip().strip("'\"")
                            if k and k not in os.environ:
                                os.environ[k] = v
                break
            except Exception:
                pass


_load_dotenv()


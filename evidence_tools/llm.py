"""Gemini JSON helper. Cached on disk so repeated prompts cost nothing."""
import json
import os
from typing import Optional

from .cache import DiskCache

# Override with GEMINI_MODEL if this name is unavailable on your key.
DEFAULT_MODEL = "gemini-3.5-flash-lite"
FALLBACK_MODELS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-flash-latest"]


class LLMUnavailable(RuntimeError):
    pass


def gemini_json(prompt: str, cache: Optional[DiskCache] = None,
                model: Optional[str] = None) -> dict:
    selected_model = model or os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)
    cache = cache or DiskCache(".cache/llm")
    params = {"kind": "gemini", "model": selected_model, "prompt": prompt}
    hit = cache.get(params)
    if hit is not None:
        return hit
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise LLMUnavailable("Set GEMINI_API_KEY")
    try:
        from google import genai
        from google.genai import types
    except ImportError as e:
        raise LLMUnavailable("pip install google-genai") from e
    client = genai.Client(api_key=api_key)

    candidates = [selected_model]
    for m in FALLBACK_MODELS:
        if m not in candidates:
            candidates.append(m)

    last_err = None
    for cand in candidates:
        try:
            resp = client.models.generate_content(
                model=cand, contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json", temperature=0),
            )
            data = json.loads(resp.text)
            cache.set(params, data)
            return data
        except Exception as e:
            last_err = e
            msg = str(e).lower()
            if any(k in msg for k in ("429", "resource_exhausted", "503", "unavailable", "deadline")):
                continue
            raise

    if last_err:
        raise last_err
    raise LLMUnavailable("No candidate model succeeded")


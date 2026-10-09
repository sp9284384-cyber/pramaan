"""SerpApi Google Scholar client: cached fetch + defensive parsing."""
import json
import os
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Optional

from .cache import DiskCache

SERPAPI_URL = "https://serpapi.com/search.json"


@dataclass
class ScholarResult:
    position: int
    title: str
    snippet: str
    venue: str          # publication_info.summary (authors - journal, year - host)
    year: Optional[int]
    cited_by: int
    link: str
    result_type: Optional[str]  # "Book", "Pdf", "Html" or None
    cites_id: Optional[str]


def _year(summary: str) -> Optional[int]:
    years = re.findall(r"\b((?:19|20)\d{2})\b", summary or "")
    return int(years[-1]) if years else None


def parse_scholar(data: dict) -> list:
    """Parse a SerpApi google_scholar response. Tolerates missing fields."""
    out = []
    for i, r in enumerate(data.get("organic_results", []), start=1):
        summary = (r.get("publication_info") or {}).get("summary", "")
        cited = ((r.get("inline_links") or {}).get("cited_by") or {})
        out.append(ScholarResult(
            position=r.get("position", i),
            title=r.get("title", ""),
            snippet=r.get("snippet", ""),
            venue=summary,
            year=_year(summary),
            cited_by=cited.get("total", 0) or 0,
            link=r.get("link", ""),
            result_type=r.get("type"),
            cites_id=cited.get("cites_id"),
        ))
    return out


def search_scholar(query: str, api_key: Optional[str] = None,
                   cache: Optional[DiskCache] = None, **extra) -> list:
    """Search Google Scholar via SerpApi. Cached responses cost 0 credits."""
    params = {"engine": "google_scholar", "q": query, "hl": "en", **extra}
    cache = cache or DiskCache()
    data = cache.get(params)
    if data is None:
        key = api_key or os.environ.get("SERPAPI_API_KEY")
        if not key:
            raise RuntimeError("Set SERPAPI_API_KEY (serpapi.com/manage-api-key)")
        url = SERPAPI_URL + "?" + urllib.parse.urlencode({**params, "api_key": key})
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        cache.set(params, data)
    return parse_scholar(data)

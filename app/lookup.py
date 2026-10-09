"""Official check: what official sites say about the organisation a caller claims to be.

Privacy (RULES.md): only the organisation's name leaves Ringproof, never the transcript, memory or
the user's details. Trust: results come only from official domains. Phone numbers are never
taken from search text (a wrong number is worse than none); the number to call comes from
policy.NATIONAL_HELPLINE. The call never waits for this: it runs beside the risk checks.
"""

import logging
import re
import time
from typing import Protocol
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel

from app.config import settings

log = logging.getLogger("ringproof.lookup")

# Suffixes match subdomains too (Tavily include_domains, checked Oct 8: crpf.gov.in, nhrc.nic.in).
OFFICIAL_DOMAINS = ["gov.in", "nic.in", "rbi.org.in", "npci.org.in"]
CACHE_TTL_S = 24 * 3600
SNIPPET_CHARS = 220


class Source(BaseModel):
    title: str
    url: str
    snippet: str


class OrgCheck(BaseModel):
    org: str
    sources: list[Source]


class Lookup(Protocol):
    name: str

    async def check(self, org: str) -> OrgCheck: ...


def is_official(url: str) -> bool:
    parts = urlparse(url)
    if parts.scheme not in ("http", "https"):  # the URL becomes a link on screen
        return False
    host = (parts.hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in OFFICIAL_DOMAINS)


def clean_snippet(text: str) -> str:
    """Strip markdown, collapse whitespace, cut at a word (search snippets are often page fragments)."""
    text = re.sub(r"[#*_>|`]+", " ", text)  # markdown left over from the page
    text = re.sub(r"^\s*(?:[^›]{0,60}›\s*)+", "", text)  # leading breadcrumb: "Home › Media › "
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= SNIPPET_CHARS:
        return text
    return text[:SNIPPET_CHARS].rsplit(" ", 1)[0] + "…"


class TavilyLookup:
    name = "tavily"
    URL = "https://api.tavily.com/search"

    def __init__(self, api_key: str, timeout_s: float = 15.0) -> None:
        self.api_key = api_key
        self.timeout_s = timeout_s
        self._cache: dict[str, tuple[float, OrgCheck]] = {}  # per process; Redis when scaled out

    async def check(self, org: str) -> OrgCheck:
        key = org.strip().lower()
        hit = self._cache.get(key)
        if hit and time.monotonic() - hit[0] < CACHE_TTL_S:
            return hit[1]
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            res = await client.post(
                self.URL,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "query": f"{org} phone call scam warning",
                    "max_results": 3,
                    "search_depth": "basic",
                    "include_domains": OFFICIAL_DOMAINS,
                },
            )
            res.raise_for_status()
        result = OrgCheck(org=org, sources=[
            Source(title=r["title"], url=r["url"], snippet=clean_snippet(r.get("content", "")))
            for r in res.json().get("results", [])
            if is_official(r["url"])  # double check: never show a non-official page
        ])
        self._cache[key] = (time.monotonic(), result)
        return result


class NoLookup:
    """Used when no Tavily key is set: the official check shows only the built-in helpline."""

    name = "off"

    async def check(self, org: str) -> OrgCheck:
        return OrgCheck(org=org, sources=[])


_lookup: Lookup | None = None


def get_lookup() -> Lookup:
    global _lookup
    if _lookup is None:
        _lookup = TavilyLookup(settings.tavily_api_key) if settings.tavily_api_key else NoLookup()
        log.info("lookup: %s", _lookup.name)
    return _lookup

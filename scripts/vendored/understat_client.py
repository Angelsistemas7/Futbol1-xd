"""Unofficial client for Understat's internal `getLeagueData` JSON endpoint.

Confirmed live 2026-07-16: unlike FBref (which returned a straight HTTP 403 to
a plain `urllib` request, and still returned a Cloudflare "Just a moment..."
challenge page even through `cloudscraper` — real xG scraping there would need
a full headless browser, a much heavier dependency this project doesn't carry
yet), Understat's data endpoint answers a plain request with no JS challenge
at all, as long as it's asked for like the site's own frontend asks for it:
  - `X-Requested-With: XMLHttpRequest` and a `Referer` matching the league page
    — a request without both was rejected with a 404 (confirmed live).
  - The response body is gzip-compressed regardless of whether an
    `Accept-Encoding` header was sent — must be decompressed manually since
    `urllib` (unlike `requests`) does not do this automatically.

This is still an internal, undocumented endpoint (no contract, no key) — same
unofficial/best-effort posture as infrastructure/scraping/bing_sports/, not a
published API.
"""
from __future__ import annotations

import gzip
import json
import urllib.parse
import urllib.request
from typing import Callable

_BASE_URL = "https://understat.com/getLeagueData"
_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

Transport = Callable[[str, str], dict]


def _default_transport(url: str, referer: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": _USER_AGENT,
            "X-Requested-With": "XMLHttpRequest",
            "Referer": referer,
        },
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        raw = response.read()
        if response.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        return json.loads(raw.decode("utf-8"))


class UnderstatClient:
    def __init__(self, transport: Transport = _default_transport):
        self._transport = transport

    def get_league_data(self, league: str, season_year: int) -> dict:
        """`league` is Understat's own slug — confirmed live for the 5 major
        European leagues: "EPL", "La liga", "Bundesliga", "Serie A", "Ligue 1".
        `season_year` is the season's start year (e.g. 2025 for 2025/26)."""
        url = f"{_BASE_URL}/{urllib.parse.quote(league)}/{season_year}"
        referer = f"https://understat.com/league/{urllib.parse.quote(league.replace(' ', '_'))}/{season_year}"
        return self._transport(url, referer)

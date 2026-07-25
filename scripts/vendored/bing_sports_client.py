"""Unofficial scraper for Bing's public sports pages (bing.com/sportsdetails),
which server-render match schedules and minute-by-minute event timelines from
SportRadar-licensed data — confirmed live 2026-07-12: a plain GET with a normal
browser User-Agent returns the full match data with no JavaScript execution
needed (no headless browser required).

This is NOT a documented API — there is no contract, no key, and the markup can
change without notice. Treat it as best-effort and personal-use only:
  - It never feeds the prediction model (see application/use_cases/generate_prediction.py) —
    only the live-view event timeline display, which is honestly labeled
    "sin conectar" without it.
  - infrastructure/scraping/bing_sports/translator.py is pinned against real
    saved HTML fixtures (tests/unit/fixtures/bing_sports/) specifically so a
    breaking markup change fails a test loudly instead of failing silently in
    production.
  - Bing's Terms of Use restrict automated scraping of their pages. This adapter
    exists for a single user's personal, non-commercial use (viewing real match
    events next to our own predictions) — it is not for redistribution or at
    any scale beyond that.
"""
from __future__ import annotations

import urllib.parse
import urllib.request
from typing import Callable

_BASE_URL = "https://www.bing.com/sportsdetails"
_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

Transport = Callable[[str], str]


def _default_transport(url: str) -> str:
    request = urllib.request.Request(
        url, headers={"User-Agent": _USER_AGENT, "Accept-Language": "es-ES,es;q=0.9"}
    )
    # One immediate retry — confirmed live on 2026-07-15: an isolated request
    # can drop (connection reset) and succeed on the very next attempt with no
    # delay needed. Cuts down on user-visible "no events" blips that would
    # otherwise wait for the next 15s poll to self-correct.
    last_error: Exception | None = None
    for _ in range(2):
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                return response.read().decode("utf-8", errors="replace")
        except Exception as exc:
            last_error = exc
    raise last_error


class BingSportsClient:
    def __init__(self, transport: Transport = _default_transport):
        self._transport = transport

    def get_schedule_html(
        self, league: str, season_year: int, timezone_id: str = "SA Pacific Standard Time",
        iana_timezone_id: str = "America/Bogota", iso_timezone_key: str = "COT",
    ) -> str:
        params = {
            "q": "resultados", "league": league, "scenario": "League", "intent": "Schedule",
            "sport": "Soccer", "TimezoneId": timezone_id, "IANATimezoneId": iana_timezone_id,
            "ISOTimezoneKey": iso_timezone_key, "seasonyear": season_year,
            "segment": "sports", "isl2": "true", "form": "ARENL2",
        }
        return self._transport(f"{_BASE_URL}?{urllib.parse.urlencode(params)}")

    def get_stats_html(
        self, league: str, season_year: int, timezone_id: str = "SA Pacific Standard Time",
        iana_timezone_id: str = "America/Bogota", iso_timezone_key: str = "COT",
    ) -> str:
        """The tournament-wide leaders page (top scorers, assists, cards) —
        `intent=Stats`, a different intent from the schedule/match-detail pages
        above but the same base URL and query shape."""
        params = {
            "q": "estadisticas", "league": league, "scenario": "League", "intent": "Stats",
            "sport": "Soccer", "TimezoneId": timezone_id, "IANATimezoneId": iana_timezone_id,
            "ISOTimezoneKey": iso_timezone_key, "seasonyear": season_year,
            "segment": "sports", "isl2": "true", "form": "ARENL2",
        }
        return self._transport(f"{_BASE_URL}?{urllib.parse.urlencode(params)}")

    def get_match_detail_html(self, detail_query_string: str) -> str:
        """`detail_query_string` is the query string extracted verbatim from a
        schedule entry's own link (see translator.parse_schedule) — it already
        carries the gameid/team/venueid parameters Bing requires; a query built
        from team names alone returns 400 Bad Request (confirmed live).

        The string comes from an HTML attribute (BeautifulSoup already decoded
        entities like `&quot;` back to literal `"`), so it is NOT URL-safe as-is
        — spaces and quotes in it raise `InvalidURL` in Python's http.client even
        though a real browser tolerates them. Re-encode every value, leaving `&`
        and `=` as the structural delimiters."""
        encoded = "&".join(
            f"{k}={urllib.parse.quote(v, safe='')}"
            for pair in detail_query_string.split("&") if pair
            for k, _, v in [pair.partition("=")]
        )
        return self._transport(f"{_BASE_URL}?{encoded}")

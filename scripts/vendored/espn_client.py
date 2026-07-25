"""Unofficial scraper for ESPN's public `site.api.espn.com` JSON endpoints —
confirmed live 2026-07-20: a plain GET with a normal browser User-Agent returns
full scoreboard/boxscore JSON, no key, no account, no JavaScript execution.

This is NOT a documented API — there is no contract, no key, and the JSON shape
can change without notice, same caution as infrastructure/scraping/bing_sports/.
Treat it as best-effort and personal-use only: ESPN's Terms of Use restrict
automated access to their site; this adapter exists for a single user's
personal, non-commercial use, not for redistribution or at any scale beyond that.

Two things confirmed live that aren't obvious from ESPN's own docs (there are
none):
  - `scoreboard` truncates to 100 events per request UNLESS `limit` is passed
    explicitly (confirmed: a full Champions League season query returned exactly
    100 events without `limit`, 189 — the real count — with `limit=1000`). Every
    call below always passes a generous limit for this reason.
  - `dates` accepts a `YYYYMMDD-YYYYMMDD` range, not just a single day.
"""
from __future__ import annotations

import urllib.parse
import urllib.request
from typing import Callable

_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer"
_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
_SCOREBOARD_LIMIT = 1000

Transport = Callable[[str], str]


def _default_transport(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(request, timeout=15) as response:
        return response.read().decode("utf-8", errors="replace")


class ESPNClient:
    def __init__(self, transport: Transport = _default_transport):
        self._transport = transport

    def get_scoreboard_json(self, sport_path: str, date_from: str, date_to: str) -> str:
        """`sport_path` is ESPN's own competition slug (e.g. "uefa.champions",
        "eng.1", "fifa.world" — there is no published list; each one used by
        this project was confirmed live against a real request). `date_from`/
        `date_to` are "YYYYMMDD"."""
        params = {"dates": f"{date_from}-{date_to}", "limit": _SCOREBOARD_LIMIT}
        return self._transport(f"{_BASE_URL}/{sport_path}/scoreboard?{urllib.parse.urlencode(params)}")

    def get_summary_json(self, sport_path: str, event_id: str) -> str:
        params = {"event": event_id}
        return self._transport(f"{_BASE_URL}/{sport_path}/summary?{urllib.parse.urlencode(params)}")

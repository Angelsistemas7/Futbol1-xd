"""Unofficial client for WorldFootball.net's per-competition referee stats page.

Confirmed live 2026-07-16: a plain `urllib` GET with a normal browser
User-Agent gets a real 200 for the actual page (`/competition/{slug}/referees/`)
— same "cheap and simple" category as Bing/Understat/Transfermarkt/BBC, not
FBref. Two guessed URLs did fail with non-200s first (`/referee/{name}/` was
404, `/search/?q=` was 403) — the real path was only found by following the
site's own "Referees" nav link in a real browser, not guessed from a URL
pattern; don't assume a WorldFootball URL works before confirming it live.
"""
from __future__ import annotations

import urllib.request
from typing import Callable

_BASE_URL = "https://www.worldfootball.net"
_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

Transport = Callable[[str], str]


def _default_transport(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT, "Referer": _BASE_URL + "/"})
    with urllib.request.urlopen(request, timeout=15) as response:
        return response.read().decode("utf-8", errors="replace")


class WorldFootballClient:
    def __init__(self, transport: Transport = _default_transport):
        self._transport = transport

    def get_referees_html(self, competition_path: str) -> str:
        """`competition_path` is the site's own path segment, e.g.
        "co139/fifa-world-cup" — confirmed live for the World Cup; verify a
        new competition's path the same way (follow its own "Referees" nav
        link) before assuming the pattern holds."""
        return self._transport(f"{_BASE_URL}/competition/{competition_path}/referees/")

"""Unofficial client for BBC Sport's public team pages.

Vendored verbatim from FutureSport's own
infrastructure/scraping/bbc_sport/client.py (see that file's docstring for why
this is unofficial/best-effort).
"""
from __future__ import annotations

import urllib.request
from typing import Callable

_BASE_URL = "https://www.bbc.com/sport/football/teams"
_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

Transport = Callable[[str], str]


def _default_transport(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT, "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(request, timeout=15) as response:
        return response.read().decode("utf-8", errors="replace")


class BBCSportClient:
    def __init__(self, transport: Transport = _default_transport):
        self._transport = transport

    def get_team_page_html(self, team_slug: str) -> str:
        return self._transport(f"{_BASE_URL}/{team_slug}")

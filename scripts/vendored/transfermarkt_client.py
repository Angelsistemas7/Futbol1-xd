"""Unofficial client for Transfermarkt's public suspensions/injuries page.

Vendored verbatim from FutureSport's own
infrastructure/scraping/transfermarkt/client.py (see that file's docstring for
why this is unofficial/best-effort, and why the slug+ID pairs used against it
are individually verified rather than guessed).
"""
from __future__ import annotations

import urllib.request
from typing import Callable

_BASE_URL = "https://www.transfermarkt.com"
_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

Transport = Callable[[str], str]


def _default_transport(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT, "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(request, timeout=15) as response:
        return response.read().decode("utf-8", errors="replace")


class TransfermarktClient:
    def __init__(self, transport: Transport = _default_transport):
        self._transport = transport

    def get_injuries_html(self, team_slug: str, team_id: int) -> str:
        return self._transport(f"{_BASE_URL}/{team_slug}/sperrenundverletzungen/verein/{team_id}")

"""Fetches raw HTML/JSON from 4 unofficial sports data sources on a schedule
(see ../.github/workflows/snapshot.yml) and writes them under ../data/ so a
separate private app (FutureSport) can read pre-fetched snapshots instead of
scraping live on every request. Runs on GitHub Actions' free unlimited minutes
for public repos.

Snapshots the RAW response, never a parsed/derived structure — this repo does
no parsing at all. The consumer owns the one real parser per source (already
tested there); this script's only job is "fetch the same thing the consumer's
client.py would fetch, and save it."

Deliberately best-effort per source: if one source fails, the others still
get committed, and a failing source's file is left at its last-good snapshot
rather than being overwritten with an error page (see `_write_if_ok`).
"""
from __future__ import annotations

import json
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "vendored"))

import competitions
from bing_sports_client import BingSportsClient
from espn_client import ESPNClient
from understat_client import UnderstatClient
from worldfootball_client import WorldFootballClient

DATA_DIR = Path(__file__).parent.parent / "data"
REQUEST_DELAY_SECONDS = 2.5  # personal-use pace, not a scraping burst — see README.

_bing = BingSportsClient()
_espn = ESPNClient()
_understat = UnderstatClient()
_worldfootball = WorldFootballClient()

_results: dict[str, str] = {}  # source name -> "ok" | "error: ..."


def _write_if_ok(relative_path: str, fetch) -> None:
    """Runs `fetch()` (returns str or dict); on success, writes it to
    DATA_DIR/relative_path (dicts as JSON, strings as-is) and records "ok".
    On any exception, records the error and leaves the existing file (if any)
    untouched — a transient failure should never clobber the last good
    snapshot with an error page."""
    try:
        value = fetch()
        path = DATA_DIR / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(value, (dict, list)):
            path.write_text(json.dumps(value), encoding="utf-8")
        else:
            path.write_text(value, encoding="utf-8")
        _results[relative_path] = "ok"
        print(f"[ok] {relative_path}")
    except Exception:
        _results[relative_path] = f"error: {traceback.format_exc(limit=1).strip().splitlines()[-1]}"
        print(f"[FAIL] {relative_path}: {_results[relative_path]}")
    time.sleep(REQUEST_DELAY_SECONDS)


def main() -> None:
    # World Cup — Bing Sports (schedule + top scorers) and WorldFootball (referees).
    _write_if_ok(
        "bing/wc_schedule.html",
        lambda: _bing.get_schedule_html(competitions.BING_LEAGUE, competitions.BING_SEASON_YEAR),
    )
    _write_if_ok(
        "bing/wc_stats.html",
        lambda: _bing.get_stats_html(competitions.BING_LEAGUE, competitions.BING_SEASON_YEAR),
    )
    _write_if_ok(
        "worldfootball/wc_referees.html",
        lambda: _worldfootball.get_referees_html(competitions.WORLDFOOTBALL_COMPETITION_PATH),
    )

    # ESPN-native competitions (Champions League, Liga MX, MLS, Brasileirão).
    for comp_code, cfg in competitions.ESPN_NATIVE_COMPETITIONS.items():
        _write_if_ok(
            f"espn/{comp_code}_schedule.json",
            lambda cfg=cfg: _espn.get_scoreboard_json(cfg["espn_sport_path"], cfg["espn_date_from"], cfg["espn_date_to"]),
        )

    # Domestic leagues via Understat (schedule + player season stats, one payload).
    for comp_code, cfg in competitions.UNDERSTAT_COMPETITIONS.items():
        _write_if_ok(
            f"understat/{comp_code}_league_data.json",
            lambda cfg=cfg: _understat.get_league_data(cfg["understat_slug"], cfg["season_year"]),
        )

    meta = {"generated_at": datetime.now(timezone.utc).isoformat(), "sources": _results}
    (DATA_DIR).mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"\ndone — {sum(1 for v in _results.values() if v == 'ok')}/{len(_results)} sources ok")


if __name__ == "__main__":
    main()

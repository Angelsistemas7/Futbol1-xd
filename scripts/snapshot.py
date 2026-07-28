"""Fetches raw HTML/JSON from unofficial sports data sources on a schedule
(see ../.github/workflows/snapshot.yml) and writes them under ../data/ so a
separate private app (FutureSport) can read pre-fetched snapshots instead of
scraping live on every request. Runs on GitHub Actions' free unlimited minutes
for public repos.

Snapshots the RAW response, never a parsed/derived structure — this repo does
no parsing at all, with ONE deliberate exception (see `_fetch_new_espn_summaries`
below: gzip is a compression transform, not a parse, but it's still a step up
from every other source here, done only because raw ESPN summary JSON runs
~470KB per match and this job accumulates hundreds of them over a season —
see README.md's "Per-match ESPN summaries" section for the size math that
justified this). The consumer owns the one real parser per source (already
tested there); this script's job is "fetch the same thing the consumer's
client.py would fetch, and save it."

Deliberately best-effort per source: if one source fails, the others still
get committed, and a failing source's file is left at its last-good snapshot
rather than being overwritten with an error page (see `_write_if_ok`).
"""
from __future__ import annotations

import gzip
import json
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "vendored"))

import competitions
from bbc_sport_client import BBCSportClient
from bing_sports_client import BingSportsClient
from espn_client import ESPNClient
from transfermarkt_client import TransfermarktClient
from understat_client import UnderstatClient
from worldfootball_client import WorldFootballClient

DATA_DIR = Path(__file__).parent.parent / "data"
REQUEST_DELAY_SECONDS = 2.5  # personal-use pace, not a scraping burst — see README.

# Per-match ESPN summaries are the expensive, high-value part of this job
# (posession/shots/corners/cards/lineups/goal events — everything the "more
# markets" and player-market features actually need, none of which the plain
# schedule snapshot below captures). A full season is hundreds of matches;
# fetching all of them in one run would blow well past a sane Actions job
# duration and hammer ESPN far harder than the "personal use" pace this
# project holds itself to everywhere else. So this is INCREMENTAL: a played
# match's summary never changes, so once a file exists for an event_id it is
# never re-fetched, and each run only spends its budget on matches that are
# still missing — the whole history fills in gradually across many runs,
# same "accumulates over time, no need to raise the cap" reasoning already
# used for FutureSport's own Champions League goalscorer backfill
# (_MAX_EVENTS_FETCHES, interfaces/api/app.py).
_MAX_NEW_SUMMARIES_PER_RUN = 25

_bing = BingSportsClient()
_espn = ESPNClient()
_understat = UnderstatClient()
_worldfootball = WorldFootballClient()
_transfermarkt = TransfermarktClient()
_bbc = BBCSportClient()

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


def _completed_event_ids(schedule_json_path: Path) -> list[str]:
    """Minimal, targeted read of just `id` and `status.type.completed` from a
    previously-saved ESPN scoreboard JSON — deliberately not importing
    FutureSport's own full translator (this repo has zero dependency on
    FutureSport's private code, see README.md)."""
    if not schedule_json_path.exists():
        return []
    try:
        data = json.loads(schedule_json_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    ids = []
    for event in data.get("events", []):
        comps = event.get("competitions") or []
        if not comps:
            continue
        completed = bool(comps[0].get("status", {}).get("type", {}).get("completed"))
        if completed and event.get("id"):
            ids.append(event["id"])
    return ids


def _fetch_new_espn_summaries() -> None:
    """Tops up data/espn/{comp_code}/summary_{event_id}.json.gz for every
    completed match that doesn't have one on disk yet, capped at
    _MAX_NEW_SUMMARIES_PER_RUN new fetches for this run, split into an even
    per-competition sub-budget (oldest-listed-first within each competition).

    The per-competition split matters in practice, not just in theory:
    confirmed live 2026-07-27 with a real run — Champions League alone had
    more than 25 missing summaries backlogged (its 2025-26 season just
    finished), so a single shared pool consumed in competition order left
    Liga MX/MLS/Brasileirao — the leagues actually in season right now —
    completely starved until UCL's backlog cleared, which at 25/run could
    have taken days. Splitting the budget evenly means every competition
    makes some progress every run instead of one hogging it."""
    comp_items = list(competitions.ESPN_NATIVE_COMPETITIONS.items())
    per_comp_budget = max(1, _MAX_NEW_SUMMARIES_PER_RUN // len(comp_items))
    total_fetched = 0
    for comp_code, cfg in comp_items:
        schedule_path = DATA_DIR / f"espn/{comp_code}_schedule.json"
        summaries_dir = DATA_DIR / "espn" / comp_code
        fetched_this_comp = 0
        for event_id in _completed_event_ids(schedule_path):
            if fetched_this_comp >= per_comp_budget:
                break
            out_path = summaries_dir / f"summary_{event_id}.json.gz"
            if out_path.exists():
                continue
            rel = f"espn/{comp_code}/summary_{event_id}.json.gz"
            try:
                raw = _espn.get_summary_json(cfg["espn_sport_path"], event_id)
                summaries_dir.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(gzip.compress(raw.encode("utf-8")))
                _results[rel] = "ok"
                print(f"[ok] {rel}")
            except Exception:
                _results[rel] = f"error: {traceback.format_exc(limit=1).strip().splitlines()[-1]}"
                print(f"[FAIL] {rel}: {_results[rel]}")
            fetched_this_comp += 1
            total_fetched += 1
            time.sleep(REQUEST_DELAY_SECONDS)
    print(f"espn summaries: {total_fetched} new this run, "
          f"budget was {_MAX_NEW_SUMMARIES_PER_RUN} ({per_comp_budget}/competition)")


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

    # World Cup national teams — Transfermarkt (injuries) + BBC Sport (news),
    # the same 8 teams FutureSport itself has verified IDs/slugs for (see
    # competitions.py — never guessed, extend both places together).
    for team_name, (slug, team_id) in competitions.TRANSFERMARKT_TEAM_IDS.items():
        _write_if_ok(
            f"transfermarkt/{slug}_injuries.html",
            lambda slug=slug, team_id=team_id: _transfermarkt.get_injuries_html(slug, team_id),
        )
    for team_name in competitions.TRANSFERMARKT_TEAM_IDS:
        bbc_slug = competitions.bbc_slug(team_name)
        _write_if_ok(
            f"bbc/{bbc_slug}_news.html",
            lambda bbc_slug=bbc_slug: _bbc.get_team_page_html(bbc_slug),
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

    # Per-match ESPN detail (stats/lineups/goal events) — the rich data, run
    # last and after the fresh schedules above so it sees this run's newest
    # completed matches, not last run's. See _fetch_new_espn_summaries's own
    # docstring for the incremental/capped/gzip reasoning.
    _fetch_new_espn_summaries()

    meta = {"generated_at": datetime.now(timezone.utc).isoformat(), "sources": _results}
    (DATA_DIR).mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"\ndone — {sum(1 for v in _results.values() if v == 'ok')}/{len(_results)} sources ok")


if __name__ == "__main__":
    main()

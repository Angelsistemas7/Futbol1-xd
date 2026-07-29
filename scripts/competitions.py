"""Competition config for the snapshot job — mirrors FutureSport's own
`_COMPETITIONS` dict (futuresport/interfaces/api/app.py). Keep these two in
sync by hand: if a comp_code, espn_sport_path, understat_slug, or season_year
changes on the FutureSport side, update it here too, or the snapshot for that
competition will silently go stale (the consumer falls back to a live scrape
in that case, so nothing breaks — it just stops getting the free-Actions-minutes
benefit for that one competition until this file catches up).
"""
from __future__ import annotations

# World Cup: Bing Sports is canonical (schedule + group standings + top scorers).
BING_LEAGUE = "Soccer_InternationalWorldCup"
BING_SEASON_YEAR = 2026

# WorldFootball: World Cup referee tendency stats.
WORLDFOOTBALL_COMPETITION_PATH = "co139/fifa-world-cup"

# ESPN-native competitions: ESPN's own scoreboard IS the canonical schedule.
ESPN_NATIVE_COMPETITIONS = {
    "ucl": {"espn_sport_path": "uefa.champions", "espn_date_from": "20250701", "espn_date_to": "20260630"},
    "liga_mx": {"espn_sport_path": "mex.1", "espn_date_from": "20260101", "espn_date_to": "20261231"},
    "mls": {"espn_sport_path": "usa.1", "espn_date_from": "20260101", "espn_date_to": "20261231"},
    "brasileirao": {"espn_sport_path": "bra.1", "espn_date_from": "20260101", "espn_date_to": "20261231"},
}

# The World Cup and the 5 domestic leagues below: Bing/Understat are still the
# CANONICAL fixture source for these (see BING_LEAGUE/UNDERSTAT_COMPETITIONS),
# this is only a supplementary ESPN schedule so this job can discover event_ids
# to backfill the same rich per-match summaries (stats/lineups/events/odds) it
# already saves for the 4 espn_native competitions above. FutureSport already
# fetches these same sport_paths live for exactly this reason (real stats for
# every competition, not just espn_native ones, matched by team name via
# normalize_team_name) - this just lets that same data get backfilled from a
# snapshot instead of a live request. Mirrors futuresport's own
# `_COMPETITIONS` espn_sport_path/date values exactly (2026-07-29).
ESPN_SUPPLEMENTARY_COMPETITIONS = {
    "wc": {"espn_sport_path": "fifa.world", "espn_date_from": "20260601", "espn_date_to": "20260720"},
    "la_liga": {"espn_sport_path": "esp.1", "espn_date_from": "20250801", "espn_date_to": "20260630"},
    "epl": {"espn_sport_path": "eng.1", "espn_date_from": "20250801", "espn_date_to": "20260630"},
    "bundesliga": {"espn_sport_path": "ger.1", "espn_date_from": "20250801", "espn_date_to": "20260630"},
    "serie_a": {"espn_sport_path": "ita.1", "espn_date_from": "20250801", "espn_date_to": "20260630"},
    "ligue_1": {"espn_sport_path": "fra.1", "espn_date_from": "20250801", "espn_date_to": "20260630"},
}

# Domestic leagues: Understat is canonical (schedule + player season stats).
UNDERSTAT_COMPETITIONS = {
    "la_liga": {"understat_slug": "La liga", "season_year": 2025},
    "epl": {"understat_slug": "EPL", "season_year": 2025},
    "bundesliga": {"understat_slug": "Bundesliga", "season_year": 2025},
    "serie_a": {"understat_slug": "Serie A", "season_year": 2025},
    "ligue_1": {"understat_slug": "Ligue 1", "season_year": 2025},
}

# World Cup national teams — Transfermarkt (slug, team_id) pairs mirrored
# verbatim from FutureSport's own
# infrastructure/scraping/transfermarkt/injury_provider.py._TEAM_IDS. Do NOT
# add a team here by guessing the slug/ID pattern — a guessed Transfermarkt ID
# has silently returned the WRONG team's page before (see that file's
# docstring). Only extend this after verifying a new pair live and copying it
# into both places by hand.
TRANSFERMARKT_TEAM_IDS: dict[str, tuple[str, int]] = {
    "Spain": ("spanien", 3375),
    "Argentina": ("argentinien", 3437),
    "Barcelona": ("fc-barcelona", 131),
    "France": ("frankreich", 3377),
    "Morocco": ("marokko", 3575),
    "Belgium": ("belgien", 3382),
    "Norway": ("norwegen", 3440),
    "England": ("england", 3299),
    "Switzerland": ("schweiz", 3384),
}

# Same World Cup team set for BBC Sport — slug is normally lowercase-hyphenate,
# with overrides mirrored from
# infrastructure/scraping/bbc_sport/news_provider.py._SLUG_OVERRIDES. Reuses
# the same team-name keys as TRANSFERMARKT_TEAM_IDS above so both snapshot
# steps iterate the exact same verified team list.
BBC_SLUG_OVERRIDES = {
    "United States": "usa",
}


def bbc_slug(team_name: str) -> str:
    return BBC_SLUG_OVERRIDES.get(team_name, team_name.lower().replace(" ", "-"))

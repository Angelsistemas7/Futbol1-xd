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

# Domestic leagues: Understat is canonical (schedule + player season stats).
UNDERSTAT_COMPETITIONS = {
    "la_liga": {"understat_slug": "La liga", "season_year": 2025},
    "epl": {"understat_slug": "EPL", "season_year": 2025},
    "bundesliga": {"understat_slug": "Bundesliga", "season_year": 2025},
    "serie_a": {"understat_slug": "Serie A", "season_year": 2025},
    "ligue_1": {"understat_slug": "Ligue 1", "season_year": 2025},
}

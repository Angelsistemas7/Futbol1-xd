# Futbol1-xd

Scheduled data-snapshot pipeline for [FutureSport](https://github.com/Angelsistemas7/futuresport)
(a private repo). Every 20 minutes, a GitHub Actions job in this **public** repo
(public repos get unlimited free Actions minutes) fetches raw HTML/JSON schedule,
standings, and season-stats pages from a handful of unofficial, undocumented
football data sources, and commits them under [`data/`](data/).

FutureSport reads those files first and falls back to fetching the same sources
live, exactly as it always has, whenever a snapshot is missing, stale, or fails
to parse — this repo is a pure optimization (saves FutureSport its own request
volume and Actions minutes), never a hard dependency.

## What's here

- `scripts/vendored/` — verbatim copies of FutureSport's own HTTP client modules
  (`infrastructure/scraping/*/client.py`) for Bing Sports, ESPN's undocumented
  JSON API, Understat, and WorldFootball.net. Kept as plain copies, not a shared
  package, so this repo has zero dependency on FutureSport's private repo.
- `scripts/competitions.py` — which competitions/leagues to fetch. Mirrors
  FutureSport's own competition config; update both by hand if one changes.
- `scripts/snapshot.py` — fetches every source and writes raw responses to
  `data/`. Never parses anything — parsing stays FutureSport's job, so there is
  exactly one parser per source, not two copies that can drift apart.
- `data/` — committed by the workflow, not by hand. `data/meta.json` records
  when each source last succeeded.

## Not an API

None of the 4 sources are official/documented APIs — they're the same pages a
browser would load, fetched with a normal User-Agent. No key, no contract, no
guarantee the shape won't change. This exists for one person's personal,
non-commercial use (a hobby prediction dashboard), fetched at a deliberately
low, personal-use pace (one pass every 20 minutes, ~2.5s between requests
within a pass) — not for redistribution or any larger scale.

# Futbol1-xd

Scheduled data-snapshot pipeline for [FutureSport](https://github.com/Angelsistemas7/futuresport)
(a private repo). Every 20 minutes, a GitHub Actions job in this **public** repo
(public repos get unlimited free Actions minutes) fetches raw HTML/JSON schedule,
standings, season-stats, injury, news, and per-match detail pages from a handful
of unofficial, undocumented football data sources, and commits them under
[`data/`](data/).

FutureSport reads those files first and falls back to fetching the same sources
live, exactly as it always has, whenever a snapshot is missing, stale, or fails
to parse — this repo is a pure optimization (saves FutureSport its own request
volume and Actions minutes), never a hard dependency. It's also the durable
historical record: FutureSport itself only keeps what it needs for the current
prediction (a short-TTL in-memory/pickle cache), so this repo's git history —
one commit per source per run in which that source's content actually changed
— is the only place that data survives across weeks/months for future,
richer-than-today modeling.

## What's here

- `scripts/vendored/` — verbatim copies of FutureSport's own HTTP client modules
  (`infrastructure/scraping/*/client.py`) for Bing Sports, ESPN's undocumented
  JSON API, Understat, WorldFootball.net, Transfermarkt, and BBC Sport. Kept as
  plain copies, not a shared package, so this repo has zero dependency on
  FutureSport's private repo.
- `scripts/competitions.py` — which competitions/leagues/teams to fetch.
  Mirrors FutureSport's own competition config and team ID/slug maps; update
  both by hand if one changes. The Transfermarkt/BBC team list is deliberately
  the same *individually verified* 9-team World Cup set FutureSport itself
  uses — never guessed (see that file's docstring for why a guessed
  Transfermarkt ID silently returns the WRONG team's page).
- `scripts/snapshot.py` — fetches every source and writes raw responses to
  `data/`. Never *parses* anything — parsing stays FutureSport's job, so there
  is exactly one parser per source, not two copies that can drift apart. One
  deliberate exception to "never transforms the data": per-match ESPN
  summaries are gzip-compressed before being written (see "Per-match ESPN
  summaries" below for why).
- `data/` — committed by the workflow, not by hand. `data/meta.json` records
  when each source last succeeded (or its error, if it failed that run).

## Per-match ESPN summaries — the expensive, high-value part

`data/espn/{comp_code}/summary_{event_id}.json.gz` holds ESPN's full per-match
payload (possession/shots/corners/cards/lineups/goal events, everything
FutureSport's "more markets" and player-market features need) for the 4
ESPN-native competitions (Champions League, Liga MX, MLS, Brasileirão).

Two things make this different from every other source here:

1. **Incremental, not refetched every run.** A played match's summary never
   changes, so once a file exists for an `event_id` it's never re-fetched.
   Each run only spends its budget (`_MAX_NEW_SUMMARIES_PER_RUN` in
   `snapshot.py`, currently 25, split evenly across the 4 competitions so one
   competition's backlog can't starve the others) on matches still missing —
   the full history fills in gradually across many runs. Confirmed live
   2026-07-27: Champions League alone had a backlog bigger than the whole
   budget (its season just ended), so the even per-competition split exists
   specifically so Liga MX/MLS/Brasileirão (in-season right now) still make
   progress every run instead of waiting for UCL's backlog to clear first.
2. **Gzip-compressed**, the one exception to "never transforms the data"
   above. A raw summary is ~470 KB; with 4 competitions and hundreds of
   matches per season, saving them uncompressed would run this repo into the
   hundreds of MB. Gzip is a ~12x reduction (confirmed live: 470 KB → ~35-40
   KB) with zero information loss — still the exact raw ESPN response, just
   compressed, so FutureSport's own parser can read it after
   `gzip.decompress()` with no format changes needed on its side.

**Known gap, not fixed this pass:** this only covers the 4 ESPN-native
competitions, using event IDs already known from their own schedule snapshot.
FutureSport separately cross-references World Cup and the 5 Understat-domestic-
league matches against ESPN's scoreboard by team name (`_match_stats_or_none`
in `interfaces/api/app.py`) to get the same rich stats for those competitions
too — reproducing that name-matching logic here would be real duplicated
complexity, so those two categories still only get live-fetched, never
snapshotted. Revisit only if that gap turns out to matter in practice.

## Not an API

None of these sources are official/documented APIs — they're the same pages a
browser would load, fetched with a normal User-Agent. No key, no contract, no
guarantee the shape won't change. This exists for one person's personal,
non-commercial use (a hobby prediction dashboard), fetched at a deliberately
low, personal-use pace (2.5s between requests within a pass) — not for
redistribution or any larger scale.

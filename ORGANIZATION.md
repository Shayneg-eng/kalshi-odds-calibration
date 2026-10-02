# Kalshi Sports Odds Calibration Project — Directory Layout

Goal: Does a pre-game "60% to win" price on Kalshi actually correspond to a ~60% real win
rate? Plus: how did the in-game price evolve over the course of each game?

## Layout

```
kalshi_sports_odds/
├── ORGANIZATION.md      <- this file. Update if the structure changes.
├── PROGRESS.md          <- running, timestamped log of work done. Update after every
│                           meaningful step (don't wait until the end).
├── data/
│   ├── nfl/
│   │   ├── events/       <- raw event-list JSON pulls (which games exist, by week/season)
│   │   ├── markets/      <- one JSON file per game market: pregame price, final result,
│   │   │                    metadata (teams, date, close time, settlement)
│   │   └── candlesticks/ <- one JSON/CSV file per game: full intraday price history
│   │                        (timestamp, yes_bid/ask, price) from open to settlement
│   ├── nba/  <- same sub-structure as nfl/, added once NFL is complete
│   └── (other sports added the same way if/when we expand breadth)
├── scripts/              <- python helpers: fetch/parse/aggregate/analyze. Re-runnable,
│                            not one-off scratch — kept because we'll re-run them as more
│                            data comes in.
├── analysis/             <- final output: calibration tables/charts, per-game price-path
│                            charts, the write-up.
└── logs/                 <- raw fetch logs / error logs from the pull process (not the
                              data itself — just what-happened-when for debugging pulls).
```

## Conventions

- Sport scope: NFL and NBA are being done **completely** first (depth-first, per user's
  choice). **Update (2026-09-20): "past 2 seasons" turned out to be infeasible.** Kalshi's
  public/non-trading price-history endpoints only retain data for roughly the last several
  weeks. The accessible NFL sample is 79 games, Aug 6 – Sep 20 2026. NBA is currently
  **entirely inaccessible** via this method — its most recent season ended outside the live
  retention window and the next season hasn't started. `data/nba/` is left empty/unused for
  now; see PROGRESS.md's 2026-09-20 entry for the full explanation. Other sports not yet
  attempted; same ceiling will apply.
- Market files are named by Kalshi's own ticker (e.g. `KXNFLGAME-26SEP20INDKC-KC.json`) so
  they're traceable back to the source game.
- Candlestick files are named the same way, suffixed `_candles`.
- Data is pulled via the browser, from Kalshi's own public, unauthenticated data endpoints
  (the same ones the kalshi.com website itself loads to render odds/charts) — never via the
  Kalshi trading/account API or MCP tools, and never while authenticated. See PROGRESS.md
  for the exact endpoints found.

# Kalshi Sports Odds Calibration — Findings (NFL, Aug 6 - Sep 20, 2026)

## The question

If Kalshi prices a team at ~60% to win before a game, how often does that team actually win?
And how does the market's price react as the game itself plays out?

## Important scope note — read this first

The original plan was "past 2 seasons, all major sports Kalshi lists." That turned out to be
infeasible: Kalshi's public, non-trading data endpoints (the only ones usable without logging
in or trading) only retain market and price-history data for roughly the last several weeks.
Anything older comes back empty, even though the game itself is real and the event still
appears in Kalshi's own settled-events listing.

Practical result:
- **NFL**: 79 games, Aug 6 - Sep 20, 2026 (2026 preseason + the first ~2-3 weeks of the 2026
  regular season). This is the entire NFL sample currently reachable this way.
- **NBA**: not reachable at all right now. The most recently completed NBA season ended
  before the accessible retention window begins, and the next season hasn't started yet — so
  there is no NBA data on the accessible side of that window as of today.
- Other sports were not attempted, since the same retention ceiling will apply to them too.

None of this is a bug or something retried its way out of — it's a real limit of what's
publicly exposed outside the trading API. Full technical detail is in `PROGRESS.md` at the
project root.

## Methodology notes

- **"Pregame" price** isn't an exact pre-kickoff snapshot — Kalshi's public API doesn't expose
  a kickoff timestamp anywhere. It's defined here as the price of the first hourly candle on
  the game's calendar day: a "morning-of" proxy. On a normal game day this should be close to
  the true pregame price, but it can be several hours removed from actual kickoff, especially
  for early-window vs. primetime games.
- **Tie/void games** (NFL preseason games that end tied, which settle both sides at $0.50) are
  excluded from the win-rate calibration rather than counted as a win or loss. 1 such game is
  in this sample (`KXNFLGAME-26AUG13INDNE`).
- **In-game price paths** are 1-minute candlesticks resampled to 5-minute points, covering a
  4-hour window ending at game settlement (game-end, not kickoff — Kalshi's API gives no
  separate kickoff field). This comfortably covers a full game including overtime, but the
  early portion of the window can include pregame time for games shorter than 4 hours.

## Calibration result

79 games / 158 team-sides. The one tied/void game contributes 2 rows, both excluded as
`result: "scalar"`, leaving 156 usable rows for the calibration buckets below. See
`calibration_table.md` for the exact bucketed table and `calibration_summary.json` for the
machine-readable version.

Headline: the bucketed actual win rates track the diagonal (predicted = actual) reasonably
well across the middle of the range (40-70% predicted), which is where almost all of the
sample sits. The extreme buckets (10-20%, 80-90%) have only 2 games each, so they're not
statistically meaningful on their own — a single upset in a 2-game bucket swings the "actual
rate" by 50 points. With a 79-game sample concentrated in the middle probabilities, this is
consistent with, but does not strongly prove, good calibration — a much larger sample
(ideally spanning full seasons, once more weeks accumulate inside Kalshi's retention window)
would be needed to say more confidently.

See `calibration_chart.png` for the visual (marker size = sample size per bucket).

## In-game price behavior

See `ingame_sample_grid.png` for a representative sample of price paths (picked to span the
full range of in-game volatility, not cherry-picked for the best story). Patterns visible in
the data:
- Some games are nearly flat all the way to the final minutes, then snap to 0 or 1 at
  settlement (e.g. a comfortable win that stays comfortable).
- Others swing dramatically and even fully invert — see `KXNFLGAME-26AUG20LVHOU`, where Las
  Vegas's implied win probability dropped from ~53% pregame to under 5% mid-game before
  rallying to nearly 100% by the end (LV won).
- Preseason games in particular showed more mid-game noise than the price stability you'd
  expect from a market with real stakes — consistent with lower liquidity/volume in
  preseason markets.

## Files

- `calibration_table.md` — bucketed win-rate-vs-predicted table (human-readable)
- `calibration_summary.json` — same data, machine-readable
- `calibration_chart.png` — predicted vs. actual scatter with diagonal reference line
- `ingame_sample_grid.png` — 9 illustrative in-game price paths spanning the volatility range
- Underlying data: `../data/nfl/markets/nfl_pregame_calibration.json`,
  `../data/nfl/candlesticks/nfl_ingame_charts_part{1,2}.json`
- Full technical log: `../PROGRESS.md`

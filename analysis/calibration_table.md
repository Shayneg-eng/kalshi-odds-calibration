# Kalshi Pregame Calibration — NFL

Sample: 158 team-sides (79 games), 4 excluded as tie/void (`result: "scalar"`).

**Caveat on "pregame":** Kalshi's public API does not expose an exact kickoff timestamp. `pregame_prob` here is the price of the first hourly candle on the game's calendar day (a "morning-of" proxy), not the price at the moment of kickoff. Treat this as directionally informative, not exact.

**Caveat on sample window:** Kalshi's non-trading data endpoints only retain recent history. This sample covers Aug 6 - Sep 20, 2026 (2026 NFL preseason + first ~2-3 weeks of the regular season) — not the "past 2 seasons" originally hoped for. Small per-bucket sample sizes below should be read with that in mind.

| Predicted prob. bucket | Avg. predicted | Games (n) | Wins | Actual win rate | Predicted - Actual |
|---|---|---|---|---|---|
| 10-20% | 14% | 2 | 1 | 50% | -36% |
| 20-30% | 26% | 9 | 4 | 44% | -19% |
| 30-40% | 36% | 26 | 9 | 35% | +1% |
| 40-50% | 44% | 40 | 21 | 52% | -8% |
| 50-60% | 56% | 40 | 19 | 48% | +8% |
| 60-70% | 64% | 27 | 17 | 63% | +1% |
| 70-80% | 75% | 8 | 5 | 62% | +12% |
| 80-90% | 86% | 2 | 1 | 50% | +36% |

# Is there money on the table? — Edge analysis on the Kalshi NFL dataset

Short answer up front: **nothing in this dataset rises to a trustworthy, tradeable edge.**
The sample (79 games, mostly preseason) is too small and too dominated by preseason noise to
bet real money on any single number below. That said, here's everything I checked and what it
actually shows, including one pattern worth watching as more data comes in.

## 1. Calibration split by preseason vs. regular season

The original report noted that underdogs (<50% priced) won somewhat more than their price
implied, and favorites somewhat less, across the full 79-game sample. Splitting that by
season type tells a more interesting — and contradictory — story:

**Preseason (49 games / 98 rows):** underdogs (avg priced 41%) actually won **55%** of the
time; favorites (avg priced 59%) won only **45%**. Underdogs meaningfully outperformed their
price.

**Regular season (30 games / 60 rows):** the pattern *flips*. Underdogs (avg priced 34%) won
only **30%** of the time; favorites (avg priced 66%) won **70%**. Favorites outperformed
their price.

That regular-season flip is actually consistent with the well-documented "favorite-longshot
bias" found in most sports betting markets historically — bettors tend to overvalue longshots
and undervalue favorites, so favorites are, on average, slightly underpriced. If that holds up
with more data, the naive takeaway would be "lean toward favorites, fade extreme underdogs" —
**but 30 games is nowhere near enough to act on.** A single blowout upset or two would erase
this. It's also not monotonic within the regular-season bucket breakdown (60-70% favorites
overperformed a lot, 70-80% and 80-90% favorites actually *underperformed* their price), which
is more consistent with noise than a clean, exploitable effect.

**Most likely explanation for the preseason pattern going the other way:** backup players,
teams resting starters, coaches optimizing for roster evaluation rather than winning, and much
thinner trading volume/liquidity in preseason markets. That's a real, structural reason
preseason odds could be less reliable — but it's also a reason *not* to trade preseason games
even if the pattern is real, since it's driven by unpredictable coaching decisions (who plays,
for how long) more than skill differences.

## 2. The vig (cost of trading)

Checking both sides of each of the 79 games at the same "morning-of" snapshot: the two team
prices summed to essentially exactly $1.00 on average (no meaningful under- or over-round).
This means Kalshi's own spread on NFL game markets is very thin — good news in the sense that
the "vig tax" isn't the obstacle here; the obstacle is not having a real edge to overcome it
with in the first place.

## 3. In-game overreaction / mean-reversion

I checked every ≥15-percentage-point, 5-minute price swing across all 79 games (86 such moves)
and looked at what happened in the following 15 minutes: does the market partially reverse the
move (suggesting a tradeable overreaction), or keep going?

Result: swings mostly **kept going or stayed put** — only 27% showed meaningful reversion,
49% continued in the same direction, and the rest were roughly flat. On average, big swings
showed a *slight continuation* bias, not reversion. In plain terms: big in-game price moves in
this sample were mostly the market correctly re-pricing a real event (a turnover, a score),
not an overreaction you could fade. There's no evidence here of a "the market always
overreacts to X, fade it" pattern — and even if there were, a human reacting to a 15-minute-old
price move is already trading on stale information.

## Bottom line

- No robust, statistically defensible edge in this dataset as it stands.
- The one pattern worth tracking: regular-season favorites (especially in the 55-70% priced
  range) modestly outperforming their price, consistent with known favorite-longshot bias in
  sports betting broadly — but on 30 games, this could easily be noise, and it wasn't even
  consistent across all favorite sub-buckets.
- Preseason games look mispriced in the *opposite* direction, but for reasons (backup
  players, low liquidity) that argue against trading them rather than for it.
- The vig is thin, so if a real edge existed it wouldn't get eaten by trading costs — but
  that's moot without an edge to begin with.
- **Honest recommendation:** don't trade on this data yet. If you want a real answer, the
  useful next step is letting more regular-season weeks accumulate (Kalshi's retention window
  is rolling, so in a few more weeks there will be 100+ regular-season games instead of 30)
  and re-running `scripts/edge_analysis.py` against the larger sample — it's already built to
  just re-run as the dataset grows.

This is a statistical read of historical data, not financial or betting advice, and none of
these patterns are validated or guaranteed to persist.

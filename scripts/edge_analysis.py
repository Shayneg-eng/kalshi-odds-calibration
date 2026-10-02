#!/usr/bin/env python3
"""
Edge-finding analysis on the Kalshi NFL dataset (79 games, Aug 6 - Sep 20 2026).

This looks for statistically visible mispricings/patterns in:
  1. Calibration by season segment (preseason vs regular season) - is the
     "underdogs win more than priced" pattern seen in the full-sample
     calibration driven by preseason noise, or does it hold in the regular
     season too?
  2. The vig/overround - how much the two sides of each game cost together,
     which is the real hurdle any "edge" has to clear.
  3. In-game overreaction/reversion - after a big short-window price swing,
     does the market tend to partially revert (overreaction, tradeable) or
     keep drifting (underreaction/momentum, tradeable the other way)?

All findings are descriptive statistics on a small (79-game) sample. This
is NOT a validated trading strategy and is not financial advice - see the
caveats printed at the end of each section.

Re-runnable: safe to re-run as more games accumulate.
"""
import json
import os
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAL_PATH = os.path.join(BASE, "data", "nfl", "markets", "nfl_pregame_calibration.json")
CANDLE_DIR = os.path.join(BASE, "data", "nfl", "candlesticks")
OUT_DIR = os.path.join(BASE, "analysis")


def load_calibration():
    with open(CAL_PATH) as f:
        return json.load(f)


def load_candles():
    games = []
    for fname in ("nfl_ingame_charts_part1.json", "nfl_ingame_charts_part2.json"):
        with open(os.path.join(CANDLE_DIR, fname)) as f:
            games.extend(json.load(f))
    return games


# ---------------------------------------------------------------------------
# 1. Calibration by season segment
# ---------------------------------------------------------------------------

def bucket_calibration(rows, bucket_size=0.10):
    buckets = defaultdict(list)
    for r in rows:
        if r["result"] == "scalar":
            continue
        p = r["pregame_prob"]
        lower = min(int(p // bucket_size) * bucket_size, 1.0 - bucket_size if p < 1.0 else p)
        buckets[round(lower, 2)].append(r)
    out = []
    for lower in sorted(buckets.keys()):
        rs = buckets[lower]
        n = len(rs)
        wins = sum(1 for r in rs if r["result"] == "yes")
        out.append({
            "bucket": f"{int(lower*100)}-{int((lower+0.10)*100)}%",
            "n": n,
            "avg_predicted": round(sum(r["pregame_prob"] for r in rs) / n, 3),
            "actual_win_rate": round(wins / n, 3),
        })
    return out


def section_1_season_split(rows):
    print("\n" + "=" * 70)
    print("1. CALIBRATION BY SEASON SEGMENT")
    print("=" * 70)
    preseason = [r for r in rows if r["kickoff_day"] < "2026-09-01"]
    regular = [r for r in rows if r["kickoff_day"] >= "2026-09-01"]
    print(f"\nPreseason: {len(preseason)//2} games, {len(preseason)} team-sides")
    for row in bucket_calibration(preseason):
        diff = row["actual_win_rate"] - row["avg_predicted"]
        print(f"  {row['bucket']:>8}  n={row['n']:<3} predicted={row['avg_predicted']:.0%}  "
              f"actual={row['actual_win_rate']:.0%}  actual-predicted={diff:+.0%}")

    print(f"\nRegular season: {len(regular)//2} games, {len(regular)} team-sides")
    for row in bucket_calibration(regular):
        diff = row["actual_win_rate"] - row["avg_predicted"]
        print(f"  {row['bucket']:>8}  n={row['n']:<3} predicted={row['avg_predicted']:.0%}  "
              f"actual={row['actual_win_rate']:.0%}  actual-predicted={diff:+.0%}")

    # Aggregate "below 50% priced" vs "above 50% priced" over/underperformance,
    # split by segment - this is the cleanest single test of the
    # "underdogs outperform their price" pattern seen in the full sample.
    for label, subset in [("Preseason", preseason), ("Regular season", regular)]:
        usable = [r for r in subset if r["result"] != "scalar"]
        dogs = [r for r in usable if r["pregame_prob"] < 0.5]
        favs = [r for r in usable if r["pregame_prob"] >= 0.5]
        def rate(rs):
            return sum(1 for r in rs if r["result"] == "yes") / len(rs) if rs else None
        def avg_p(rs):
            return sum(r["pregame_prob"] for r in rs) / len(rs) if rs else None
        print(f"\n  {label} — underdogs (<50% priced): n={len(dogs)}, "
              f"avg priced={avg_p(dogs):.1%}, actual win rate={rate(dogs):.1%}" if dogs else "")
        print(f"  {label} — favorites (>=50% priced): n={len(favs)}, "
              f"avg priced={avg_p(favs):.1%}, actual win rate={rate(favs):.1%}" if favs else "")

    print("\n  CAVEAT: preseason games involve backup players, unusual coaching")
    print("  incentives (resting starters, evaluating roster bubble players), and")
    print("  much lower trading volume/liquidity than regular-season markets --")
    print("  any 'underdogs beat their price' effect concentrated there may not")
    print("  transfer to the regular season, where it matters for real money.")


# ---------------------------------------------------------------------------
# 2. Vig / overround - the real cost of any edge
# ---------------------------------------------------------------------------

def section_2_vig(rows):
    print("\n" + "=" * 70)
    print("2. VIG / OVERROUND PER GAME")
    print("=" * 70)
    by_event = defaultdict(list)
    for r in rows:
        by_event[r["event_ticker"]].append(r)

    overrounds = []
    for event, rs in by_event.items():
        if len(rs) == 2:
            total = sum(r["pregame_prob"] for r in rs)
            overrounds.append(total)

    avg_overround = sum(overrounds) / len(overrounds)
    print(f"\n  Games with both sides present: {len(overrounds)}")
    print(f"  Average (side A price + side B price): {avg_overround:.3f}")
    print(f"  Implied average vig: {(avg_overround - 1) * 100:+.1f} cents per $1 pair")
    under_1 = sum(1 for o in overrounds if o < 1.0)
    over_1 = sum(1 for o in overrounds if o > 1.0)
    print(f"  Games where the two sides summed to < $1.00 (arbitrage-shaped gap): {under_1}")
    print(f"  Games where the two sides summed to > $1.00 (normal vig): {over_1}")
    print("\n  CAVEAT: this uses the 'morning-of' proxy price for both sides on the same")
    print("  day, not simultaneous quotes, so small gaps here are a rough signal, not a")
    print("  confirmed real-time arbitrage - by the time you could act, the quotes will")
    print("  have moved. It DOES tell you the ballpark cost of the vig you're fighting.")


# ---------------------------------------------------------------------------
# 3. In-game overreaction / reversion
# ---------------------------------------------------------------------------

def section_3_reversion(games, move_threshold=0.15, window_after=3):
    print("\n" + "=" * 70)
    print("3. IN-GAME OVERREACTION / MEAN-REVERSION AFTER BIG SWINGS")
    print("=" * 70)
    print(f"\n  Definition: a 'big swing' = a >= {move_threshold:.0%} move in implied probability")
    print(f"  between two consecutive 5-min candles. We then check the next")
    print(f"  {window_after} candles ({window_after*5} min) to see whether price partially")
    print(f"  reverts back toward the pre-swing level (overreaction), or keeps moving")
    print(f"  the same direction (continuation/momentum).")

    reversions = []
    continuations = []
    flats = []
    examples = []

    for g in games:
        if g["result"] == "scalar":
            continue
        candles = g["candles_5min"]
        for i in range(1, len(candles) - window_after):
            prev_p = candles[i - 1][1]
            cur_p = candles[i][1]
            move = cur_p - prev_p
            if abs(move) < move_threshold:
                continue
            future_p = candles[i + window_after][1]
            # how much of the move was retraced (reversion) vs extended (continuation)
            retraced = (cur_p - future_p) / move if move != 0 else 0
            entry = {
                "ticker": g["ticker"],
                "event_ticker": g["event_ticker"],
                "minute": candles[i][0],
                "prev_p": prev_p,
                "cur_p": cur_p,
                "future_p": future_p,
                "move": round(move, 3),
                "retraced_fraction": round(retraced, 3),
            }
            if retraced > 0.25:
                reversions.append(entry)
            elif retraced < -0.10:
                continuations.append(entry)
            else:
                flats.append(entry)

    total = len(reversions) + len(continuations) + len(flats)
    print(f"\n  Total big-swing events found: {total}")
    if total:
        print(f"  -> Partially/fully reverted (>25% retraced): {len(reversions)} "
              f"({len(reversions)/total:.0%})")
        print(f"  -> Continued/extended further (<-10% retraced, i.e. kept moving): "
              f"{len(continuations)} ({len(continuations)/total:.0%})")
        print(f"  -> Roughly flat after (in between): {len(flats)} ({len(flats)/total:.0%})")

        avg_retrace = sum(e["retraced_fraction"] for e in (reversions + continuations + flats)) / total
        print(f"\n  Average retraced fraction across ALL big-swing events: {avg_retrace:.2f}")
        print("  (0 = no reversion at all, on average price keeps going; ")
        print("   1 = swings fully reverse on average within 15 min)")

    print("\n  CAVEAT: this pools every 5-minute swing across all 79 games, most of")
    print("  which are large in-game win-probability swings driven by real plays")
    print("  (turnovers, scores) that mechanically move a team closer to winning/losing")
    print("  - most 'moves' here are the market correctly re-pricing a real change in")
    print("  win probability, not mispricing. A move that later revents can just mean")
    print("  the team that scored then gave it right back, not that the market")
    print("  overreacted. This is a description of what happened, not a proven,")
    print("  tradeable edge (and by the time a human read a 15-min-old price move,")
    print("  it's already stale).")

    return reversions, continuations


def main():
    rows = load_calibration()
    games = load_candles()

    section_1_season_split(rows)
    section_2_vig(rows)
    reversions, continuations = section_3_reversion(games)

    print("\n" + "=" * 70)
    print("BOTTOM LINE")
    print("=" * 70)
    print("""
  On this sample, the only pattern that shows up with any consistency is
  "underdogs (priced under 50%) win somewhat more often than their price
  implies, favorites somewhat less" - but it's concentrated in the
  preseason subsample (49 of 79 games), where illiquid markets and backup
  players are the more likely explanation, not a real, exploitable
  inefficiency. The regular-season-only subsample (30 games) is too small
  to draw a conclusion from on its own.

  There is no in-game pattern here reliable enough to trade on with this
  sample size - swings mostly reflect real, correctly-priced changes in
  win probability from live game events, not detectable overreaction.

  This is NOT investment/betting advice, and 79 games (most of them
  preseason) is not enough data to safely bet money on any pattern found
  here. If you want a real answer to "is there money on the table,"
  the honest next step is accumulating several hundred regular-season
  games (i.e. revisiting this once more weeks fall inside Kalshi's
  retention window) before trusting any of these numbers with real stakes.
""")


if __name__ == "__main__":
    main()

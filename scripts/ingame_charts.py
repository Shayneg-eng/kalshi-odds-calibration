#!/usr/bin/env python3
"""
Generate illustrative in-game price-path charts from the candlestick data.

Input: data/nfl/candlesticks/nfl_ingame_charts_part1.json
       data/nfl/candlesticks/nfl_ingame_charts_part2.json
       (79 games total, 5-minute-resampled price paths over a 240-min window
        ending at game_end; x-axis = minutes since window start, i.e. roughly
        "4 hours before game-end" -> "game-end")

Output: analysis/ingame_sample_grid.png - a 3x3 grid of varied example games
        (picked for variety: blowout, nailbiter, upset/big-swing, tie) so the
        user can see how odds reacted during play, not just the final calibration
        number.

Re-runnable.
"""
import json
import os
import random

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANDLE_DIR = os.path.join(BASE, "data", "nfl", "candlesticks")
OUT_DIR = os.path.join(BASE, "analysis")
os.makedirs(OUT_DIR, exist_ok=True)


def load_all_games():
    games = []
    for fname in ("nfl_ingame_charts_part1.json", "nfl_ingame_charts_part2.json"):
        with open(os.path.join(CANDLE_DIR, fname)) as f:
            games.extend(json.load(f))
    return games


def pick_examples(games, k=9):
    """Pick a variety: some low-volatility/blowout, some high-swing nailbiters,
    a comeback/upset, and a tie if present — for a representative, non-cherry-picked
    illustrative grid, sorted by total price movement (range) to get a spread."""
    def total_swing(g):
        prices = [p for _, p in g["candles_5min"]]
        return max(prices) - min(prices) if prices else 0

    scalars = [g for g in games if g["result"] == "scalar"]
    others = [g for g in games if g["result"] != "scalar"]
    others_sorted = sorted(others, key=total_swing)

    picks = []
    if scalars:
        picks.append(scalars[0])
    # spread across the swing distribution: lowest, a few middles, highest
    n = len(others_sorted)
    idxs = sorted(set([0, n // 6, n // 3, n // 2, 2 * n // 3, 5 * n // 6, n - 1]))
    for i in idxs:
        if len(picks) >= k:
            break
        picks.append(others_sorted[i])
    return picks[:k]


def write_grid(games):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    examples = pick_examples(games, k=9)
    fig, axes = plt.subplots(3, 3, figsize=(14, 12))
    axes = axes.flatten()

    for ax, g in zip(axes, examples):
        xs = [m for m, _ in g["candles_5min"]]
        ys = [p for _, p in g["candles_5min"]]
        color = {"yes": "#16a34a", "no": "#dc2626", "scalar": "#6b7280"}.get(g["result"], "#333")
        ax.plot(xs, ys, color=color, linewidth=1.6)
        ax.axhline(g["pregame_prob"], color="gray", linestyle=":", linewidth=1, alpha=0.7)
        ax.set_ylim(0, 1)
        result_label = {"yes": "WON", "no": "LOST", "scalar": "TIE/VOID"}.get(g["result"], g["result"])
        ax.set_title(f"{g['team']}\n{g['event_ticker']}\npregame {g['pregame_prob']:.0%} -> {result_label}",
                      fontsize=9)
        ax.set_xlabel("min. before game-end", fontsize=8)
        ax.set_ylabel("implied prob.", fontsize=8)
        ax.tick_params(labelsize=7)

    fig.suptitle("Kalshi In-Game Price Paths — Illustrative Sample\n"
                  "(dotted line = morning-of pregame price; window = ~4hrs before game-end -> game-end)",
                  fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    path = os.path.join(OUT_DIR, "ingame_sample_grid.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def main():
    games = load_all_games()
    path = write_grid(games)
    print(f"Wrote {path} from {len(games)} games")


if __name__ == "__main__":
    main()

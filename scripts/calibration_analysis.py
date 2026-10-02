#!/usr/bin/env python3
"""
Calibration analysis: does a Kalshi pregame price of X% actually correspond
to an X% real win rate?

Input:  data/nfl/markets/nfl_pregame_calibration.json
          - 158 rows (79 games x 2 team-sides)
          - each row: {event_ticker, ticker, team, result, status,
                        kickoff_day, game_end, pregame_prob}
          - result: "yes" (won), "no" (lost), "scalar" (tie/void -> excluded)

Output: analysis/calibration_table.md   (markdown table, bucketed)
        analysis/calibration_chart.png  (predicted vs actual scatter + diagonal)
        analysis/calibration_summary.json (machine-readable summary)

Re-runnable: safe to re-run any time the underlying dataset grows.
"""
import json
import os
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN_PATH = os.path.join(BASE, "data", "nfl", "markets", "nfl_pregame_calibration.json")
OUT_DIR = os.path.join(BASE, "analysis")
os.makedirs(OUT_DIR, exist_ok=True)


def load_rows():
    with open(IN_PATH) as f:
        rows = json.load(f)
    return rows


def bucket_rows(rows, bucket_size=0.10):
    """Bucket by pregame_prob into bucket_size-wide bins, e.g. 0.10 -> deciles.
    Excludes result == 'scalar' (ties/voids)."""
    buckets = defaultdict(list)
    excluded = 0
    for r in rows:
        if r["result"] == "scalar":
            excluded += 1
            continue
        p = r["pregame_prob"]
        # bucket label = lower edge of the bin, e.g. 0.30 covers [0.30, 0.40)
        lower = min(int(p // bucket_size) * bucket_size, 1.0 - bucket_size if p < 1.0 else p)
        lower = round(lower, 2)
        buckets[lower].append(r)
    return buckets, excluded


def summarize(buckets):
    out = []
    for lower in sorted(buckets.keys()):
        rs = buckets[lower]
        n = len(rs)
        wins = sum(1 for r in rs if r["result"] == "yes")
        actual_rate = wins / n if n else None
        avg_pred = sum(r["pregame_prob"] for r in rs) / n if n else None
        # simple 95% CI via normal approx (Wilson would be better for small n, noted as caveat)
        out.append({
            "bucket_lower": lower,
            "bucket_upper": round(lower + 0.10, 2),
            "n": n,
            "wins": wins,
            "actual_win_rate": round(actual_rate, 3) if actual_rate is not None else None,
            "avg_predicted_prob": round(avg_pred, 3) if avg_pred is not None else None,
        })
    return out


def write_markdown_table(summary, excluded, total_rows):
    lines = []
    lines.append("# Kalshi Pregame Calibration — NFL")
    lines.append("")
    lines.append(f"Sample: {total_rows} team-sides ({total_rows // 2} games), "
                  f"{excluded} excluded as tie/void (`result: \"scalar\"`).")
    lines.append("")
    lines.append("**Caveat on \"pregame\":** Kalshi's public API does not expose an exact "
                  "kickoff timestamp. `pregame_prob` here is the price of the first hourly "
                  "candle on the game's calendar day (a \"morning-of\" proxy), not the price "
                  "at the moment of kickoff. Treat this as directionally informative, not exact.")
    lines.append("")
    lines.append("**Caveat on sample window:** Kalshi's non-trading data endpoints only "
                  "retain recent history. This sample covers Aug 6 - Sep 20, 2026 (2026 NFL "
                  "preseason + first ~2-3 weeks of the regular season) — not the \"past 2 "
                  "seasons\" originally hoped for. Small per-bucket sample sizes below should "
                  "be read with that in mind.")
    lines.append("")
    lines.append("| Predicted prob. bucket | Avg. predicted | Games (n) | Wins | Actual win rate | Predicted - Actual |")
    lines.append("|---|---|---|---|---|---|")
    for row in summary:
        n = row["n"]
        pred = row["avg_predicted_prob"]
        actual = row["actual_win_rate"]
        diff = round(pred - actual, 3) if (pred is not None and actual is not None) else None
        bucket_label = f"{int(row['bucket_lower']*100)}-{int(row['bucket_upper']*100)}%"
        lines.append(
            f"| {bucket_label} | {pred:.0%} | {n} | {row['wins']} | "
            f"{actual:.0%} | {diff:+.0%} |"
        )
    md = "\n".join(lines) + "\n"
    path = os.path.join(OUT_DIR, "calibration_table.md")
    with open(path, "w") as f:
        f.write(md)
    return path


def write_chart(summary):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    xs = [row["avg_predicted_prob"] for row in summary]
    ys = [row["actual_win_rate"] for row in summary]
    ns = [row["n"] for row in summary]

    fig, ax = plt.subplots(figsize=(7, 7))
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Perfect calibration")
    sizes = [max(n * 15, 40) for n in ns]
    ax.scatter(xs, ys, s=sizes, alpha=0.75, color="#2563eb", edgecolor="white", zorder=3)
    for x, y, n in zip(xs, ys, ns):
        ax.annotate(f"n={n}", (x, y), textcoords="offset points", xytext=(6, 6), fontsize=8, color="#444")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Kalshi pregame (morning-of) implied probability")
    ax.set_ylabel("Actual win rate")
    ax.set_title("Kalshi NFL Pregame Price Calibration\n(Aug 6 - Sep 20, 2026, n=79 games)")
    ax.legend(loc="upper left")
    ax.set_aspect("equal")
    fig.tight_layout()
    path = os.path.join(OUT_DIR, "calibration_chart.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def main():
    rows = load_rows()
    buckets, excluded = bucket_rows(rows)
    summary = summarize(buckets)

    table_path = write_markdown_table(summary, excluded, len(rows))
    chart_path = write_chart(summary)

    summary_out = {
        "total_rows": len(rows),
        "excluded_scalar": excluded,
        "buckets": summary,
    }
    summary_path = os.path.join(OUT_DIR, "calibration_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary_out, f, indent=2)

    print(f"Wrote {table_path}")
    print(f"Wrote {chart_path}")
    print(f"Wrote {summary_path}")
    for row in summary:
        print(row)


if __name__ == "__main__":
    main()

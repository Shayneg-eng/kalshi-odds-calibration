# Kalshi Sports Odds Calibration

A data-analysis study of **prediction-market calibration** on
[Kalshi](https://kalshi.com) sports markets.

## The questions

1. **Calibration** — when Kalshi prices a team at ~60% to win pre-game, do they actually win
   about 60% of the time? (A well-calibrated market should.)
2. **In-game dynamics** — how did each market's price evolve over the course of the game as the
   result unfolded?

Scope was depth-first: NFL and NBA analyzed completely first, other sports added as time allowed
(see [`PROGRESS.md`](PROGRESS.md) for the running log and [`ORGANIZATION.md`](ORGANIZATION.md)
for the directory contract).

## Scripts

| File | Role |
|---|---|
| `scripts/calibration_analysis.py` | Bucket pre-game prices and compare to realized win rates |
| `scripts/edge_analysis.py` | Look for systematic mispricing / exploitable edges |
| `scripts/ingame_charts.py` | Reconstruct intraday price trajectories per game |

## Results

Pre-generated outputs live in `analysis/`:

- `calibration_table.md` / `calibration_summary.json` / `calibration_chart.png` — calibration results
- `EDGE_ANALYSIS.md` — edge findings
- `ingame_sample_grid.png` — sample in-game price trajectories

## Data

Raw market pulls live under `data/`. Re-run the scripts to regenerate everything in `analysis/`.

## Run it

```bash
python -m pip install pandas numpy matplotlib
python scripts/calibration_analysis.py
python scripts/ingame_charts.py
```

> Analysis of historical market behavior only — not betting or investment advice.

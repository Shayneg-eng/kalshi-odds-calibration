# Progress Log — Kalshi Sports Odds Calibration Project

Format: timestamp (America/New_York), what was done, what was learned/decided, what's next.
Kept updated continuously, not just at the end.

---

### 2026-09-20 — Kickoff & scoping

- User's question: if Kalshi prices a team at ~60% to win pre-game, how often do they
  actually win? Plus: capture the full intraday price chart for each game to see how odds
  reacted as the game played out. Wants everything saved in an organized, analyzable way.
- Clarified with user:
  - Sport scope: **all major sports**, but prioritized **depth-first** — NFL and NBA done
    completely first, other sports added afterward only if time allows.
  - History: past ~2 seasons.
  - In-game charts: every game in the sample (not just a subset).
  - Method: user initially said "use browser use, not the API." Clarified further and got
    explicit approval to use Kalshi's own **public, unauthenticated, non-trading JSON
    endpoints** (the same data the website itself loads to render odds/charts), accessed
    by navigating the browser to them — never the Kalshi trading/account API, never the
    `kalshi_mcp` tool, never logged in. This is necessary for scale: doing this purely by
    reading rendered pixels for thousands of games isn't feasible in one session.

### 2026-09-20 — Technical discovery (browser network inspection)

- Used Claude in Chrome to browse kalshi.com/sports and open an individual NFL game market
  page (IND Colts vs KC Chiefs, Sep 20 2026).
- Game market page URL pattern:
  `https://kalshi.com/markets/{series_ticker}/{slug}/{event_ticker}`
  e.g. `kxnflgame/professional-football-game/kxnflgame-26sep20indkc`
- Captured (via `read_network_requests`) the underlying public data call the page makes:
  `GET https://api.elections.kalshi.com/v1/cached/markets_by_ticker/{MARKET_TICKER}`
  → returns JSON with pregame/current price, volume, open/close dates, settlement result,
  team metadata. Confirmed this loads with no auth (fetched directly by navigating a tab to
  the URL — plain 200 JSON, no login wall).
- Still need to find (next step): the **candlestick/price-history endpoint** for the
  intraday chart, and the **event/series listing endpoint** to enumerate all past games
  (rather than clicking through the UI one game at a time). Will find both by opening a
  settled/historical game's page and watching network requests while interacting with the
  chart's time-range controls.
- Project directory created at `~/kalshi_sports_odds/` (see ORGANIZATION.md).

**Next steps:**
1. Find candlestick + event-listing endpoints.
2. Build a small fetch pipeline (likely via `javascript_tool` running `fetch()` inside the
   kalshi.com page context, to batch requests instead of one browser navigation per game).
3. Pull full NFL game list for ~past 2 seasons, then NBA.
4. For each game: pregame price snapshot + final result + full candlestick history.
5. Compute win-rate-by-pregame-price-bucket (the calibration question) and save per-game
   price-path charts.
6. Write up findings.

### 2026-09-20 — Endpoint discovery, methodology, and the data-retention wall

**Endpoints found (all public, unauthenticated, non-trading; accessed by browser navigation
and in-page `fetch()` — never `kalshi_mcp`, never logged in):**

- `GET https://api.elections.kalshi.com/v1/cached/markets_by_ticker/{TICKER}` — legacy/cached
  snapshot. Works even for old/archived markets, but has no price history, only a snapshot
  (last price, previous-day price, settlement result).
- `GET https://api.elections.kalshi.com/trade-api/v2/events?series_ticker=X&status=settled&limit=200&cursor=...`
  — paginated listing of settled events for a series (`KXNFLGAME`, `KXNBAGAME`). Cursor-based
  pagination. Note: `status=finalized` is rejected (400 bad_request); `status=settled` is correct.
- `GET https://api.elections.kalshi.com/trade-api/v2/markets?event_ticker=X` — the (usually 2)
  team-markets for one event. Fields used: `ticker`, `result` (`"yes"`/`"no"`/`"scalar"` for a
  tied/void game), `status`, `occurrence_datetime`, `open_time`, `close_time`, `yes_sub_title`
  (team name), `rules_primary`/`rules_secondary`.
- `GET https://api.elections.kalshi.com/trade-api/v2/series/{series_ticker}/markets/{ticker}/candlesticks?start_ts=...&end_ts=...&period_interval=...`
  (interval in minutes — 1, 60, or 1440) — the actual price-history endpoint. Returns
  `{candlesticks: [{end_period_ts, price: {open_dollars, close_dollars, high_dollars,
  low_dollars, mean_dollars, previous_dollars}, yes_bid: {...}, yes_ask: {...}, volume_fp,
  open_interest_fp}]}`.

**Gotcha — `occurrence_datetime` is GAME END, not kickoff.** Kalshi's market objects don't
expose an exact kickoff time anywhere. Initial attempts to sample "the last price before
occurrence_datetime" as the pregame price were nonsense — that's essentially the final,
already-settled price. **Adopted definition instead:** `pregame_prob` = the price of the
first available hourly (`period_interval=60`) candle on the event's calendar day (the date
is parsed straight out of the ticker, e.g. `26SEP20` → `2026-09-20T00:00:00Z`), i.e. a
"morning-of" proxy, not a true pre-kickoff snapshot. This is a real methodological
approximation and is called out as such in the final write-up.

**Hard constraint discovered — data retention window.** The `trade-api/v2/markets` and
`.../candlesticks` endpoints only return data for *recent* events. Empirically: everything
with a kickoff on/after **2026-08-06** returned real data; every 2025-season NFL game (and
effectively the entire NBA 2024-25 and 2025-26 seasons, both of which ended before the
accessible window) returned `markets: []` (0 markets) or a 404 on candlesticks — even though
the event still appears in the `events?status=settled` listing, tagged with the tell-tale
`"last_updated_ts":"0001-01-01T00:00:00Z"`. The `v1/cached/markets_by_ticker` endpoint still
returns a final-result snapshot for old tickers, but never price history. This is NOT a bug
on my end and isn't fixable by retrying, changing headers, etc. — it's an actual limitation
of what Kalshi's public/non-trading surface exposes. Ruled out "hypothetical/placeholder
bracket event" as the sole explanation (confirmed real, played, regular-season 2025 games —
e.g. `KXNFLGAME-25SEP14DENIND`, Denver at Indianapolis — hit the exact same 0-markets wall).

**Consequence — scope reduction from the original plan:**
- NFL: instead of "past 2 seasons," the accessible sample is **79 games, Aug 6 – Sep 20 2026**
  (2026 preseason + first ~2-3 weeks of the 2026 regular season). Kalshi's NFL series only
  goes back to mid-2025 in the first place, and only the last several weeks are inside the
  live retention window.
- NBA: **not obtainable via this method at all right now.** The most recent completed NBA
  season ended in mid-2026, before the 2026-09-20 "now," but the *accessible* window only
  reaches back to ~2026-08-06 — so literally no NBA games (recent or otherwise) fall inside
  it as of today. Will need to be revisited once the 2026-27 NBA season is underway and has
  settled games inside the same rolling window.
- Other sports (MLB, etc.): not yet attempted; same retention-window ceiling will apply.
- **This is being surfaced directly to the user in-chat, not just logged here.**

**Final NFL dataset produced:**
- `data/nfl/markets/nfl_pregame_calibration.json` — 158 rows (79 games × 2 team-sides). Shape:
  `{event_ticker, ticker, team, result, status, kickoff_day, game_end, pregame_prob}`.
  A few rows have `result: "scalar"` (NFL preseason ties, settle both sides at $0.50) and are
  excluded from the win-rate calibration, not treated as a win or loss.
- `data/nfl/candlesticks/nfl_ingame_charts_part1.json` + `..._part2.json` — all 79 games' full
  in-game price paths, split into two 40/39-game files (browser JS-context extraction had to
  be done in two batches). Shape per game:
  `{ticker, event_ticker, team, result, pregame_prob, candles_5min: [[minuteOffset, price], ...]}`.
  Fetched as 1-minute candles over `[game_end - 240min, game_end + 5min]` (4-hour buffer to
  safely cover a full game incl. overtime), then resampled to one point per 5 minutes to keep
  the payload manageable. `minuteOffset` is minutes since the start of that 240-minute window,
  not clock time — 0 is 4 hours before game-end, ~240 is game-end.

**Technique notes (for reproducibility):**
- Bulk-extracting JSON out of the browser's JS context: `javascript_tool`'s return value
  truncates hard at ~700-800 chars regardless of actual size. Workaround: write the JSON into
  a DOM node (`document.getElementById('datadump').textContent = JSON.stringify(data)`) and
  read it back with `get_page_text` (works up to ~50,000 chars). `read_page` does NOT work for
  this — it collapses large text nodes into short truncated labels even with a large
  `max_chars`.
- Network URLs with query strings get redacted (`[BLOCKED: Cookie/query string data]`) in tool
  output — had to strip query strings before logging/returning URLs from in-page JS, and
  ultimately just constructed the known-good candlestick URL directly rather than relying on
  sniffed traffic.
- Used in-page `<a>` link clicks (SPA client-side routing) instead of the `navigate` tool when
  I needed to preserve injected `window.*` state across "page views" — `navigate` does a hard
  reload and wipes it.
- Moderate concurrency (4-6 workers, ~60ms stagger) with retry/backoff on 429s kept the fetch
  pipeline reliable against Kalshi's rate limiting.

**Status at this point:** both candlestick files and the full pregame-calibration dataset are
saved to disk. Analysis (win-rate-by-bucket calibration table + chart, sample in-game price
plots) and the final write-up are the remaining work — see bottom of this file for live status.

**Next steps:**
1. ~~Build the calibration analysis~~ **DONE.**
2. ~~Generate a calibration chart~~ **DONE.**
3. Tell the user plainly about the scope reduction — being done now, in-chat.
4. ~~Write up final findings~~ **DONE.**

### 2026-09-20 — Analysis complete

- `scripts/calibration_analysis.py`: buckets `nfl_pregame_calibration.json` by `pregame_prob`
  into deciles, excludes `result: "scalar"` rows, computes actual win rate per bucket. Writes
  `analysis/calibration_table.md`, `analysis/calibration_chart.png`,
  `analysis/calibration_summary.json`. Re-runnable as more data accumulates.
- `scripts/ingame_charts.py`: loads both candlestick part files (79 games total), picks 9
  games spread across the full range of in-game price volatility (not cherry-picked for a
  good story — sorted by total price swing and sampled at even percentile spacing, plus the
  one tie/void game), plots a 3x3 grid. Writes `analysis/ingame_sample_grid.png`.
- Result: bucketed actual win rates track the predicted-probability diagonal reasonably well
  in the 40-70% range where most of the sample sits (e.g. ~44% predicted -> ~53% actual on 40
  games; ~64% predicted -> ~63% actual on 27 games). The 10-20% and 80-90% buckets have only
  2 games each and aren't statistically meaningful alone. Full writeup in `analysis/README.md`.
- **Project status: core deliverable complete for the NFL-only, Aug 6 - Sep 20 2026 sample.**
  NBA and other sports remain blocked on Kalshi's data-retention window (see above) and would
  need to be revisited once more weeks of in-window data accumulate, or once open a season
  that overlaps the window.

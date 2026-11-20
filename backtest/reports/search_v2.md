# Combination search: result (rules in `docs/spec-v2-search.md`, committed before the run, commit 1bde317)

3,547 CRT trades (Nov 2021 – Dec 2024, New York clock, both pairs, D1 and H4, two entry types). 25 conditions covering Romeo's discretionary parts: key levels, older highs/lows, previous day/week extremes, timing (weekday, 1/5/9, London/NY sweep), candle shapes, premium/discount, trend, HTF FVG/order block. Every combination of up to 3: **6,349 combinations**.

| Stage | Real data | Shuffled data (luck only, 30 runs) |
|---|---|---|
| 1. Find (2021–22): 40+ trades, z ≥ 2.5, avg R > 0 | **0** | 1.2 on average (max 6) |
| 2. Confirm (2023): 20+ trades, z ≥ 2, avg R > 0 | **0** | 0.07 on average (max 1) |
| 3. Check (2024) | 0 (nothing reached it) | — |

## Why: results don't repeat
For the 899 combinations with enough trades in both periods, the 2021–22 score and the 2023 score are **unrelated** (correlation −0.14).
The ten best combinations of 2021–22 (z 1.9–2.3, e.g. "premium + New York 09:00 sweep", "Tuesday/Wednesday sweep") all fell to about chance in 2023 (z −1.0 to +0.5).
The ten worst did not stay bad either, so trading the opposite way (breakout) has no edge.

## Conclusion
Within everything that can be measured from candles on GBP/USD and gold, CRT setups behave like chance after the sweep, whichever conditions are combined. Any edge must come from information outside these candles (a correlated market for SMT, news, order flow) or from human judgment, which the practice reviews measure.
2025–2026 remain untouched. 2024 was not used (nothing reached stage 3).
Data: `backtest/out/search_v2_trades.csv`, `backtest/out/search_v2_results.csv` (not committed; re-create with `python -m backtest.search`).

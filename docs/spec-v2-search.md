# Combination search (pre-registered 20 Nov 2026, before any result)

Ore asked for many iterations and combinations of the discretionary parts of Romeo's method. Code: `backtest/search.py`.

- **Trades:** CRTs on the New York clock (D1 and H4, both pairs, both directions). Two entries: at C2's close, and the Candle-3 trap + Model #1 (spec v2).
- **Conditions:** 25 yes/no conditions measurable at entry time (key levels, timing, candle shapes, premium/discount, trend, HTF FVG/order block). The list is in `FLAGS` in the code. Every combination of 1, 2 or 3 conditions is tested.
- **Measure:** Target 1 (50% of the range) reached before the stop, against the chance rate (z-score), and average R after spread with half off at 50%.
- **Stage 1, find (Nov 2021 – Dec 2022):** at least 40 trades, z ≥ 2.5, average R > 0.
- **Stage 2, confirm (2023):** the same combination, at least 20 trades, z ≥ 2.0, average R > 0.
- **Stage 3, check (2024):** survivors only, same thresholds. 2024 was looked at once before (v1.2), so this is weaker evidence.
- **Luck test:** the identical search run 30 times on outcomes shuffled within each period. A real finding must beat what shuffled data produces.
- **2025–2026** is not loaded. It is kept for one final test of at most a few survivors, with Ore's go-ahead.

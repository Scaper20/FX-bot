# Spec v2 (Romeo's CRT from Ore's pack): Design-period result

Rules and pass mark: `docs/spec-v2-romeo.md`, committed before this run (commit df4a87a). Script: `backtest/romeo.py`.
Period: Nov 2021 – Dec 2023 only. New York clock. Both pairs. 1-minute outcomes.

## Result: nothing passed (needed z ≥ 3 with 60+ trades)

| Entry | TF | Filter | Trades | Target 1 hit vs chance | z | Target 2 hit vs chance | z | Avg R after spread (half at 50%) |
|---|---|---|---|---|---|---|---|---|
| Candle 3 trap + Model #1 | D1 | none | 136 | 28.2% vs 25.0% | +0.9 | 13.5% vs 12.2% | +0.5 | −0.10 |
| Candle 3 trap + Model #1 | H4 | none | 489 | 27.7% vs 31.7% | −2.0 | 14.7% vs 16.8% | −1.3 | −0.27 |
| Candle 3 trap + Model #1 | D1 | weekly timing (F3) | 53 | 28.3% vs 25.5% | +0.5 | 15.1% vs 12.7% | +0.5 | −0.13 |
| Candle 3 trap + Model #1 | H4 | 1/5/9 model (F3) | 53 | 26.4% vs 39.0% | −2.0 | 16.0% vs 22.3% | −1.1 | −0.48 |
| Candle 3 trap + Model #1 | any | all filters | 1–2 | too few | | | | |
| Enter at C2 close (control) | D1 | none | 285 | 60.8% vs 58.7% | +0.8 | 35.0% vs 34.7% | +0.1 | +0.05 |
| Enter at C2 close (control) | H4 | none | 1,580 | 59.2% vs 59.8% | −0.6 | 37.1% vs 36.3% | +0.7 | −0.11 |

Full table: `backtest/out/romeo_design.csv` (re-create with `python -m backtest.romeo`).

## Reading
- As far as it can be written as rules, Romeo's model behaves like chance on GBP/USD and gold in 2021–2023, like every earlier version. On H4 it is, if anything, slightly worse than chance (price after a C3 trap tends to keep going).
- His filters combined leave almost no trades (1–16 in two years), so "all conditions met" cannot be judged from history.
- What remains untested is the discretionary part he keeps private (key-level choice, exact timing, candle shapes) and SMT, which needs EUR/USD and silver data. That is exactly what the practice reviews can measure: the Insights page shows whether the reasons traders tick (now including Romeo's concepts) pick winners.
- 2024 and 2025–2026 were not used.

# Spec v8 result: breaker entry with Ore's v1.2 filters / Romeo's 3 filters, with and without MSnR

Spec: `docs/spec-v8-breaker-filters.md` (committed before the run). GBP/USD + gold, Nov 2021 – Nov 2026, average R after spread. Consistent = 30+ trades, positive in 4 of 5 years (2022–2026) and in total.

## 1. v1.2 filters

| Row (TF entry stop) | Trades | 2022 | 2023 | 2024 | 2025 | 2026 | Avg R | Years + | Consistent |
|---|---|---|---|---|---|---|---|---|---|
| D1 confirm classic | 203 | +0.02 | -0.00 | -0.12 | -0.28 | -0.38 | -0.15 | 1 | no |
| D1 confirm tight | 203 | -0.17 | -0.26 | -0.20 | -0.17 | -0.66 | -0.28 | 0 | no |
| D1 edge classic | 234 | -0.01 | -0.03 | -0.14 | -0.22 | -0.37 | -0.15 | 0 | no |
| D1 edge tight | 234 | +0.20 | -0.24 | -0.03 | -0.24 | -0.75 | -0.21 | 1 | no |
| D1 mid classic | 215 | -0.07 | -0.17 | -0.09 | -0.20 | -0.36 | -0.18 | 0 | no |
| D1 mid tight | 215 | -0.41 | -0.47 | +0.06 | -0.01 | -0.97 | -0.34 | 1 | no |
| H4 confirm classic | 563 | -0.09 | -0.00 | -0.04 | -0.23 | -0.05 | -0.08 | 0 | no |
| H4 confirm tight | 563 | -0.29 | -0.14 | -0.26 | -0.24 | -0.11 | -0.21 | 0 | no |
| H4 edge classic | 716 | -0.09 | +0.00 | -0.08 | -0.24 | -0.09 | -0.10 | 1 | no |
| H4 edge tight | 716 | -0.34 | -0.25 | -0.24 | -0.39 | -0.15 | -0.27 | 0 | no |
| H4 mid classic | 597 | -0.11 | +0.07 | -0.09 | -0.21 | -0.16 | -0.10 | 1 | no |
| H4 mid tight | 597 | -0.48 | -0.30 | -0.54 | -0.48 | -0.52 | -0.43 | 0 | no |

Walk-forward: blind average -0.233 over 131 trades, positive in 0 of 4 years -> fail.

## 2. Romeo 3 filters

| Row (TF entry stop) | Trades | 2022 | 2023 | 2024 | 2025 | 2026 | Avg R | Years + | Consistent |
|---|---|---|---|---|---|---|---|---|---|
| D1 confirm classic | 10 | — | +4.89 | +3.91 | -0.11 | -1.00 | +1.41 | 2 | no |
| D1 confirm tight | 10 | — | +11.19 | +3.37 | -0.74 | -1.00 | +1.63 | 2 | no |
| D1 edge classic | 11 | -1.00 | +5.91 | +4.49 | +0.13 | -1.00 | +1.54 | 3 | no |
| D1 edge tight | 11 | -1.00 | +17.44 | +4.71 | -1.00 | -1.00 | +2.23 | 2 | no |
| D1 mid classic | 9 | -1.00 | — | +3.04 | +0.57 | -1.00 | +0.59 | 2 | no |
| D1 mid tight | 9 | -1.00 | — | +12.27 | -1.00 | -1.00 | +1.95 | 1 | no |
| H4 confirm classic | 12 | -0.43 | -0.50 | -0.26 | -0.01 | -1.00 | -0.33 | 0 | no |
| H4 confirm tight | 12 | -0.27 | -0.50 | -0.57 | +0.33 | -1.00 | -0.32 | 1 | no |
| H4 edge classic | 16 | -0.26 | +0.03 | -0.32 | +0.03 | -1.00 | -0.21 | 2 | no |
| H4 edge tight | 16 | -0.17 | -0.51 | -0.20 | +0.48 | -1.00 | -0.17 | 1 | no |
| H4 mid classic | 14 | -0.51 | -0.16 | -0.65 | +0.28 | -1.00 | -0.33 | 1 | no |
| H4 mid tight | 14 | -1.00 | -0.54 | -0.49 | +1.79 | -1.00 | -0.19 | 1 | no |

Walk-forward: too few trades to walk forward (no unit had 30 training trades).

## 3. v1.2 filters + MSnR

| Row (TF entry stop) | Trades | 2022 | 2023 | 2024 | 2025 | 2026 | Avg R | Years + | Consistent |
|---|---|---|---|---|---|---|---|---|---|
| D1 confirm classic | 47 | +0.02 | +0.04 | -0.10 | -0.28 | -0.11 | -0.08 | 2 | no |
| D1 confirm tight | 47 | +0.43 | -0.41 | -0.44 | +0.25 | +0.35 | -0.08 | 3 | no |
| D1 edge classic | 62 | -0.05 | +0.44 | -0.14 | -0.40 | -0.35 | -0.11 | 1 | no |
| D1 edge tight | 62 | +0.56 | +0.13 | -0.12 | -1.00 | +0.26 | -0.04 | 3 | no |
| D1 mid classic | 52 | +0.01 | +0.41 | -0.38 | -0.29 | -0.79 | -0.20 | 2 | no |
| D1 mid tight | 52 | +0.52 | +0.23 | -1.00 | -1.00 | -0.76 | -0.46 | 2 | no |
| H4 confirm classic | 152 | -0.04 | -0.03 | +0.08 | -0.11 | -0.01 | -0.02 | 1 | no |
| H4 confirm tight | 152 | -0.08 | -0.20 | -0.12 | -0.03 | -0.30 | -0.13 | 0 | no |
| H4 edge classic | 192 | -0.00 | +0.03 | +0.02 | -0.18 | -0.13 | -0.05 | 2 | no |
| H4 edge tight | 192 | -0.38 | -0.20 | -0.08 | -0.47 | -0.35 | -0.30 | 0 | no |
| H4 mid classic | 161 | +0.15 | +0.20 | -0.06 | -0.18 | -0.22 | -0.01 | 2 | no |
| H4 mid tight | 161 | -0.54 | -0.57 | -0.26 | -0.69 | -0.72 | -0.54 | 0 | no |

Walk-forward: blind average -0.308 over 38 trades, positive in 0 of 4 years -> fail.

## 4. Romeo 3 filters + MSnR

| Row (TF entry stop) | Trades | 2022 | 2023 | 2024 | 2025 | 2026 | Avg R | Years + | Consistent |
|---|---|---|---|---|---|---|---|---|---|
| D1 confirm classic | 1 | — | — | — | -1.00 | — | -1.00 | 0 | no |
| D1 confirm tight | 1 | — | — | — | -1.00 | — | -1.00 | 0 | no |
| D1 edge classic | 1 | — | — | — | -1.00 | — | -1.00 | 0 | no |
| D1 edge tight | 1 | — | — | — | -1.00 | — | -1.00 | 0 | no |
| D1 mid classic | 1 | — | — | — | +0.07 | — | +0.07 | 1 | no |
| D1 mid tight | 1 | — | — | — | -1.00 | — | -1.00 | 0 | no |
| H4 confirm classic | 1 | +0.15 | — | — | — | — | +0.15 | 1 | no |
| H4 confirm tight | 1 | +0.46 | — | — | — | — | +0.46 | 1 | no |
| H4 edge classic | 2 | -0.40 | — | — | — | — | -0.40 | 0 | no |
| H4 edge tight | 2 | -1.00 | — | — | — | — | -1.00 | 0 | no |
| H4 mid classic | 2 | -0.02 | — | — | — | — | -0.02 | 0 | no |
| H4 mid tight | 2 | -1.00 | — | — | — | — | -1.00 | 0 | no |

Walk-forward: too few trades to walk forward (no unit had 30 training trades).

## Romeo F1 only (for information)

| Row (TF entry stop) | Trades | 2022 | 2023 | 2024 | 2025 | 2026 | Avg R | Years + | Consistent |
|---|---|---|---|---|---|---|---|---|---|
| D1 confirm classic | 202 | +0.43 | -0.15 | +0.19 | -0.24 | -0.22 | +0.02 | 2 | no |
| D1 confirm tight | 202 | +0.25 | -0.04 | -0.15 | -0.39 | -0.38 | -0.12 | 1 | no |
| D1 edge classic | 255 | +0.30 | -0.22 | +0.16 | -0.19 | -0.20 | -0.02 | 2 | no |
| D1 edge tight | 255 | -0.14 | +0.00 | +0.09 | -0.50 | -0.28 | -0.16 | 2 | no |
| D1 mid classic | 223 | +0.41 | -0.38 | +0.06 | -0.38 | -0.26 | -0.09 | 2 | no |
| D1 mid tight | 223 | -0.26 | -0.53 | +0.35 | -0.48 | -0.68 | -0.32 | 1 | no |
| H4 confirm classic | 812 | -0.12 | -0.09 | -0.15 | -0.16 | -0.05 | -0.12 | 0 | no |
| H4 confirm tight | 812 | -0.17 | -0.24 | -0.22 | -0.12 | -0.24 | -0.20 | 0 | no |
| H4 edge classic | 1019 | -0.16 | -0.11 | -0.15 | -0.14 | -0.03 | -0.13 | 0 | no |
| H4 edge tight | 1019 | -0.27 | -0.32 | -0.21 | -0.30 | -0.26 | -0.27 | 0 | no |
| H4 mid classic | 836 | -0.22 | -0.08 | -0.27 | -0.16 | -0.10 | -0.17 | 0 | no |
| H4 mid tight | 836 | -0.45 | -0.53 | -0.54 | -0.46 | -0.48 | -0.48 | 0 | no |

Walk-forward: blind average -0.253 over 81 trades, positive in 0 of 4 years -> fail.

## Romeo F2 only (for information)

| Row (TF entry stop) | Trades | 2022 | 2023 | 2024 | 2025 | 2026 | Avg R | Years + | Consistent |
|---|---|---|---|---|---|---|---|---|---|
| D1 confirm classic | 131 | -0.16 | -0.18 | +0.44 | -0.13 | -0.53 | -0.09 | 1 | no |
| D1 confirm tight | 131 | -0.51 | -0.17 | -0.14 | +0.03 | -0.69 | -0.25 | 1 | no |
| D1 edge classic | 156 | -0.25 | -0.17 | +0.38 | -0.19 | -0.26 | -0.09 | 1 | no |
| D1 edge tight | 156 | -0.50 | -0.22 | +0.13 | +0.15 | +0.08 | -0.07 | 3 | no |
| D1 mid classic | 137 | -0.23 | -0.27 | +0.22 | -0.39 | -0.60 | -0.22 | 1 | no |
| D1 mid tight | 137 | -0.50 | -0.66 | +0.67 | -0.39 | -1.00 | -0.31 | 1 | no |
| H4 confirm classic | 531 | -0.23 | -0.07 | -0.15 | +0.00 | +0.12 | -0.08 | 2 | no |
| H4 confirm tight | 531 | -0.37 | -0.23 | -0.21 | -0.12 | -0.16 | -0.22 | 0 | no |
| H4 edge classic | 669 | -0.22 | -0.01 | -0.18 | -0.04 | -0.03 | -0.11 | 0 | no |
| H4 edge tight | 669 | -0.43 | -0.33 | -0.31 | -0.43 | -0.44 | -0.39 | 0 | no |
| H4 mid classic | 557 | -0.20 | +0.01 | -0.22 | -0.12 | +0.10 | -0.10 | 2 | no |
| H4 mid tight | 557 | -0.70 | -0.61 | -0.53 | -0.53 | -0.62 | -0.59 | 0 | no |

Walk-forward: blind average -0.134 over 135 trades, positive in 1 of 4 years -> fail.

## Romeo F3 only (for information)

| Row (TF entry stop) | Trades | 2022 | 2023 | 2024 | 2025 | 2026 | Avg R | Years + | Consistent |
|---|---|---|---|---|---|---|---|---|---|
| D1 confirm classic | 194 | +0.37 | -0.10 | +0.51 | -0.40 | -0.11 | +0.05 | 2 | no |
| D1 confirm tight | 194 | -0.20 | +0.09 | +0.10 | -0.38 | -0.21 | -0.11 | 2 | no |
| D1 edge classic | 238 | +0.36 | -0.10 | +0.50 | -0.40 | +0.07 | +0.09 | 3 | no |
| D1 edge tight | 238 | +0.06 | +0.11 | +0.42 | -0.53 | +0.21 | +0.06 | 4 | YES |
| D1 mid classic | 202 | +0.57 | -0.39 | +0.41 | -0.38 | +0.03 | +0.03 | 3 | no |
| D1 mid tight | 202 | -0.47 | -0.58 | +0.68 | -0.52 | -0.48 | -0.28 | 1 | no |
| H4 confirm classic | 138 | +0.06 | -0.09 | -0.16 | -0.05 | +0.06 | -0.05 | 2 | no |
| H4 confirm tight | 138 | +0.19 | +0.08 | -0.17 | -0.19 | -0.17 | -0.08 | 2 | no |
| H4 edge classic | 224 | -0.22 | +0.05 | -0.17 | +0.09 | -0.03 | -0.03 | 2 | no |
| H4 edge tight | 224 | -0.24 | +0.08 | -0.18 | -0.09 | -0.20 | -0.09 | 1 | no |
| H4 mid classic | 200 | -0.29 | +0.21 | -0.23 | +0.03 | -0.03 | -0.04 | 2 | no |
| H4 mid tight | 200 | -0.62 | +0.18 | -0.20 | -0.27 | -0.44 | -0.19 | 1 | no |

Walk-forward: blind average +0.016 over 57 trades, positive in 2 of 4 years -> fail.

## no filter (v6b baseline) (for information)

| Row (TF entry stop) | Trades | 2022 | 2023 | 2024 | 2025 | 2026 | Avg R | Years + | Consistent |
|---|---|---|---|---|---|---|---|---|---|
| D1 confirm classic | 455 | +0.20 | -0.11 | +0.04 | -0.21 | -0.23 | -0.06 | 2 | no |
| D1 confirm tight | 455 | +0.03 | -0.30 | -0.28 | -0.18 | -0.44 | -0.23 | 1 | no |
| D1 edge classic | 573 | +0.13 | -0.07 | +0.05 | -0.24 | -0.20 | -0.06 | 2 | no |
| D1 edge tight | 573 | -0.09 | -0.29 | -0.13 | -0.24 | -0.30 | -0.21 | 0 | no |
| D1 mid classic | 504 | +0.20 | -0.13 | +0.07 | -0.41 | -0.26 | -0.10 | 2 | no |
| D1 mid tight | 504 | -0.29 | -0.52 | +0.08 | -0.34 | -0.76 | -0.37 | 1 | no |
| H4 confirm classic | 1891 | -0.14 | -0.09 | -0.17 | -0.09 | -0.04 | -0.11 | 0 | no |
| H4 confirm tight | 1891 | -0.29 | -0.23 | -0.29 | -0.09 | -0.23 | -0.23 | 0 | no |
| H4 edge classic | 2405 | -0.13 | -0.11 | -0.20 | -0.08 | -0.08 | -0.12 | 0 | no |
| H4 edge tight | 2405 | -0.31 | -0.33 | -0.33 | -0.24 | -0.28 | -0.30 | 0 | no |
| H4 mid classic | 2014 | -0.21 | -0.09 | -0.26 | -0.15 | -0.09 | -0.16 | 0 | no |
| H4 mid tight | 2014 | -0.57 | -0.50 | -0.63 | -0.48 | -0.50 | -0.52 | 0 | no |

Walk-forward: blind average -0.204 over 180 trades, positive in 1 of 4 years -> fail.

## Summary

| Test | Trades | Consistent rows (of 12) | Best row avg R | Walk-forward |
|---|---|---|---|---|
| 1. v1.2 filters | 5056 | 0 | -0.08 | blind average -0.233 over 131 trades, positive in 0 of 4 years -> fail |
| 2. Romeo 3 filters | 144 | 0 | +2.23 | too few trades to walk forward (no unit had 30 training trades) |
| 3. v1.2 filters + MSnR | 1332 | 0 | -0.01 | blind average -0.308 over 38 trades, positive in 0 of 4 years -> fail |
| 4. Romeo 3 filters + MSnR | 16 | 0 | +0.46 | too few trades to walk forward (no unit had 30 training trades) |
| Romeo F1 only | 6694 | 0 | +0.02 | blind average -0.253 over 81 trades, positive in 0 of 4 years -> fail |
| Romeo F2 only | 4362 | 0 | -0.07 | blind average -0.134 over 135 trades, positive in 1 of 4 years -> fail |
| Romeo F3 only | 2392 | 1 | +0.09 | blind average +0.016 over 57 trades, positive in 2 of 4 years -> fail |
| no filter (v6b baseline) | 15684 | 0 | -0.06 | blind average -0.204 over 180 trades, positive in 1 of 4 years -> fail |

## Reading (written after the run)
- **Test 1, v1.2 filters + breaker:** 12 of 12 rows negative overall, 2,000+ trades per timeframe. The filters keep about a third of the setups and don't improve them. Walk-forward: past winner lost in all 4 blind years.
- **Test 2, Romeo's 3 filters + breaker:** only **9–16 trades per row in five years**. D1 rows show +0.6 to +2.2R a trade, but the target was hit exactly as often as chance (3 hits vs 2.9 expected, z 0.05). The average comes from 2–3 trades that ran far (+17R, +15R with the tight stop). 2025 and 2026 were negative. Too few trades to walk forward.
- **Test 3, v1.2 + MSnR:** fewer trades (47–192 per row), still negative overall in all 12 rows; walk-forward 0 of 4 years positive.
- **Test 4, Romeo + MSnR:** 1–2 trades per row in five years. Nothing can be judged.
- **Romeo F3 alone, D1 edge tight stop** is the only "consistent" row (+0.06R, 230 trades, 4 of 5 years). It's 1 of 96 rows tested, about what luck gives. Its target hit rate is near chance (13.8% vs 12.3%, z 0.7), gold lost on it (−0.29R), and its walk-forward fails. It's at most a pattern to tag and watch on the live log.

**Bottom line: neither filter set, with or without MSnR, turns the breaker entry into an edge. Romeo's full filter set is too rare to test (about 2 trades a year).**

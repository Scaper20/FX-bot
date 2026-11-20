# Spec v9 result: Romeo's filters loosened (and any 2 of 3), with the breaker entry

Spec: `docs/spec-v9-romeo-loose.md` (committed before the run). GBP/USD + gold, Nov 2021 – Nov 2026, average R after spread. Consistent = 30+ trades, positive in 4 of 5 years (2022–2026) and in total.

## 5. Romeo loose 3 filters

| Row (TF entry stop) | Trades | 2022 | 2023 | 2024 | 2025 | 2026 | Avg R | Years + | Consistent |
|---|---|---|---|---|---|---|---|---|---|
| D1 confirm classic | 112 | +0.14 | +0.20 | +0.75 | -0.21 | -0.30 | +0.11 | 3 | no |
| D1 confirm tight | 112 | +0.38 | +0.72 | +0.74 | -0.31 | -0.39 | +0.21 | 3 | no |
| D1 edge classic | 131 | +0.07 | +0.09 | +0.84 | +0.06 | -0.19 | +0.17 | 4 | YES |
| D1 edge tight | 131 | -0.10 | +0.72 | +1.44 | -0.47 | -0.00 | +0.32 | 2 | no |
| D1 mid classic | 111 | +0.05 | -0.28 | +0.52 | -0.12 | -0.44 | -0.07 | 2 | no |
| D1 mid tight | 111 | -0.09 | -0.18 | +1.69 | -0.34 | -0.95 | -0.02 | 1 | no |
| H4 confirm classic | 342 | -0.17 | -0.06 | -0.02 | -0.18 | -0.06 | -0.11 | 0 | no |
| H4 confirm tight | 342 | -0.25 | -0.15 | -0.17 | -0.06 | -0.15 | -0.16 | 0 | no |
| H4 edge classic | 443 | -0.11 | -0.02 | -0.04 | -0.11 | -0.13 | -0.08 | 0 | no |
| H4 edge tight | 443 | -0.25 | -0.28 | -0.15 | -0.22 | -0.21 | -0.21 | 0 | no |
| H4 mid classic | 363 | -0.12 | +0.05 | -0.08 | -0.25 | -0.10 | -0.11 | 1 | no |
| H4 mid tight | 363 | -0.48 | -0.59 | -0.30 | -0.40 | -0.14 | -0.36 | 0 | no |

Walk-forward: blind average -0.025 over 93 trades, positive in 1 of 4 years -> fail.

## 6. Romeo loose 3 filters + MSnR

| Row (TF entry stop) | Trades | 2022 | 2023 | 2024 | 2025 | 2026 | Avg R | Years + | Consistent |
|---|---|---|---|---|---|---|---|---|---|
| D1 confirm classic | 23 | -0.01 | -0.37 | -0.28 | -0.17 | -0.60 | -0.27 | 0 | no |
| D1 confirm tight | 23 | +0.01 | -0.15 | -0.25 | +1.50 | -0.48 | +0.00 | 2 | no |
| D1 edge classic | 32 | -0.22 | -0.24 | -0.17 | +0.14 | -0.68 | -0.23 | 1 | no |
| D1 edge tight | 32 | +0.27 | +0.31 | +0.68 | -1.00 | -0.57 | +0.13 | 3 | no |
| D1 mid classic | 24 | -0.25 | -1.00 | -0.82 | +0.50 | -0.74 | -0.46 | 1 | no |
| D1 mid tight | 24 | +1.84 | -1.00 | -1.00 | -1.00 | -0.70 | -0.24 | 1 | no |
| H4 confirm classic | 75 | +0.02 | +0.36 | +0.18 | +0.45 | -0.05 | +0.17 | 4 | YES |
| H4 confirm tight | 75 | +0.05 | +0.23 | +0.16 | +0.98 | -0.35 | +0.19 | 4 | YES |
| H4 edge classic | 92 | +0.12 | +0.47 | +0.21 | +0.28 | -0.14 | +0.17 | 4 | YES |
| H4 edge tight | 92 | -0.33 | +0.19 | +0.19 | -0.44 | -0.24 | -0.16 | 2 | no |
| H4 mid classic | 80 | +0.36 | +0.59 | +0.02 | +0.15 | -0.16 | +0.22 | 4 | YES |
| H4 mid tight | 80 | -0.38 | -0.14 | +0.07 | -1.00 | -0.35 | -0.41 | 1 | no |

Walk-forward: blind average -0.712 over 5 trades, positive in 0 of 4 years -> fail.

## 7. Romeo any 2 of 3 strict

| Row (TF entry stop) | Trades | 2022 | 2023 | 2024 | 2025 | 2026 | Avg R | Years + | Consistent |
|---|---|---|---|---|---|---|---|---|---|
| D1 confirm classic | 154 | +0.45 | -0.14 | +0.51 | -0.27 | -0.17 | +0.07 | 2 | no |
| D1 confirm tight | 154 | -0.49 | +0.23 | +0.06 | -0.26 | -0.31 | -0.14 | 2 | no |
| D1 edge classic | 180 | +0.34 | -0.29 | +0.58 | -0.24 | +0.16 | +0.10 | 3 | no |
| D1 edge tight | 180 | -0.44 | +0.16 | +0.50 | -0.40 | +0.39 | +0.02 | 3 | no |
| D1 mid classic | 153 | +0.55 | -0.52 | +0.46 | -0.28 | +0.02 | +0.05 | 3 | no |
| D1 mid tight | 153 | -0.79 | -0.44 | +0.81 | -0.62 | -0.48 | -0.28 | 1 | no |
| H4 confirm classic | 211 | -0.27 | -0.12 | -0.09 | -0.13 | +0.07 | -0.11 | 1 | no |
| H4 confirm tight | 211 | -0.34 | -0.22 | -0.12 | -0.30 | -0.18 | -0.24 | 0 | no |
| H4 edge classic | 290 | -0.34 | -0.06 | -0.07 | -0.01 | +0.01 | -0.09 | 1 | no |
| H4 edge tight | 290 | -0.44 | -0.21 | +0.04 | -0.33 | -0.39 | -0.25 | 1 | no |
| H4 mid classic | 251 | -0.40 | +0.07 | -0.14 | -0.02 | +0.14 | -0.07 | 2 | no |
| H4 mid tight | 251 | -0.74 | -0.28 | +0.13 | -0.24 | -0.58 | -0.30 | 1 | no |

Walk-forward: blind average +0.024 over 78 trades, positive in 2 of 4 years -> fail.

## 8. Romeo any 2 of 3 strict + MSnR

| Row (TF entry stop) | Trades | 2022 | 2023 | 2024 | 2025 | 2026 | Avg R | Years + | Consistent |
|---|---|---|---|---|---|---|---|---|---|
| D1 confirm classic | 18 | -0.47 | -0.58 | -0.80 | -0.17 | -0.38 | -0.58 | 0 | no |
| D1 confirm tight | 18 | -0.38 | -0.44 | -0.75 | +1.50 | -0.27 | -0.23 | 1 | no |
| D1 edge classic | 27 | -0.81 | -0.49 | -0.68 | +0.14 | -0.29 | -0.52 | 1 | no |
| D1 edge tight | 27 | -0.73 | -0.13 | +0.01 | -1.00 | -0.03 | -0.34 | 1 | no |
| D1 mid classic | 22 | -1.00 | -1.00 | -1.00 | +0.99 | -0.09 | -0.65 | 1 | no |
| D1 mid tight | 22 | -1.00 | -1.00 | -1.00 | -1.00 | +0.94 | -0.82 | 1 | no |
| H4 confirm classic | 32 | -0.23 | +0.10 | +0.07 | -1.00 | -0.40 | -0.24 | 2 | no |
| H4 confirm tight | 32 | -0.53 | +0.03 | +0.25 | -1.00 | -0.27 | -0.24 | 2 | no |
| H4 edge classic | 45 | -0.23 | +0.28 | +0.32 | -0.63 | -0.42 | -0.12 | 2 | no |
| H4 edge tight | 45 | -0.58 | +0.01 | +0.67 | -0.88 | -0.25 | -0.17 | 2 | no |
| H4 mid classic | 36 | -0.17 | +0.20 | +0.09 | -0.64 | -1.00 | -0.22 | 2 | no |
| H4 mid tight | 36 | -0.76 | -0.39 | +0.51 | -1.00 | -1.00 | -0.44 | 1 | no |

Walk-forward: too few trades to walk forward (no unit had 30 training trades).

## loose F1 only (not against HTF) (for information)

| Row (TF entry stop) | Trades | 2022 | 2023 | 2024 | 2025 | 2026 | Avg R | Years + | Consistent |
|---|---|---|---|---|---|---|---|---|---|
| D1 confirm classic | 271 | +0.41 | -0.06 | +0.15 | -0.25 | -0.14 | +0.03 | 2 | no |
| D1 confirm tight | 271 | +0.16 | -0.20 | -0.10 | -0.29 | -0.36 | -0.15 | 1 | no |
| D1 edge classic | 335 | +0.32 | -0.04 | +0.13 | -0.21 | -0.09 | +0.03 | 2 | no |
| D1 edge tight | 335 | -0.11 | -0.16 | +0.13 | -0.49 | -0.12 | -0.15 | 1 | no |
| D1 mid classic | 293 | +0.45 | -0.12 | +0.02 | -0.39 | -0.14 | -0.03 | 2 | no |
| D1 mid tight | 293 | -0.34 | -0.52 | +0.14 | -0.44 | -0.69 | -0.37 | 1 | no |
| H4 confirm classic | 1120 | -0.15 | -0.09 | -0.17 | -0.19 | -0.11 | -0.15 | 0 | no |
| H4 confirm tight | 1120 | -0.18 | -0.25 | -0.24 | -0.14 | -0.30 | -0.23 | 0 | no |
| H4 edge classic | 1409 | -0.14 | -0.11 | -0.19 | -0.19 | -0.11 | -0.16 | 0 | no |
| H4 edge tight | 1409 | -0.25 | -0.33 | -0.24 | -0.32 | -0.30 | -0.29 | 0 | no |
| H4 mid classic | 1171 | -0.21 | -0.08 | -0.28 | -0.21 | -0.14 | -0.19 | 0 | no |
| H4 mid tight | 1171 | -0.46 | -0.53 | -0.56 | -0.45 | -0.47 | -0.49 | 0 | no |

Walk-forward: blind average -0.186 over 114 trades, positive in 0 of 4 years -> fail.

## loose F2 only (key level) (for information)

| Row (TF entry stop) | Trades | 2022 | 2023 | 2024 | 2025 | 2026 | Avg R | Years + | Consistent |
|---|---|---|---|---|---|---|---|---|---|
| D1 confirm classic | 329 | -0.01 | -0.06 | +0.17 | -0.18 | -0.31 | -0.08 | 1 | no |
| D1 confirm tight | 329 | -0.14 | -0.14 | -0.14 | -0.23 | -0.46 | -0.22 | 0 | no |
| D1 edge classic | 414 | -0.07 | -0.07 | +0.14 | -0.20 | -0.27 | -0.10 | 1 | no |
| D1 edge tight | 414 | -0.23 | -0.18 | +0.02 | -0.23 | -0.30 | -0.19 | 1 | no |
| D1 mid classic | 367 | +0.03 | -0.22 | +0.11 | -0.35 | -0.47 | -0.17 | 2 | no |
| D1 mid tight | 367 | -0.32 | -0.53 | +0.19 | -0.34 | -0.98 | -0.39 | 1 | no |
| H4 confirm classic | 1348 | -0.12 | -0.09 | -0.16 | -0.09 | +0.00 | -0.10 | 1 | no |
| H4 confirm tight | 1348 | -0.26 | -0.20 | -0.30 | -0.11 | -0.25 | -0.22 | 0 | no |
| H4 edge classic | 1726 | -0.12 | -0.10 | -0.18 | -0.07 | -0.09 | -0.12 | 0 | no |
| H4 edge tight | 1726 | -0.32 | -0.33 | -0.32 | -0.27 | -0.37 | -0.32 | 0 | no |
| H4 mid classic | 1438 | -0.16 | -0.10 | -0.24 | -0.18 | -0.07 | -0.15 | 0 | no |
| H4 mid tight | 1438 | -0.56 | -0.56 | -0.60 | -0.54 | -0.54 | -0.54 | 0 | no |

Walk-forward: blind average -0.071 over 133 trades, positive in 2 of 4 years -> fail.

## loose F3 only (time) (for information)

| Row (TF entry stop) | Trades | 2022 | 2023 | 2024 | 2025 | 2026 | Avg R | Years + | Consistent |
|---|---|---|---|---|---|---|---|---|---|
| D1 confirm classic | 288 | +0.25 | -0.12 | +0.17 | -0.37 | -0.19 | -0.05 | 2 | no |
| D1 confirm tight | 288 | +0.16 | +0.05 | -0.09 | -0.42 | -0.34 | -0.12 | 2 | no |
| D1 edge classic | 353 | +0.26 | -0.10 | +0.12 | -0.33 | -0.13 | -0.03 | 2 | no |
| D1 edge tight | 353 | +0.04 | +0.04 | +0.07 | -0.40 | -0.04 | -0.05 | 3 | no |
| D1 mid classic | 303 | +0.34 | -0.26 | +0.00 | -0.51 | -0.21 | -0.13 | 2 | no |
| D1 mid tight | 303 | -0.29 | -0.28 | +0.14 | -0.62 | -0.66 | -0.32 | 1 | no |
| H4 confirm classic | 821 | -0.08 | -0.03 | -0.09 | -0.09 | -0.05 | -0.07 | 0 | no |
| H4 confirm tight | 821 | -0.33 | -0.05 | -0.25 | -0.13 | -0.12 | -0.17 | 0 | no |
| H4 edge classic | 1059 | -0.10 | +0.00 | -0.08 | -0.06 | -0.07 | -0.06 | 1 | no |
| H4 edge tight | 1059 | -0.39 | -0.16 | -0.21 | -0.19 | -0.21 | -0.23 | 0 | no |
| H4 mid classic | 873 | -0.14 | +0.01 | -0.13 | -0.15 | -0.07 | -0.10 | 1 | no |
| H4 mid tight | 873 | -0.59 | -0.39 | -0.47 | -0.42 | -0.40 | -0.44 | 0 | no |

Walk-forward: blind average -0.293 over 118 trades, positive in 0 of 4 years -> fail.

## Summary

| Test | Trades | Consistent rows (of 12) | Best row avg R | Walk-forward |
|---|---|---|---|---|
| 5. Romeo loose 3 filters | 3004 | 1 | +0.32 | blind average -0.025 over 93 trades, positive in 1 of 4 years -> fail |
| 6. Romeo loose 3 filters + MSnR | 652 | 4 | +0.22 | blind average -0.712 over 5 trades, positive in 0 of 4 years -> fail |
| 7. Romeo any 2 of 3 strict | 2478 | 0 | +0.10 | blind average +0.024 over 78 trades, positive in 2 of 4 years -> fail |
| 8. Romeo any 2 of 3 strict + MSnR | 360 | 0 | -0.12 | too few trades to walk forward (no unit had 30 training trades) |
| loose F1 only (not against HTF) | 9198 | 0 | +0.03 | blind average -0.186 over 114 trades, positive in 0 of 4 years -> fail |
| loose F2 only (key level) | 11244 | 0 | -0.08 | blind average -0.071 over 133 trades, positive in 2 of 4 years -> fail |
| loose F3 only (time) | 7394 | 0 | -0.03 | blind average -0.293 over 118 trades, positive in 0 of 4 years -> fail |

## Reading (written after the run)
**Why the strict filters were rare** (see spec): F3 on H4 keeps 9% (one candle sequence a day), and F1 and F2 work against each other (5–6% pass both vs 12% if unrelated). All three: 1.9% of D1 and 0.7% of H4 setups.

**Looser filters give 20× more trades** (test 5: 3,004 vs 144) but on their own still don't make money on H4. D1 edge classic is the one consistent row in test 5 (+0.17R, 131 trades), but 2026 was negative and the walk-forward fails (1 of 4 blind years).

**Test 6, loose filters + MSnR, H4, classic stop, is the strongest candidate found in this project so far:**
| Entry | Trades | Avg R | Years + | Target 1 hit vs chance | Target 2 hit vs chance | GBP/USD | Gold |
|---|---|---|---|---|---|---|---|
| edge | 92 | +0.17 | 4 of 5 | 67% vs 57% (z +1.7) | 48% vs 39% (z +1.9) | +0.29 | +0.06 |
| confirm | 75 | +0.19 | 4 of 5 | 65% vs 61% | 54% vs 44% (z +1.8) | +0.27 | +0.08 |
| mid | 80 | +0.22 | 4 of 5 | 55% vs 52% | 39% vs 34% | +0.33 | +0.12 |
- Luck test: random 92-trade groups from all H4 breaker setups reached this average with 4+ positive years in 0.8% of 2,000 draws.
- **But:** the three rows are largely the same ~90 setups; about 48 rows were looked at after loosening the filters having seen data, so a 1-in-100 result is not rare; 2026 is negative in all rows; it's ~18 trades a year.
- Walk-forward: the pre-registered version (units split by pair) could hardly trade (5 trades). Pooling the pairs (a change made after seeing the data, shown for information): blind −0.004R over 41 trades, positive in 2 of 4 years. **Not confirmed.**

**Verdict:** a candidate, not an edge. It needs data it has never seen. Next honest test: the same rule, unchanged, on EUR/USD and silver (data already in the repo, never used for this rule), and/or logged live.

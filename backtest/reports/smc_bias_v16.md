# Spec v16 result: D1/H4 bias + MSS + order block / FVG entries

Spec: `docs/spec-v16-smc-bias.md` (committed before the run). GBP/USD + gold, Nov 2021 – Nov 2026, Ore's spreads, target 3R (chance 25%), stop above the top + 2 spreads.

## D1 + H4 bias (Ore's model)

| TF | Entry | Session | Trades | Win vs chance | Avg R no costs | **Avg R after spread** | 2022 | 2023 | 2024 | 2025 | 2026 | Years + | Consistent |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H1 | E1 market at MSS close | all | 1861 | 20.3% vs 25.0% | -0.009 | **-0.037** | -0.09 | -0.12 | -0.01 | +0.10 | -0.10 | 1 | no |
| H1 | E1 market at MSS close | London/NY | 1244 | 18.9% vs 25.0% | -0.005 | **-0.032** | -0.05 | -0.14 | -0.03 | +0.12 | -0.12 | 1 | no |
| H1 | E2 FVG near edge | all | 393 | 25.6% vs 25.0% | +0.093 | **+0.038** | +0.16 | +0.04 | -0.06 | +0.06 | -0.11 | 3 | no |
| H1 | E2 FVG near edge | London/NY | 248 | 28.6% vs 25.0% | +0.238 | **+0.163** | +0.30 | +0.03 | +0.06 | +0.18 | +0.19 | 5 | YES |
| H1 | E3 FVG middle | all | 371 | 27.1% vs 25.0% | +0.124 | **+0.077** | +0.20 | +0.07 | -0.01 | +0.18 | -0.18 | 3 | no |
| H1 | E3 FVG middle | London/NY | 231 | 30.8% vs 25.0% | +0.286 | **+0.241** | +0.42 | +0.22 | +0.14 | +0.31 | +0.05 | 5 | YES |
| H1 | E4 OB open | all | 234 | 32.9% vs 25.0% | +0.324 | **+0.268** | +0.18 | +0.36 | +0.13 | +0.21 | +0.47 | 5 | YES |
| H1 | E4 OB open | London/NY | 166 | 34.4% vs 25.0% | +0.384 | **+0.322** | +0.30 | +0.19 | +0.22 | +0.08 | +0.93 | 5 | YES |
| H1 | E5 OB middle | all | 195 | 31.4% vs 25.0% | +0.261 | **+0.150** | +0.29 | +0.17 | -0.04 | +0.13 | +0.13 | 4 | YES |
| H1 | E5 OB middle | London/NY | 135 | 34.3% vs 25.0% | +0.377 | **+0.240** | +0.34 | -0.07 | +0.24 | +0.30 | +0.62 | 4 | YES |
| M15 | E1 market at MSS close | all | 6783 | 23.7% vs 25.0% | -0.017 | **-0.064** | -0.07 | -0.08 | -0.11 | -0.01 | -0.07 | 0 | no |
| M15 | E1 market at MSS close | London/NY | 4256 | 23.0% vs 25.0% | -0.023 | **-0.064** | -0.09 | -0.06 | -0.12 | -0.02 | -0.07 | 0 | no |
| M15 | E2 FVG near edge | all | 1666 | 23.0% vs 25.0% | -0.067 | **-0.124** | -0.07 | -0.14 | -0.24 | -0.05 | -0.11 | 0 | no |
| M15 | E2 FVG near edge | London/NY | 1011 | 22.5% vs 25.0% | -0.077 | **-0.125** | -0.03 | -0.14 | -0.24 | -0.02 | -0.19 | 0 | no |
| M15 | E3 FVG middle | all | 1535 | 23.4% vs 25.0% | -0.051 | **-0.128** | -0.18 | -0.10 | -0.17 | -0.09 | -0.07 | 0 | no |
| M15 | E3 FVG middle | London/NY | 932 | 23.8% vs 25.0% | -0.026 | **-0.102** | -0.14 | -0.10 | -0.10 | -0.01 | -0.11 | 0 | no |
| M15 | E4 OB open | all | 1039 | 23.9% vs 25.0% | -0.038 | **-0.135** | -0.16 | -0.18 | -0.30 | +0.00 | -0.02 | 1 | no |
| M15 | E4 OB open | London/NY | 611 | 24.0% vs 25.0% | -0.032 | **-0.112** | -0.23 | -0.15 | -0.21 | +0.11 | -0.07 | 1 | no |
| M15 | E5 OB middle | all | 873 | 24.2% vs 25.0% | -0.031 | **-0.148** | -0.13 | -0.22 | -0.30 | -0.08 | +0.03 | 1 | no |
| M15 | E5 OB middle | London/NY | 512 | 24.4% vs 25.0% | -0.020 | **-0.115** | -0.15 | -0.14 | -0.26 | +0.04 | -0.03 | 1 | no |

Walk-forward: blind +0.099R over 112 trades, positive in 3 of 4 years -> **PASS**.

## D1 bias only

| TF | Entry | Session | Trades | Win vs chance | Avg R no costs | **Avg R after spread** | 2022 | 2023 | 2024 | 2025 | 2026 | Years + | Consistent |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H1 | E1 market at MSS close | all | 2943 | 20.3% vs 25.0% | -0.009 | **-0.032** | -0.10 | -0.05 | -0.11 | +0.14 | -0.05 | 1 | no |
| H1 | E1 market at MSS close | London/NY | 2007 | 19.0% vs 25.0% | -0.005 | **-0.029** | -0.04 | -0.09 | -0.13 | +0.15 | -0.06 | 1 | no |
| H1 | E2 FVG near edge | all | 618 | 24.5% vs 25.0% | +0.093 | **+0.013** | +0.21 | +0.11 | -0.30 | +0.16 | -0.22 | 3 | no |
| H1 | E2 FVG near edge | London/NY | 396 | 26.7% vs 25.0% | +0.238 | **+0.112** | +0.41 | +0.07 | -0.21 | +0.20 | -0.03 | 3 | no |
| H1 | E3 FVG middle | all | 578 | 24.4% vs 25.0% | +0.124 | **-0.007** | +0.20 | +0.06 | -0.32 | +0.18 | -0.26 | 3 | no |
| H1 | E3 FVG middle | London/NY | 366 | 26.6% vs 25.0% | +0.286 | **+0.099** | +0.45 | +0.05 | -0.21 | +0.23 | -0.16 | 3 | no |
| H1 | E4 OB open | all | 371 | 29.0% vs 25.0% | +0.324 | **+0.133** | +0.14 | +0.20 | -0.19 | +0.30 | +0.26 | 4 | YES |
| H1 | E4 OB open | London/NY | 270 | 29.9% vs 25.0% | +0.384 | **+0.170** | +0.28 | +0.13 | -0.26 | +0.36 | +0.44 | 4 | YES |
| H1 | E5 OB middle | all | 313 | 28.0% vs 25.0% | +0.261 | **+0.043** | +0.34 | -0.04 | -0.28 | +0.10 | +0.11 | 3 | no |
| H1 | E5 OB middle | London/NY | 224 | 31.1% vs 25.0% | +0.377 | **+0.154** | +0.47 | -0.17 | -0.20 | +0.39 | +0.41 | 3 | no |
| M15 | E1 market at MSS close | all | 11311 | 23.7% vs 25.0% | -0.017 | **-0.057** | -0.06 | -0.05 | -0.14 | +0.01 | -0.06 | 1 | no |
| M15 | E1 market at MSS close | London/NY | 7083 | 23.1% vs 25.0% | -0.023 | **-0.048** | -0.08 | -0.01 | -0.12 | +0.01 | -0.07 | 1 | no |
| M15 | E2 FVG near edge | all | 2676 | 23.8% vs 25.0% | -0.067 | **-0.090** | -0.02 | -0.11 | -0.27 | -0.01 | -0.03 | 0 | no |
| M15 | E2 FVG near edge | London/NY | 1621 | 23.8% vs 25.0% | -0.077 | **-0.072** | +0.06 | -0.14 | -0.25 | +0.03 | -0.05 | 2 | no |
| M15 | E3 FVG middle | all | 2470 | 24.1% vs 25.0% | -0.051 | **-0.094** | -0.11 | -0.08 | -0.19 | -0.06 | +0.00 | 1 | no |
| M15 | E3 FVG middle | London/NY | 1490 | 25.1% vs 25.0% | -0.026 | **-0.046** | -0.00 | -0.08 | -0.16 | +0.02 | +0.03 | 2 | no |
| M15 | E4 OB open | all | 1660 | 24.5% vs 25.0% | -0.038 | **-0.104** | -0.16 | -0.09 | -0.27 | +0.01 | +0.00 | 2 | no |
| M15 | E4 OB open | London/NY | 978 | 25.9% vs 25.0% | -0.032 | **-0.038** | -0.11 | -0.07 | -0.15 | +0.11 | +0.03 | 2 | no |
| M15 | E5 OB middle | all | 1396 | 24.3% vs 25.0% | -0.031 | **-0.141** | -0.16 | -0.16 | -0.24 | -0.09 | -0.02 | 0 | no |
| M15 | E5 OB middle | London/NY | 818 | 24.9% vs 25.0% | -0.020 | **-0.096** | -0.12 | -0.14 | -0.26 | +0.04 | +0.02 | 2 | no |

Walk-forward: blind +0.046R over 231 trades, positive in 2 of 4 years -> **fail**.

## no bias (baseline)

| TF | Entry | Session | Trades | Win vs chance | Avg R no costs | **Avg R after spread** | 2022 | 2023 | 2024 | 2025 | 2026 | Years + | Consistent |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H1 | E1 market at MSS close | all | 5812 | 20.2% vs 25.0% | -0.009 | **-0.018** | -0.08 | -0.07 | -0.02 | +0.10 | +0.00 | 2 | no |
| H1 | E1 market at MSS close | London/NY | 4016 | 19.1% vs 25.0% | -0.005 | **-0.014** | -0.05 | -0.08 | -0.03 | +0.09 | +0.01 | 2 | no |
| H1 | E2 FVG near edge | all | 1147 | 24.2% vs 25.0% | +0.093 | **+0.018** | +0.08 | +0.05 | -0.14 | +0.02 | +0.05 | 4 | no |
| H1 | E2 FVG near edge | London/NY | 732 | 24.9% vs 25.0% | +0.238 | **+0.071** | +0.28 | -0.05 | -0.06 | +0.04 | +0.07 | 3 | no |
| H1 | E3 FVG middle | all | 1065 | 24.2% vs 25.0% | +0.124 | **+0.004** | +0.10 | +0.05 | -0.17 | -0.02 | +0.01 | 3 | no |
| H1 | E3 FVG middle | London/NY | 675 | 25.2% vs 25.0% | +0.286 | **+0.071** | +0.34 | -0.01 | -0.07 | -0.01 | +0.01 | 2 | no |
| H1 | E4 OB open | all | 706 | 26.8% vs 25.0% | +0.324 | **+0.063** | +0.04 | +0.01 | -0.13 | +0.17 | +0.26 | 4 | YES |
| H1 | E4 OB open | London/NY | 501 | 27.4% vs 25.0% | +0.384 | **+0.094** | +0.13 | -0.00 | -0.13 | +0.31 | +0.25 | 3 | no |
| H1 | E5 OB middle | all | 608 | 27.2% vs 25.0% | +0.261 | **+0.015** | +0.14 | -0.13 | -0.12 | +0.07 | +0.16 | 3 | no |
| H1 | E5 OB middle | London/NY | 427 | 29.3% vs 25.0% | +0.377 | **+0.107** | +0.21 | -0.10 | -0.06 | +0.34 | +0.31 | 3 | no |
| M15 | E1 market at MSS close | all | 22674 | 23.4% vs 25.0% | -0.017 | **-0.066** | -0.08 | -0.09 | -0.08 | -0.02 | -0.05 | 0 | no |
| M15 | E1 market at MSS close | London/NY | 14165 | 22.4% vs 25.0% | -0.023 | **-0.070** | -0.09 | -0.07 | -0.09 | -0.03 | -0.08 | 0 | no |
| M15 | E2 FVG near edge | all | 5330 | 23.4% vs 25.0% | -0.067 | **-0.111** | -0.11 | -0.11 | -0.15 | -0.06 | -0.10 | 0 | no |
| M15 | E2 FVG near edge | London/NY | 3236 | 22.8% vs 25.0% | -0.077 | **-0.105** | -0.05 | -0.15 | -0.18 | -0.03 | -0.10 | 0 | no |
| M15 | E3 FVG middle | all | 4917 | 23.8% vs 25.0% | -0.051 | **-0.108** | -0.12 | -0.09 | -0.12 | -0.08 | -0.11 | 0 | no |
| M15 | E3 FVG middle | London/NY | 2967 | 23.9% vs 25.0% | -0.026 | **-0.083** | -0.03 | -0.12 | -0.11 | -0.04 | -0.10 | 0 | no |
| M15 | E4 OB open | all | 3350 | 23.9% vs 25.0% | -0.038 | **-0.133** | -0.12 | -0.12 | -0.23 | -0.04 | -0.12 | 0 | no |
| M15 | E4 OB open | London/NY | 1987 | 24.7% vs 25.0% | -0.032 | **-0.084** | -0.11 | -0.09 | -0.17 | +0.03 | -0.06 | 1 | no |
| M15 | E5 OB middle | all | 2865 | 24.4% vs 25.0% | -0.031 | **-0.155** | -0.15 | -0.16 | -0.23 | -0.10 | -0.11 | 0 | no |
| M15 | E5 OB middle | London/NY | 1680 | 24.7% vs 25.0% | -0.020 | **-0.119** | -0.11 | -0.10 | -0.24 | -0.03 | -0.07 | 0 | no |

Walk-forward: blind +0.048R over 405 trades, positive in 3 of 4 years -> **PASS**.

## Summary

Consistent rows: **9 of 60**. With Ore's D1+H4 bias: average -0.070R after spread, -0.012R with no costs, over 14,950 trades. No bias: -0.073R after spread over 48,474 trades.

## Fresh-market check (spec addendum): EUR/USD + silver, script unchanged, H1, D1 + H4 bias
| Entry | GBP/USD + gold | EUR/USD + silver | |
|---|---|---|---|
| **E4 OB open, all sessions (main row)** | +0.268R, 234 trades, 5 of 5 years, 32.9% vs 25% | **−0.123R, 222 trades, 2 of 5 years, 23.6% vs 25%** (EUR/USD −0.22R, silver −0.01R) | **FAIL** |
| E4 OB open, London/NY | +0.322R, 166 | −0.057R, 169, 3 of 5 | |
| E2 FVG edge / E3 FVG middle | +0.04 to +0.24R | −0.10 to −0.12R | |
| E5 OB middle | +0.15 / +0.24R | −0.21 / −0.22R | |

## Reading
- On GBP/USD + gold the model looked genuinely good: 9 of 60 rows consistent (more than luck alone would give), a clear order (no bias < D1 bias < D1 + H4 bias), the walk-forward passed, and the main row had t 2.3, positive on both pairs and both directions.
- **On EUR/USD + silver every one of those rows lost money**, and the target was hit at or below chance. So the GBP/USD + gold result most likely came from these two markets in these years, not from a rule that works generally. By our standard it doesn't count.
- M15 entries and market entries at the MSS close were negative on GBP/USD + gold too. Overall: −0.07R a trade after spread with the D1 + H4 bias (−0.01R before costs), about the same as with no bias.
- If Ore wants to keep watching it, the honest test is live: log every H1 OB-open setup with D1 + H4 bias at the moment it forms, before the outcome, and judge after enough trades.

# Spec v24 result: Ore's liquidity model

Spec: `docs/spec-v24-ore-model.md` (committed before the run). Main test GBP/USD + gold, fresh check EUR/USD + silver, Nov 2021 – Nov 2026, Ore's spreads, 1-minute scoring.

| Model | TF | Target | Bias | Trades | No costs | **After spread** | t | Hit vs chance | 2022 | 2023 | 2024 | 2025 | 2026 | Yrs + | Consistent | Fresh (trades · avg · yrs+ · hit) | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Reversal · OB | H1 | 3R | D1 trend | 25 | -0.360 | **-0.375** | -1.3 | 16% vs 25% | -1.00 | -1.00 | -0.23 | -0.34 | +0.96 | 1 | no | 24 · -0.204 · 1 · 21% |  |
| Reversal · OB | H1 | 3R | none | 52 | -0.462 | **-0.470** | -2.5 | 13% vs 25% | -1.00 | -1.00 | -0.13 | -0.01 | -0.13 | 0 | no | 39 · +0.191 · 4 · 31% |  |
| Reversal · OB | H1 | 5R | D1 trend | 25 | -0.377 | **-0.398** | -1.2 | 8% vs 17% | -1.00 | -1.00 | +0.15 | -0.41 | +0.43 | 2 | no | 24 · -0.019 · 2 · 14% |  |
| Reversal · OB | H1 | 5R | none | 52 | -0.399 | **-0.413** | -1.8 | 8% vs 17% | -1.00 | -1.00 | +0.05 | +0.28 | -0.36 | 2 | no | 39 · +0.217 · 3 · 15% |  |
| Reversal · OB | M15 | 3R | D1 trend | 61 | -0.344 | **-0.429** | -2.4 | 16% vs 25% | -0.33 | -0.46 | -1.00 | +0.52 | -0.66 | 1 | no | 55 · -0.392 · 0 · 16% |  |
| Reversal · OB | M15 | 3R | none | 146 | -0.096 | **-0.214** | -1.7 | 23% vs 25% | -0.08 | -0.46 | -0.41 | +0.46 | -0.31 | 1 | no | 135 · -0.531 · 0 · 13% |  |
| Reversal · OB | M15 | 5R | D1 trend | 61 | -0.526 | **-0.630** | -3.6 | 7% vs 17% | -0.15 | -1.00 | -1.00 | -0.49 | -0.48 | 0 | no | 55 · -0.503 · 1 · 8% |  |
| Reversal · OB | M15 | 5R | none | 146 | -0.103 | **-0.225** | -1.4 | 15% vs 17% | +0.15 | -0.37 | -0.42 | +0.24 | -0.67 | 2 | no | 135 · -0.592 · 0 · 7% |  |
| Reversal · OB | M5 | 3R | D1 trend | 225 | +0.204 | **+0.023** | +0.2 | 30% vs 25% | -0.38 | +0.25 | +0.23 | +0.07 | -0.12 | 3 | no | 229 · -0.184 · 1 · 26% |  |
| Reversal · OB | M5 | 3R | none | 471 | +0.051 | **-0.102** | -1.4 | 26% vs 25% | -0.26 | -0.12 | -0.07 | -0.02 | -0.04 | 0 | no | 453 · -0.182 · 1 · 25% |  |
| Reversal · OB | M5 | 5R | D1 trend | 225 | +0.101 | **-0.065** | -0.5 | 18% vs 17% | -0.48 | +0.56 | -0.02 | -0.14 | -0.36 | 1 | no | 229 · -0.096 · 1 · 19% |  |
| Reversal · OB | M5 | 5R | none | 471 | -0.064 | **-0.205** | -2.3 | 15% vs 17% | -0.35 | +0.04 | -0.16 | -0.28 | -0.45 | 1 | no | 453 · -0.148 · 1 · 17% |  |
| Reversal · BB | H1 | 3R | D1 trend | 20 | +0.400 | **+0.373** | +0.9 | 35% vs 25% | +1.67 | +0.32 | +0.77 | -0.20 | +0.00 | 3 | no | 16 · -0.313 · 1 · 19% |  |
| Reversal · BB | H1 | 3R | none | 31 | +0.161 | **+0.135** | +0.4 | 29% vs 25% | +0.95 | -0.01 | -0.12 | +0.14 | -0.33 | 2 | no | 33 · +0.150 · 3 · 30% |  |
| Reversal · BB | H1 | 5R | D1 trend | 20 | +0.200 | **+0.195** | +0.4 | 20% vs 17% | +3.00 | +0.98 | -1.00 | -1.00 | -1.00 | 2 | no | 16 · -0.120 · 2 · 13% |  |
| Reversal · BB | H1 | 5R | none | 31 | +0.161 | **+0.144** | +0.3 | 19% vs 17% | +1.93 | +0.49 | -1.00 | -0.14 | -1.00 | 2 | no | 33 · +0.470 · 4 · 26% |  |
| Reversal · BB | M15 | 3R | D1 trend | 28 | +0.571 | **+0.469** | +1.3 | 39% vs 25% | +0.29 | +0.76 | +0.08 | +1.16 | -0.09 | 4 | no | 36 · -0.103 · 3 · 28% |  |
| Reversal · BB | M15 | 3R | none | 77 | +0.247 | **+0.193** | +0.9 | 31% vs 25% | -0.08 | +0.27 | -0.36 | +1.03 | +0.65 | 3 | no | 73 · -0.004 · 3 · 29% |  |
| Reversal · BB | M15 | 5R | D1 trend | 28 | +0.929 | **+0.796** | +1.6 | 32% vs 17% | +0.94 | +1.64 | +0.63 | +0.60 | +0.37 | 5 | no | 36 · -0.325 · 2 · 14% |  |
| Reversal · BB | M15 | 5R | none | 77 | +0.325 | **+0.178** | +0.7 | 22% vs 17% | -0.18 | +0.10 | -0.37 | +1.28 | +0.64 | 3 | no | 73 · -0.112 · 1 · 18% |  |
| Reversal · BB | M5 | 3R | D1 trend | 115 | +0.252 | **+0.114** | +0.7 | 31% vs 25% | +0.63 | +0.07 | +0.13 | +0.15 | -0.20 | 4 | YES | 121 · -0.333 · 0 · 24% | fresh FAIL |
| Reversal · BB | M5 | 3R | none | 248 | +0.048 | **-0.075** | -0.7 | 26% vs 25% | +0.06 | -0.20 | -0.05 | +0.13 | -0.34 | 2 | no | 244 · -0.187 · 2 · 26% |  |
| Reversal · BB | M5 | 5R | D1 trend | 115 | +0.304 | **+0.078** | +0.4 | 22% vs 17% | +0.44 | -0.17 | +0.27 | +0.01 | -0.04 | 3 | no | 121 · -0.451 · 0 · 14% |  |
| Reversal · BB | M5 | 5R | none | 248 | +0.040 | **-0.095** | -0.7 | 17% vs 17% | -0.06 | -0.22 | +0.02 | -0.08 | -0.15 | 1 | no | 244 · -0.300 · 1 · 15% |  |
| Reversal · nearest (BB, else OB) | H1 | 3R | D1 trend | 40 | +0.000 | **-0.023** | -0.1 | 25% vs 25% | +0.60 | -0.39 | +0.23 | -0.20 | +0.30 | 3 | no | 36 · -0.164 · 1 · 22% |  |
| Reversal · nearest (BB, else OB) | H1 | 3R | none | 77 | -0.221 | **-0.237** | -1.3 | 19% vs 25% | -0.10 | -0.60 | +0.03 | +0.10 | -0.40 | 2 | no | 66 · +0.218 · 4 · 32% |  |
| Reversal · nearest (BB, else OB) | H1 | 5R | D1 trend | 40 | -0.011 | **-0.027** | -0.1 | 15% vs 17% | +1.40 | -0.09 | -0.04 | -0.65 | -0.04 | 1 | no | 36 · +0.045 · 2 · 15% |  |
| Reversal · nearest (BB, else OB) | H1 | 5R | none | 77 | -0.127 | **-0.143** | -0.6 | 13% vs 17% | +0.35 | -0.41 | -0.14 | +0.19 | -0.56 | 2 | no | 66 · +0.454 · 4 · 22% |  |
| Reversal · nearest (BB, else OB) | M15 | 3R | D1 trend | 87 | -0.034 | **-0.127** | -0.7 | 24% vs 25% | -0.07 | +0.03 | -0.70 | +0.74 | -0.51 | 2 | no | 86 · -0.277 · 1 · 21% |  |
| Reversal · nearest (BB, else OB) | M15 | 3R | none | 211 | -0.033 | **-0.096** | -0.9 | 24% vs 25% | -0.23 | -0.14 | -0.44 | +0.77 | -0.03 | 1 | no | 194 · -0.318 · 0 · 20% |  |
| Reversal · nearest (BB, else OB) | M15 | 5R | D1 trend | 87 | -0.047 | **-0.163** | -0.8 | 15% vs 17% | +0.28 | +0.06 | -0.54 | -0.10 | -0.26 | 2 | no | 86 · -0.425 · 1 · 11% |  |
| Reversal · nearest (BB, else OB) | M15 | 5R | none | 211 | +0.019 | **-0.091** | -0.6 | 17% vs 17% | -0.12 | -0.14 | -0.38 | +0.73 | -0.29 | 1 | no | 194 · -0.393 · 0 · 12% |  |
| Reversal · nearest (BB, else OB) | M5 | 3R | D1 trend | 322 | +0.180 | **+0.014** | +0.2 | 30% vs 25% | -0.19 | +0.18 | +0.10 | +0.14 | -0.25 | 3 | no | 321 · -0.229 · 1 · 25% |  |
| Reversal · nearest (BB, else OB) | M5 | 3R | none | 668 | +0.036 | **-0.110** | -1.8 | 26% vs 25% | -0.17 | -0.18 | -0.12 | +0.07 | -0.18 | 1 | no | 656 · -0.191 · 1 · 25% |  |
| Reversal · nearest (BB, else OB) | M5 | 5R | D1 trend | 322 | +0.114 | **-0.072** | -0.6 | 18% vs 17% | -0.35 | +0.39 | -0.05 | -0.06 | -0.40 | 1 | no | 321 · -0.223 · 1 · 17% |  |
| Reversal · nearest (BB, else OB) | M5 | 5R | none | 668 | -0.030 | **-0.173** | -2.3 | 16% vs 17% | -0.31 | -0.01 | -0.11 | -0.16 | -0.42 | 0 | no | 656 · -0.197 · 1 · 16% |  |
| Continuation · BB | H1 | 3R | D1 trend | 69 | -0.017 | **-0.030** | -0.1 | 24% vs 25% | -0.30 | -0.03 | +0.23 | +0.08 | -0.09 | 2 | no | 69 · +0.058 · 2 · 30% |  |
| Continuation · BB | H1 | 3R | none | 121 | -0.059 | **-0.077** | -0.5 | 22% vs 25% | -0.05 | -0.12 | +0.31 | -0.21 | -0.19 | 1 | no | 112 · +0.091 · 2 · 30% |  |
| Continuation · BB | H1 | 5R | D1 trend | 69 | -0.008 | **-0.019** | -0.1 | 15% vs 17% | -0.30 | +0.30 | +0.02 | +0.62 | -0.54 | 3 | no | 69 · +0.001 · 2 · 14% |  |
| Continuation · BB | H1 | 5R | none | 121 | -0.067 | **-0.082** | -0.4 | 14% vs 17% | -0.11 | -0.02 | +0.17 | +0.18 | -0.46 | 2 | no | 112 · +0.120 · 2 · 18% |  |
| Continuation · BB | M15 | 3R | D1 trend | 170 | -0.180 | **-0.221** | -1.9 | 20% vs 25% | -0.42 | -0.21 | +0.01 | -0.36 | -0.17 | 1 | no | 184 · -0.182 · 0 · 23% |  |
| Continuation · BB | M15 | 3R | none | 314 | -0.023 | **-0.090** | -1.0 | 24% vs 25% | -0.24 | +0.08 | -0.22 | +0.01 | -0.19 | 2 | no | 326 · -0.225 · 1 · 22% |  |
| Continuation · BB | M15 | 5R | D1 trend | 170 | -0.168 | **-0.217** | -1.5 | 14% vs 17% | -0.48 | -0.18 | +0.13 | -0.37 | -0.28 | 1 | no | 184 · -0.121 · 2 · 16% |  |
| Continuation · BB | M15 | 5R | none | 314 | -0.032 | **-0.115** | -1.0 | 15% vs 17% | -0.28 | -0.04 | -0.20 | -0.03 | -0.21 | 0 | no | 326 · -0.170 · 1 · 15% |  |
| Continuation · BB | M5 | 3R | D1 trend | 521 | +0.098 | **-0.012** | -0.2 | 27% vs 25% | -0.28 | -0.28 | +0.19 | -0.03 | +0.31 | 2 | no | 474 · -0.253 · 0 · 23% |  |
| Continuation · BB | M5 | 3R | none | 1025 | +0.030 | **-0.090** | -1.8 | 26% vs 25% | -0.30 | -0.21 | +0.02 | -0.01 | +0.06 | 2 | no | 926 · -0.207 · 0 · 24% |  |
| Continuation · BB | M5 | 5R | D1 trend | 521 | +0.064 | **-0.048** | -0.5 | 17% vs 17% | -0.40 | -0.19 | +0.03 | -0.14 | +0.50 | 2 | no | 474 · -0.285 · 0 · 13% |  |
| Continuation · BB | M5 | 5R | none | 1025 | -0.033 | **-0.151** | -2.4 | 16% vs 17% | -0.30 | -0.22 | -0.20 | -0.01 | +0.05 | 1 | no | 926 · -0.192 · 0 · 15% |  |

**Reversal family walk-forward** (D1-trend rows; choose on past years, trade next year blind, 2023–26): +0.098R over 117 trades, positive in 2 of 4 years → **fail**.
**Continuation family walk-forward** (D1-trend rows; choose on past years, trade next year blind, 2023–26): -0.207R over 107 trades, positive in 2 of 4 years → **fail**.

## Reversal model: did the top start at an H4 POI? (information, D1 trend, all TFs and variants, 3R)

| Top at an H4 POI | Trades | After spread | Hit vs chance | Fresh trades · avg |
|---|---|---|---|---|
| yes | 393 | +0.019 | 29% vs 25% | 402 · -0.241 |
| no | 81 | -0.054 | 26% vs 25% | 79 · -0.264 |

## Checks
- Independent audit (`backtest/chart_v24.py`): 9,652 trades. Zone, MSS, BOS and Liq all finished before the order; entry beyond the Liq (price must take it first); price not already past the entry; reversal MSS candle closes beyond the protected swing, in order; levels on the right sides. **0 problems.**
- Example charts (random picks): `docs/smc_review/v24_*.png`. Some labels overlap where swings sit close together (drawing only).

## Reading
- **The reversal from the breaker (BB) is the best of Ore's own ideas tested so far on GBP/USD + gold.** With the D1 trend:
  - M15, 5R: +0.80R a trade, profit in all 5 years, 32% hits against 17% chance.
  - M15, 3R: +0.47R.
  - H1, 3R: +0.37R.
  - M5, 3R: +0.11R over 115 trades, profit in 4 of 5 years (the only row that passes the consistency rule).
  - Before costs, M15 5R is +0.93R.
- **But the BB rows have few trades** (20–28 on H1/M15 in 5 years across two pairs), **and on EUR/USD + silver they lose** (−0.10 to −0.45R). Only the H1 rows without the trend filter are positive there (+0.15/+0.47R on 33 trades).
- **The reversal from the OB at the top loses** on H1/M15 (−0.37 to −0.63R) and is about zero on M5 (+0.02R, 225 trades).
- **The continuation BB is about zero to negative** on all timeframes.
- **Walk-forwards fail** for both families.
- **"Top at an H4 POI" barely separates anything:** 83% of tops qualify by this definition (+0.02R vs −0.05R). A stricter HTF POI definition from Ore would be needed to test his "best trades come from an HTF POI".
- **Verdict: not proven.** The reversal from the breaker is a real lead on Ore's two markets, but with few trades and failing the fresh-market check.

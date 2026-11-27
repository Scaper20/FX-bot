# Spec v22 result: order block, Toni Iyke and Lingard on real market structure

Spec: `docs/spec-v22-smc-live.md` (committed before the run). Rules: `engine/smc_models.py` (same code as the live scanner). Main test GBP/USD + gold, fresh check EUR/USD + silver, Nov 2021 – Nov 2026, Ore's spreads.

## Order block (H1 MSS, Ore's 2/3-candle block, D1+H4 trend)

| TF | Target | Bias | Trades | No costs | **After spread** | t | Hit vs chance | 2022 | 2023 | 2024 | 2025 | 2026 | Yrs + | Consistent | Fresh (trades · avg · yrs+) | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H1 | 3R | on | 28 | -0.571 | **-0.591** | -2.6 | 11% vs 25% | -1.00 | -0.52 | +0.26 | -1.00 | -1.00 | 1 | no | 29 · -0.313 · 1 |  |
| H1 | 3R | off | 115 | +0.145 | **+0.117** | +0.7 | 28% vs 25% | +0.22 | +0.08 | +0.18 | -0.16 | +0.62 | 4 | YES | 141 · -0.217 · 1 | fresh FAIL |

Walk-forward (choose on past years, trade next year blind, 2023–26): -0.177R over 11 trades, positive in 0 of 4 years → **fail**.

## Toni Iyke

| Structure | TF | Target | Bias | Trades | No costs | **After spread** | t | Hit vs chance | 2022 | 2023 | 2024 | 2025 | 2026 | Yrs + | Consistent | Fresh (trades · avg · yrs+) | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| dbos | H1 | 5R | on | 155 | +0.134 | **+0.041** | +0.2 | 18% vs 17% | -0.10 | +0.49 | +0.01 | +0.08 | -0.37 | 3 | no | 177 · +0.022 · 3 |  |
| dbos | H1 | 5R | off | 329 | +0.186 | **+0.109** | +0.9 | 18% vs 17% | -0.12 | +0.12 | +0.09 | +0.35 | +0.28 | 4 | YES | 337 · -0.130 · 0 | fresh FAIL |
| dbos | H1 | liq | on | 155 | +0.126 | **+0.028** | +0.2 | 32% vs 31% | +0.26 | +0.00 | +0.27 | +0.02 | -0.45 | 4 | YES | 177 · -0.145 · 2 | fresh FAIL |
| dbos | H1 | liq | off | 329 | +0.208 | **+0.041** | +0.3 | 32% vs 30% | +0.06 | -0.06 | -0.13 | +0.49 | -0.11 | 2 | no | 337 · -0.204 · 0 |  |
| dbos | M15 | 5R | on | 540 | -0.064 | **-0.174** | -2.1 | 15% vs 17% | -0.37 | -0.24 | -0.11 | -0.22 | +0.16 | 1 | no | 574 · -0.143 · 2 |  |
| dbos | M15 | 5R | off | 1121 | -0.029 | **-0.137** | -2.3 | 15% vs 17% | -0.37 | -0.29 | -0.08 | -0.08 | +0.12 | 1 | no | 1129 · -0.177 · 2 |  |
| dbos | M15 | liq | on | 540 | -0.083 | **-0.183** | -2.9 | 30% vs 32% | -0.33 | -0.09 | -0.19 | -0.21 | -0.06 | 0 | no | 574 · -0.111 · 2 |  |
| dbos | M15 | liq | off | 1121 | -0.061 | **-0.160** | -3.3 | 30% vs 31% | -0.37 | -0.12 | -0.15 | -0.18 | +0.01 | 1 | no | 1129 · -0.112 · 1 |  |
| mss | H1 | 5R | on | 148 | +0.050 | **-0.045** | -0.3 | 17% vs 17% | -0.08 | -0.40 | +0.81 | -0.52 | -0.04 | 1 | no | 156 · -0.138 · 2 |  |
| mss | H1 | 5R | off | 313 | -0.043 | **-0.105** | -0.9 | 15% vs 17% | -0.10 | -0.31 | +0.29 | -0.04 | -0.18 | 1 | no | 311 · -0.201 · 1 |  |
| mss | H1 | liq | on | 148 | -0.051 | **-0.151** | -1.1 | 27% vs 28% | -0.12 | -0.35 | +0.31 | -0.39 | -0.20 | 1 | no | 156 · -0.204 · 2 |  |
| mss | H1 | liq | off | 313 | -0.116 | **-0.180** | -2.0 | 26% vs 28% | -0.23 | -0.23 | -0.11 | -0.10 | -0.17 | 0 | no | 311 · -0.213 · 0 |  |
| mss | M15 | 5R | on | 469 | +0.103 | **+0.029** | +0.3 | 17% vs 17% | -0.09 | +0.20 | -0.09 | -0.01 | +0.25 | 2 | no | 468 · -0.121 · 0 |  |
| mss | M15 | 5R | off | 1014 | +0.005 | **-0.089** | -1.4 | 16% vs 17% | -0.08 | +0.01 | -0.15 | -0.10 | -0.09 | 1 | no | 1016 · -0.171 · 1 |  |
| mss | M15 | liq | on | 469 | -0.013 | **-0.112** | -1.5 | 30% vs 30% | -0.22 | +0.07 | -0.27 | -0.20 | +0.21 | 2 | no | 468 · -0.096 · 0 |  |
| mss | M15 | liq | off | 1014 | -0.034 | **-0.142** | -2.8 | 28% vs 29% | -0.11 | -0.07 | -0.22 | -0.17 | -0.09 | 0 | no | 1016 · -0.150 · 0 |  |

Walk-forward (choose on past years, trade next year blind, 2023–26): +0.091R over 188 trades, positive in 2 of 4 years → **fail**.

## Lingard

| TF | Target | Bias | Trades | No costs | **After spread** | t | Hit vs chance | 2022 | 2023 | 2024 | 2025 | 2026 | Yrs + | Consistent | Fresh (trades · avg · yrs+) | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H1 | 5R | on | 56 | +0.004 | **-0.028** | -0.1 | 15% vs 17% | -0.20 | +0.15 | +0.22 | -1.00 | +0.60 | 3 | no | 65 · +0.006 · 2 |  |
| H1 | 5R | off | 134 | -0.092 | **-0.119** | -0.7 | 13% vs 17% | -0.49 | -0.62 | +0.33 | -0.39 | +0.41 | 2 | no | 131 · +0.087 · 4 |  |
| H1 | liq | on | 6 | -0.488 | **-0.490** | -1.0 | 0% vs 14% | -1.00 | -1.00 | -1.00 | — | +0.53 | 1 | no | 8 · +0.951 · 2 |  |
| H1 | liq | off | 18 | -0.014 | **-0.059** | -0.1 | 12% vs 13% | -0.04 | -1.00 | +1.39 | -1.00 | +0.02 | 2 | no | 15 · +0.955 · 3 |  |
| H4 | 5R | on | 17 | -0.386 | **-0.390** | -1.0 | 7% vs 17% | -1.00 | -1.00 | -0.08 | +0.20 | +0.26 | 2 | no | 33 · +0.384 · 3 |  |
| H4 | 5R | off | 47 | -0.008 | **-0.028** | -0.1 | 14% vs 17% | -0.12 | +0.33 | +0.96 | -0.26 | -0.49 | 2 | no | 60 · +0.287 · 2 |  |
| H4 | liq | on | 4 | -1.000 | **-1.000** | — | 0% vs 14% | — | -1.00 | — | -1.00 | -1.00 | 0 | no | 7 · +1.473 · 2 |  |
| H4 | liq | off | 7 | -0.076 | **-0.143** | -0.2 | 14% vs 14% | +2.00 | -1.00 | — | -1.00 | -1.00 | 1 | no | 11 · +0.574 · 2 |  |

Walk-forward (choose on past years, trade next year blind, 2023–26): -0.059R over 24 trades, positive in 1 of 4 years → **fail**.


## Checks
- Independent audit (`backtest/chart_v22.py`): 12,466 trades; zone and structure complete by the decision candle, Toni's inducement close beyond the structure candle, Toni's POI body untouched by the inducement leg, levels on the right sides. **0 problems.**
- Example charts (random picks): `docs/smc_review/v22_*.png`.
- Note: the order block here uses the 5-day hold of this spec (v21 used 3 days); the results are identical (all trades end within 3 days).

## Reading
- **Order block (live version, D1 + H4 trend):** 28 trades in 5 years, −0.59R. Without the trend filter +0.12R (115 trades) but −0.22R on EUR/USD + silver.
- **Toni Iyke:** multiple BOS on H1 is the best part: with the D1 trend and the swing-point target +0.03R (155 trades, 4 of 5 years, target hit 32% vs 31% chance), without the trend and 5R +0.11R (329 trades, 4/5 years). Both fail on EUR/USD + silver (−0.15R, −0.13R). MSS rows and all M15 rows negative. Before costs H1 multiple BOS is +0.13 to +0.21R, so the spread takes most of it.
- **Lingard:** few trades (17–56 with the D1 trend in 5 years) and about zero or negative on GBP/USD + gold. His 1:5 rule with the next-liquidity target leaves 4–18 trades. Oddly positive on EUR/USD + silver (+0.29 to +0.38R on 33–60 trades), too few to mean anything.
- Walk-forwards fail for all three. **No edge.** Going live by Ore's decision, with these numbers shown on every card.

# Spec v20 result: Toni Iyke and Lingard SMC models

Spec: `docs/spec-v20-toni-lingard.md` (committed before the run). Main test GBP/USD + gold, fresh check EUR/USD + silver, Nov 2021 – Nov 2026, Ore's spreads, 1-minute scoring.

## Toni Iyke

| Structure | TF | POI rule | Target | Bias | Trades | No costs | **After spread** | t | Hit vs chance | 2022 | 2023 | 2024 | 2025 | 2026 | Yrs + | Consistent | Fresh mkts (trades · avg · yrs+ · hit vs ch) | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| dbos | H1 | breaker_first | 5R | bias | 517 | -0.078 | **-0.130** | -1.5 | 15% vs 17% | -0.37 | -0.16 | -0.30 | +0.14 | +0.07 | 2 | no |  |  |
| dbos | H1 | breaker_first | 5R | no bias | 995 | -0.076 | **-0.167** | -2.7 | 15% vs 17% | -0.23 | -0.14 | -0.18 | -0.14 | -0.03 | 0 | no |  |  |
| dbos | H1 | breaker_first | liq | bias | 517 | -0.121 | **-0.175** | -2.4 | 26% vs 27% | -0.17 | -0.13 | -0.37 | -0.02 | -0.19 | 0 | no |  |  |
| dbos | H1 | breaker_first | liq | no bias | 995 | -0.072 | **-0.194** | -3.5 | 24% vs 26% | -0.10 | -0.09 | -0.36 | -0.21 | -0.16 | 0 | no |  |  |
| dbos | H1 | closest | 5R | bias | 520 | -0.031 | **-0.096** | -1.1 | 15% vs 17% | -0.32 | -0.05 | -0.20 | +0.14 | -0.06 | 1 | no |  |  |
| dbos | H1 | closest | 5R | no bias | 1002 | -0.047 | **-0.139** | -2.2 | 15% vs 17% | -0.21 | -0.12 | -0.10 | -0.10 | -0.10 | 0 | no |  |  |
| dbos | H1 | closest | liq | bias | 520 | -0.095 | **-0.161** | -2.2 | 27% vs 27% | -0.16 | -0.09 | -0.35 | -0.00 | -0.20 | 0 | no |  |  |
| dbos | H1 | closest | liq | no bias | 1002 | -0.057 | **-0.176** | -3.2 | 25% vs 26% | -0.09 | -0.09 | -0.33 | -0.18 | -0.16 | 0 | no |  |  |
| dbos | M15 | breaker_first | 5R | bias | 2001 | +0.019 | **-0.115** | -2.6 | 17% vs 17% | -0.16 | +0.00 | -0.21 | -0.05 | -0.21 | 1 | no |  |  |
| dbos | M15 | breaker_first | 5R | no bias | 4048 | +0.024 | **-0.108** | -3.4 | 17% vs 17% | -0.19 | -0.13 | -0.11 | -0.09 | -0.04 | 0 | no |  |  |
| dbos | M15 | breaker_first | liq | bias | 2001 | -0.006 | **-0.133** | -3.6 | 29% vs 29% | -0.18 | +0.00 | -0.22 | -0.21 | -0.07 | 1 | no |  |  |
| dbos | M15 | breaker_first | liq | no bias | 4048 | -0.008 | **-0.138** | -5.2 | 28% vs 28% | -0.19 | -0.15 | -0.15 | -0.21 | +0.02 | 1 | no |  |  |
| dbos | M15 | closest | 5R | bias | 2013 | +0.019 | **-0.125** | -2.8 | 17% vs 17% | -0.18 | -0.01 | -0.21 | -0.07 | -0.19 | 0 | no |  |  |
| dbos | M15 | closest | 5R | no bias | 4076 | +0.025 | **-0.111** | -3.5 | 17% vs 17% | -0.19 | -0.15 | -0.10 | -0.10 | -0.02 | 0 | no |  |  |
| dbos | M15 | closest | liq | bias | 2013 | +0.004 | **-0.129** | -3.5 | 29% vs 29% | -0.17 | -0.01 | -0.22 | -0.20 | -0.06 | 0 | no |  |  |
| dbos | M15 | closest | liq | no bias | 4076 | +0.000 | **-0.132** | -5.0 | 28% vs 29% | -0.17 | -0.16 | -0.14 | -0.20 | +0.03 | 1 | no |  |  |
| mss | H1 | breaker_first | 5R | bias | 334 | -0.097 | **-0.164** | -1.5 | 15% vs 17% | -0.18 | -0.25 | -0.28 | +0.19 | -0.37 | 1 | no |  |  |
| mss | H1 | breaker_first | 5R | no bias | 653 | -0.026 | **-0.098** | -1.2 | 16% vs 17% | -0.13 | +0.06 | +0.03 | -0.07 | -0.31 | 2 | no |  |  |
| mss | H1 | breaker_first | liq | bias | 334 | -0.097 | **-0.148** | -1.5 | 23% vs 24% | -0.19 | -0.14 | -0.22 | -0.05 | -0.01 | 0 | no |  |  |
| mss | H1 | breaker_first | liq | no bias | 653 | -0.111 | **-0.169** | -2.4 | 22% vs 24% | -0.21 | -0.11 | -0.11 | -0.16 | -0.15 | 0 | no |  |  |
| mss | H1 | closest | 5R | bias | 335 | -0.028 | **-0.094** | -0.8 | 16% vs 17% | -0.18 | +0.06 | -0.27 | +0.19 | -0.26 | 2 | no |  |  |
| mss | H1 | closest | 5R | no bias | 657 | +0.028 | **-0.053** | -0.6 | 17% vs 17% | -0.14 | +0.20 | +0.02 | -0.08 | -0.19 | 2 | no |  |  |
| mss | H1 | closest | liq | bias | 335 | -0.066 | **-0.116** | -1.2 | 25% vs 25% | -0.15 | -0.06 | -0.33 | -0.01 | +0.15 | 1 | no |  |  |
| mss | H1 | closest | liq | no bias | 657 | -0.068 | **-0.127** | -1.8 | 24% vs 25% | -0.11 | -0.07 | -0.19 | -0.12 | -0.02 | 0 | no |  |  |
| mss | M15 | breaker_first | 5R | bias | 1233 | +0.063 | **-0.091** | -1.6 | 17% vs 17% | -0.11 | -0.10 | -0.23 | -0.16 | +0.12 | 1 | no |  |  |
| mss | M15 | breaker_first | 5R | no bias | 2466 | -0.001 | **-0.145** | -3.6 | 16% vs 17% | -0.16 | -0.21 | -0.29 | -0.16 | +0.07 | 1 | no |  |  |
| mss | M15 | breaker_first | liq | bias | 1233 | +0.031 | **-0.136** | -2.8 | 27% vs 27% | -0.09 | -0.11 | -0.25 | -0.17 | -0.06 | 0 | no |  |  |
| mss | M15 | breaker_first | liq | no bias | 2466 | -0.029 | **-0.175** | -5.2 | 26% vs 27% | -0.17 | -0.18 | -0.29 | -0.18 | -0.05 | 0 | no |  |  |
| mss | M15 | closest | 5R | bias | 1244 | +0.059 | **-0.096** | -1.7 | 17% vs 17% | -0.06 | -0.13 | -0.27 | -0.17 | +0.12 | 1 | no |  |  |
| mss | M15 | closest | 5R | no bias | 2492 | -0.005 | **-0.144** | -3.6 | 16% vs 17% | -0.10 | -0.23 | -0.31 | -0.17 | +0.07 | 1 | no |  |  |
| mss | M15 | closest | liq | bias | 1244 | +0.025 | **-0.135** | -2.9 | 28% vs 28% | -0.06 | -0.13 | -0.26 | -0.19 | -0.05 | 0 | no |  |  |
| mss | M15 | closest | liq | no bias | 2492 | -0.030 | **-0.172** | -5.2 | 27% vs 28% | -0.12 | -0.20 | -0.30 | -0.18 | -0.06 | 0 | no |  |  |

**Toni Iyke: 0 of 32 rows consistent; 0 also held on EUR/USD + silver.** Walk-forward (choose on past years, trade next year blind, 2023–26): -0.171R over 415 trades, positive in 1 of 4 years → **fail**.

All Toni Iyke trades pooled (GBP/USD + gold): 32,778 trades, -0.011R before costs, **-0.138R after spread**, target hit 21.7% vs 22.1% chance.

## Lingard

| Pattern | TF | Target | Bias | Trades | No costs | **After spread** | t | Hit vs chance | 2022 | 2023 | 2024 | 2025 | 2026 | Yrs + | Consistent | Fresh mkts (trades · avg · yrs+ · hit vs ch) | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | H1 | 5R | bias | 93 | +0.004 | **-0.034** | -0.2 | 15% vs 17% | -0.23 | +0.81 | -0.57 | +0.16 | +0.09 | 3 | no |  |  |
| A | H1 | 5R | no bias | 171 | +0.041 | **+0.011** | +0.1 | 16% vs 17% | +0.03 | +0.11 | -0.24 | +0.64 | -0.06 | 3 | no |  |  |
| A | H1 | liq | bias | 11 | -0.343 | **-0.369** | -0.6 | 9% vs 14% | +0.16 | -1.00 | -1.00 | -1.00 | — | 1 | no |  |  |
| A | H1 | liq | no bias | 14 | -0.484 | **-0.504** | -1.0 | 7% vs 14% | +0.16 | -1.00 | -1.00 | -1.00 | — | 1 | no |  |  |
| A | H4 | 5R | bias | 33 | -0.091 | **-0.118** | -0.3 | 15% vs 17% | -0.36 | +0.96 | -0.26 | +0.42 | -1.00 | 2 | no |  |  |
| A | H4 | 5R | no bias | 53 | +0.060 | **+0.033** | +0.1 | 16% vs 17% | +0.05 | +0.17 | +0.35 | -0.19 | -0.47 | 3 | no |  |  |
| A | H4 | liq | bias | 2 | +1.155 | **+1.081** | +0.5 | 0% vs 13% | +3.16 | -1.00 | — | — | — | 1 | no |  |  |
| A | H4 | liq | no bias | 4 | +0.078 | **+0.041** | +0.0 | 0% vs 13% | +3.16 | -1.00 | — | — | -1.00 | 1 | no |  |  |
| B | H1 | 5R | bias | 144 | +0.019 | **-0.017** | -0.1 | 14% vs 17% | -0.07 | +0.17 | +0.24 | -0.20 | -0.36 | 2 | no |  |  |
| B | H1 | 5R | no bias | 281 | -0.025 | **-0.058** | -0.5 | 14% vs 17% | +0.25 | -0.17 | +0.05 | -0.21 | -0.39 | 2 | no |  |  |
| B | H1 | liq | bias | 14 | -0.506 | **-0.519** | -1.1 | 7% vs 13% | -1.00 | -1.00 | -1.00 | -1.00 | +1.24 | 1 | no |  |  |
| B | H1 | liq | no bias | 33 | -0.573 | **-0.592** | -2.1 | 6% vs 13% | +0.35 | -1.00 | -1.00 | -1.00 | +0.35 | 2 | no |  |  |
| B | H4 | 5R | bias | 75 | +0.114 | **+0.088** | +0.4 | 15% vs 17% | +0.03 | -0.40 | +0.36 | +0.42 | -1.00 | 3 | no |  |  |
| B | H4 | 5R | no bias | 115 | +0.312 | **+0.280** | +1.3 | 20% vs 17% | +0.71 | -0.56 | +0.68 | +0.84 | -1.00 | 3 | no |  |  |
| B | H4 | liq | bias | 13 | +0.365 | **+0.342** | +0.4 | 9% vs 13% | +0.39 | -1.00 | +2.04 | -1.00 | — | 2 | no |  |  |
| B | H4 | liq | no bias | 20 | +1.479 | **+1.409** | +1.7 | 28% vs 13% | +2.22 | -1.00 | +3.00 | +1.15 | -1.00 | 3 | no |  |  |

**Lingard: 0 of 16 rows consistent; 0 also held on EUR/USD + silver.** Walk-forward (choose on past years, trade next year blind, 2023–26): -0.429R over 56 trades, positive in 1 of 4 years → **fail**.

All Lingard trades pooled (GBP/USD + gold): 691 trades, +0.063R before costs, **+0.030R after spread**, target hit 15.4% vs 16.3% chance.

## By market (all rows, bias on)

| Market | Toni trades | Toni avg R | Lingard trades | Lingard avg R |
|---|---|---|---|---|
| GBPUSD | 8,232 | -0.136 | 203 | +0.068 |
| XAUUSD | 8,162 | -0.113 | 182 | -0.117 |
| EURUSD | 8,330 | -0.105 | 183 | -0.003 |
| XAGUSD | 7,778 | -0.145 | 155 | -0.443 |

## Checks

- Independent audit (`backtest/chart_toni_lingard.py`): 68,368 trades. Toni: structure candle before the decision, decision candle body-closes beyond the structure candle's close, POI body untouched by the inducement leg, target = the extreme in between. Lingard: liquidity is a real swing known in time, order block beyond the liquidity and within 1.5 ATR, entry at its near edge. Stops beyond entry by more than 2 spreads. **0 problems.**
- Example charts (GBP/USD, GMT+0): `docs/toni_lingard_examples/`. Unit tests: `tests/test_toni_lingard.py`.
- Closest Lingard near-miss, checked after the result for information: H4 pattern B, 5R, no bias: +0.28R on GBP/USD + gold (115 trades, 3 of 5 years, +0.15R without its 3 best trades), **−0.08R on EUR/USD + silver** (110 trades, hit 15% vs 17% chance).

## Reading

- **Toni Iyke: no edge.** Before costs his model is at zero (−0.01R a trade over 32,778 trades) and hits its targets at the chance rate (21.7% vs 22.1%). After the spread every row is negative (−0.05R to −0.19R). The breaker stop (just beyond the broken swing candle) is often only a few pips, so the spread takes a big share of each trade; on M15 some rows are slightly positive before costs (+0.02R to +0.06R) and clearly negative after.
- **The official-vs-classes POI conflict doesn't matter:** "closest POI" (classes) and "unmitigated breaker first" (official/explainer) give almost the same trades and results (−0.13R vs −0.14R).
- **Lingard: no edge, and few trades.** His 1:5 minimum with the next-liquidity target leaves only 2–33 trades per row in 5 years; with a fixed 5R target, 33–281 trades per row and about zero overall (+0.03R after spread, target hit 15.4% vs 16.3% chance). No row is consistent; the best near-miss failed on EUR/USD + silver.
- In this coding Lingard's Pattern B came out more common than Pattern A, the opposite of what he says. His eye may define the "first pullback" more loosely than a 5-bar swing. That is a limit of any mechanical version of a discretionary method.
- **Not tested** (discretionary, no objective rule): Toni's HTF zone + trendline confirmation, "don't trade inside a liquidity pool", trendline/range targets; Lingard's 3M → W → D top-down bias, breakers, fake zones, lower-timeframe confirmation entries. These can be measured through Ore's own reviews instead (review tags on the setup page).
- **Verdict: neither strategy goes on the site as a recommended strategy.** Same result as every mechanical SMC/ICT test before (v4, v6, v14, v16 fresh markets, v17): at chance before costs, negative after.

# Spec v23 result: IRL → ERL bias for the order-block strategy

Spec: `docs/spec-v23-irl-erl.md` (committed before the run). H1 MSS, Ore's 2/3-candle order block, 3R (OB rows) or market entry at the MSS close (E1 rows, for information). Main GBP/USD + gold, fresh EUR/USD + silver, Nov 2021 – Nov 2026, Ore's spreads.

## Order-block entry (the live strategy)

| Bias | Trades | No costs | **After spread** | t | Hit vs 25% | 2022 | 2023 | 2024 | 2025 | 2026 | Yrs + | Consistent | Fresh (trades · avg · yrs+ · hit) | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| IRL/ERL H4 | 66 | -0.013 | **-0.036** | -0.2 | 25% | +0.13 | +0.14 | -1.00 | -0.08 | +1.59 | 3 | no | 77 · -0.117 · 1 · 20% |  |
| IRL/ERL D1 | 73 | +0.310 | **+0.286** | +1.3 | 32% | +0.58 | +0.44 | -0.01 | -0.17 | +0.98 | 3 | no | 85 · -0.257 · 0 · 18% |  |
| IRL/ERL H4 + D1 agree | 48 | +0.107 | **+0.087** | +0.3 | 28% | +0.32 | +0.38 | -1.00 | +0.01 | +1.37 | 4 | YES | 50 · -0.147 · 1 · 20% | fresh FAIL |
| D1 + H4 trend (live rule) | 28 | -0.571 | **-0.591** | -2.6 | 11% | -1.00 | -0.52 | +0.26 | -1.00 | -1.00 | 1 | no | 29 · -0.313 · 1 · 15% |  |
| IRL/ERL H4 + D1 trend | 24 | +0.500 | **+0.459** | +1.2 | 38% | +1.27 | +0.21 | -1.00 | +0.00 | +1.51 | 3 | no | 32 · +0.095 · 3 · 27% |  |
| none | 115 | +0.145 | **+0.117** | +0.7 | 28% | +0.22 | +0.08 | +0.18 | -0.16 | +0.62 | 4 | YES | 141 · -0.217 · 1 · 19% | fresh FAIL |

## Market entry at the MSS close (does the bias point the right way?)

| Bias | Trades | No costs | **After spread** | t | Hit vs 25% | 2022 | 2023 | 2024 | 2025 | 2026 | Yrs + | Consistent | Fresh (trades · avg · yrs+ · hit) | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| IRL/ERL H4 | 457 | -0.002 | **-0.010** | -0.2 | 15% | +0.03 | -0.09 | +0.03 | -0.06 | +0.12 | 3 | no | 486 · -0.081 · 1 · 12% |  |
| IRL/ERL D1 | 530 | -0.013 | **-0.021** | -0.4 | 12% | -0.05 | -0.05 | -0.04 | -0.02 | +0.05 | 1 | no | 547 · -0.099 · 0 · 10% |  |
| IRL/ERL H4 + D1 agree | 293 | -0.026 | **-0.035** | -0.5 | 15% | -0.09 | -0.12 | -0.06 | -0.05 | +0.17 | 1 | no | 277 · -0.204 · 0 · 9% |  |
| D1 + H4 trend (live rule) | 220 | -0.032 | **-0.040** | -0.5 | 12% | +0.15 | +0.07 | +0.01 | -0.33 | -0.01 | 3 | no | 205 · -0.101 · 1 · 9% |  |
| IRL/ERL H4 + D1 trend | 177 | +0.212 | **+0.202** | +2.0 | 22% | +0.66 | -0.09 | +0.34 | -0.11 | +0.27 | 3 | no | 210 · -0.019 · 2 · 13% |  |
| none | 894 | -0.014 | **-0.022** | -0.6 | 13% | +0.00 | -0.02 | -0.03 | -0.08 | +0.07 | 2 | no | 953 · -0.047 · 2 · 11% |  |

IRL/ERL family walk-forward (order-block entry; choose the variant on past years, trade next year blind, 2023–26): +1.658R over 3 trades, positive in 1 of 4 years → **fail**.

## Reading
- **IRL/ERL is a far better bias than the D1 + H4 trend for this strategy.** Same order-block trades: trend bias −0.59R (28 trades); IRL/ERL D1 +0.29R (73 trades); IRL/ERL H4 + D1 agreeing +0.09R (48 trades, 4 of 5 years: the only consistent row); IRL/ERL H4 with the D1 trend +0.46R (24 trades).
- With market entries (many more trades) the IRL/ERL H4 + D1 trend filter gives +0.20R over 177 trades (t 2.0, 3 of 5 years): the strongest bias signal measured on these markets so far.
- **But it does not hold on EUR/USD + silver**: the consistent row loses −0.15R there (50 trades), D1 alone −0.26R; only IRL/ERL H4 + D1 trend is positive there (+0.10R, 32 trades, 3/5 years), and its market-entry version is −0.02R (210 trades). Walk-forward fails (too few trades per year to choose from).
- **Verdict:** not proven, so by the pre-registered rule it does not replace the live D1 + H4 trend bias. It is shown on every order-block card and in the tracking line (H4 and D1 state, last liquidity event, next draw) so Ore can judge it live. Worth watching: IRL/ERL H4 + D1 trend.

# Spec v14 result: Inter Equity liquidity strategy, alone and paired with CRT

Spec: `docs/spec-v14-liquidity.md` (committed before any run). GBP/USD + gold, Nov 2021 – Nov 2026, Exness candles (GMT+0), Ore's spreads, 1-minute outcomes. Avg = average R per trade after spread. Hit = final target reached before the stop; chance = what a random market gives for the same distances. Mgmt A = all out at the target; B = half at the nearest liquidity, stop to entry, rest at the target.

## induce → trap alone

22 rows; consistent: **0**. Best 12 by average:

| Row | Trades | Avg R | 2022 | 2023 | 2024 | 2025 | 2026 | Years + | Hit vs chance | Consistent |
|---|---|---|---|---|---|---|---|---|---|---|
| H4 trap · daily bias · mgmt B | 27 | **+0.33** | +0.02 | -1.00 | +1.18 | +0.34 | +0.93 | 4 | 27% vs 21% | no |
| H1 trap · daily bias · mgmt B | 189 | **+0.02** | +0.13 | -0.03 | -0.57 | +0.38 | +0.09 | 3 | 15% vs 19% | no |
| H4 trap · all · mgmt B | 140 | **+0.00** | -0.20 | -0.11 | +0.05 | -0.06 | +0.19 | 2 | 16% vs 19% | no |
| M15 trap · NY session · mgmt B | 860 | **-0.01** | +0.02 | +0.02 | -0.03 | -0.09 | +0.04 | 3 | 10% vs 18% | no |
| M15 trap · daily bias · mgmt B | 1002 | **-0.05** | -0.24 | -0.12 | +0.06 | -0.03 | +0.19 | 2 | 11% vs 17% | no |
| H1 trap · all · mgmt B | 614 | **-0.06** | -0.16 | -0.09 | -0.23 | +0.10 | +0.12 | 2 | 13% vs 19% | no |
| M15 trap · all · mgmt B | 2995 | **-0.09** | -0.13 | -0.04 | -0.13 | -0.07 | -0.06 | 0 | 11% vs 17% | no |
| H1 trap · daily bias · mgmt A | 460 | **-0.10** | -0.03 | +0.10 | -0.36 | -0.20 | +0.00 | 2 | 11% vs 15% | no |
| H1 trap · NY session · mgmt B | 244 | **-0.10** | -0.30 | -0.17 | -0.26 | -0.02 | +0.27 | 1 | 14% vs 19% | no |
| H4 trap · all · mgmt A | 504 | **-0.11** | -0.06 | -0.32 | -0.31 | -0.41 | +0.50 | 1 | 12% vs 14% | no |
| H1 trap · all · mgmt A | 1660 | **-0.12** | +0.02 | -0.20 | -0.16 | -0.10 | -0.15 | 1 | 11% vs 15% | no |
| M15 trap · NY session · mgmt A | 2145 | **-0.12** | -0.08 | -0.12 | -0.05 | -0.11 | -0.18 | 0 | 8% vs 15% | no |

All 22 rows together: 61,385 trades (rows overlap), median row average -0.12.

## 4-candle sniper alone

52 rows; consistent: **1**. Best 12 by average:

| Row | Trades | Avg R | 2022 | 2023 | 2024 | 2025 | 2026 | Years + | Hit vs chance | Consistent |
|---|---|---|---|---|---|---|---|---|---|---|
| H4 mid · daily bias · mgmt A | 183 | **+0.52** | -0.06 | +0.11 | +3.20 | +0.35 | -0.05 | 3 | 11% vs 8% | no |
| H4 edge · daily bias · mgmt A | 263 | **+0.19** | -0.26 | +0.08 | +1.57 | -0.02 | -0.15 | 2 | 15% vs 13% | no |
| H4 edge · all · mgmt B | 215 | **+0.04** | -0.17 | +0.13 | +0.10 | +0.08 | +0.02 | 4 | 18% vs 17% | YES |
| H4 edge · all · mgmt A | 831 | **+0.03** | -0.14 | +0.18 | +0.35 | -0.23 | -0.07 | 2 | 15% vs 13% | no |
| H1 edge · daily bias · mgmt A | 1033 | **-0.01** | -0.16 | +0.55 | -0.30 | -0.13 | -0.01 | 1 | 13% vs 14% | no |
| H1 edge · NY session · mgmt B | 386 | **-0.03** | +0.05 | -0.12 | -0.09 | +0.08 | +0.01 | 3 | 13% vs 17% | no |
| D1 mid · all · mgmt A | 110 | **-0.04** | +0.63 | +0.37 | -0.27 | +0.06 | -0.56 | 3 | 15% vs 11% | no |
| H1 edge · daily bias · mgmt B | 438 | **-0.05** | -0.16 | +0.52 | -0.30 | -0.21 | -0.28 | 1 | 14% vs 15% | no |
| H4 mid · all · mgmt A | 606 | **-0.07** | -0.23 | +0.02 | +0.53 | -0.28 | -0.47 | 2 | 10% vs 9% | no |
| H1 mid · daily bias · mgmt A | 695 | **-0.08** | -0.38 | +0.50 | -0.18 | -0.17 | -0.25 | 1 | 11% vs 11% | no |
| H1 edge · NY session · mgmt A | 1097 | **-0.10** | +0.04 | -0.04 | -0.34 | -0.29 | +0.22 | 2 | 11% vs 15% | no |
| H1 edge · all · mgmt B | 1350 | **-0.10** | -0.19 | +0.12 | -0.19 | -0.11 | -0.17 | 1 | 13% vs 15% | no |

All 52 rows together: 189,308 trades (rows overlap), median row average -0.20.

## with CRT

12 rows; consistent: **0**. Best 12 by average:

| Row | Trades | Avg R | 2022 | 2023 | 2024 | 2025 | 2026 | Years + | Hit vs chance | Consistent |
|---|---|---|---|---|---|---|---|---|---|---|
| 4-candle sniper · CRT D1→M15 · CRT targets | 112 | **-0.03** | -0.14 | +0.29 | +0.52 | -0.19 | -0.92 | 2 | 6% vs 6% | no |
| induce → trap · CRT D1→M15 · CRT targets | 181 | **-0.13** | -0.15 | +0.23 | -0.78 | -0.09 | +0.00 | 2 | 9% vs 9% | no |
| induce → trap · CRT H4→M5 · B | 503 | **-0.16** | -0.19 | -0.13 | +0.08 | -0.26 | -0.25 | 1 | 11% vs 17% | no |
| 4-candle sniper · CRT H4→M5 · A | 655 | **-0.17** | +0.10 | -0.47 | -0.25 | -0.10 | -0.29 | 1 | 13% vs 15% | no |
| induce → trap · CRT D1→M15 · B | 108 | **-0.17** | -0.32 | -0.12 | -0.55 | +0.20 | -0.11 | 1 | 6% vs 17% | no |
| induce → trap · CRT H4→M5 · A | 841 | **-0.19** | -0.38 | -0.25 | +0.04 | -0.18 | -0.15 | 1 | 10% vs 15% | no |
| 4-candle sniper · CRT H4→M5 · B | 434 | **-0.21** | -0.15 | -0.40 | -0.35 | +0.03 | -0.38 | 1 | 13% vs 16% | no |
| 4-candle sniper · CRT D1→M15 · A | 114 | **-0.30** | -0.33 | +0.24 | -0.24 | -0.36 | -1.00 | 1 | 10% vs 15% | no |
| induce → trap · CRT D1→M15 · A | 188 | **-0.31** | -0.23 | -0.09 | -0.83 | -0.23 | -0.27 | 0 | 9% vs 15% | no |
| 4-candle sniper · CRT H4→M5 · CRT targets | 561 | **-0.32** | -0.09 | -0.64 | -0.30 | -0.35 | -0.32 | 0 | 9% vs 10% | no |
| induce → trap · CRT H4→M5 · CRT targets | 694 | **-0.34** | -0.59 | -0.44 | -0.03 | -0.33 | -0.30 | 0 | 8% vs 11% | no |
| 4-candle sniper · CRT D1→M15 · B | 57 | **-0.40** | -0.46 | -0.14 | -0.39 | -0.46 | -0.77 | 0 | 13% vs 16% | no |

All 12 rows together: 4,448 trades (rows overlap), median row average -0.20.

## Walk-forward (choose on past years, trade the next year blind)

| Family | Units | Blind avg R | Trades | Blind years + of 4 | Verdict |
|---|---|---|---|---|---|
| 4-candle sniper alone | 72 | -0.372 | 364 | 1 | fail |
| induce → trap alone | 32 | +0.015 | 216 | 1 | fail |
| with CRT | 24 | -0.362 | 119 | 0 | fail |

## Fresh-market check (spec addendum)
The only consistent row, **sniper H4, entry at C3's extreme, management B** (+0.04R, 215 trades, 4 of 5 years), frozen and run on EUR/USD + silver: **−0.17R a trade over 285 trades, negative in all 5 years, final target hit 9% vs 16% chance (EUR/USD −0.09R, silver −0.24R). FAIL.**

## Detection and charts
- **Audit:** all 341,610 setups (302,893 sniper, 38,717 induce→trap) rechecked from raw candles by separate code (`backtest/audit_liquidity.py`): **0 problems**. C2 sweeps C1 and closes back, C3 inside C2 with the right colour, entry at C3's extreme or zone middle, stop 2 spreads beyond C2, order only during C4; for induce→trap: a real swing broken, the retail swing first after the leg, the most recent liquidity block from the left, targets at intact liquidity and at least 1:3.
- **Charts:** `docs/liquidity_examples/` (real candles, GMT+0 like MT5), checked by eye against his diagrams. Tests: `tests/test_liquidity.py`.

## Reading
- **Alone, neither model has an edge.** Median row −0.20R (sniper) and −0.12R (induce→trap); 1 of 74 rows "consistent", and that one failed on fresh markets. The final target is reached **less** often than chance in almost every row (e.g. induce→trap M15: 10–11% vs 17–18%): after the liquidity is taken, price doesn't run to the far liquidity more than a random market would.
- **The NY-session and daily-bias filters don't fix it.** The occasional big averages (sniper H4 + bias +0.52R) come from one year (2024: +3.20R on a few far runners) and are negative in other years.
- **Paired with CRT, it's worse, not better** (−0.03R to −0.40R, 0 of 12 rows consistent): the CRT window and his entry both rely on the same "sweep then reverse" idea, so pairing them doesn't add new information.
- **Walk-forward: all three families fail** (blind −0.37R, +0.02R, −0.36R; 0–1 of 4 years positive).
- **Fine-tuning:** with 86 rows already tried and nothing surviving, tuning settings would mostly fit noise. The parts left untested are his discretionary ones (which liquidity is "respected", news filter, stacking, refinement to a lower timeframe), which are best measured through Ore's own reviews, not more rules.

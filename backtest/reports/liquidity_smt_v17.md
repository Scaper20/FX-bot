# Spec v17 result: liquidity models with and without SMT divergence

Spec: `docs/spec-v17-liquidity-smt.md` (committed before the run). Same v14 trades (GBP/USD + gold, Nov 2021 – Nov 2026, after Ore's spreads), split by whether the partner market (EUR/USD / silver) failed to take its matching level. SMT present on 37% of trades.

| Model · row | SMT trades | SMT avg R | SMT years + | SMT hit vs chance | No-SMT trades | No-SMT avg R | Counts? |
|---|---|---|---|---|---|---|---|
| 4-candle sniper · D1 edge · mgmt A | 31 | **+0.305** | 2 | 17% vs 14% | 124 | -0.235 | no |
| 4-candle sniper · H4 edge · mgmt B | 71 | **+0.165** | 4 | 20% vs 17% | 144 | -0.024 | YES |
| induce → trap · H4 trap · mgmt B | 69 | **+0.155** | 2 | 22% vs 19% | 71 | -0.151 | no |
| 4-candle sniper · H4 mid · mgmt A | 196 | **+0.142** | 2 | 12% vs 9% | 410 | -0.177 | no |
| 4-candle sniper · D1 mid · mgmt A | 21 | **+0.115** | 3 | 19% vs 10% | 89 | -0.074 | no |
| 4-candle sniper · H4 edge · mgmt A | 274 | **+0.049** | 2 | 16% vs 13% | 557 | +0.015 | no |
| induce → trap · M15 trap · mgmt B | 1197 | **-0.045** | 2 | 11% vs 17% | 1798 | -0.127 | no |
| induce → trap · H4 trap · mgmt A | 222 | **-0.052** | 2 | 15% vs 14% | 282 | -0.152 | no |
| 4-candle sniper · H1 mid · mgmt A | 783 | **-0.068** | 2 | 11% vs 11% | 1623 | -0.179 | no |
| induce → trap · H1 trap · mgmt B | 249 | **-0.110** | 1 | 12% vs 19% | 365 | -0.027 | no |
| 4-candle sniper · H1 edge · mgmt B | 461 | **-0.114** | 1 | 14% vs 15% | 889 | -0.096 | no |
| 4-candle sniper · H1 edge · mgmt A | 1117 | **-0.131** | 1 | 12% vs 14% | 2341 | -0.102 | no |
| induce → trap · H1 trap · mgmt A | 704 | **-0.138** | 1 | 11% vs 14% | 956 | -0.103 | no |
| 4-candle sniper · H1 mid · mgmt B | 113 | **-0.152** | 2 | 11% vs 12% | 217 | -0.313 | no |
| induce → trap · M15 trap · mgmt A | 2543 | **-0.154** | 0 | 10% vs 15% | 3661 | -0.182 | no |
| induce → trap · M5 trap · mgmt B | 4059 | **-0.170** | 0 | 9% vs 16% | 5162 | -0.178 | no |
| induce → trap · M5 trap · mgmt A | 6965 | **-0.230** | 0 | 10% vs 15% | 8854 | -0.202 | no |
| 4-candle sniper · M15 edge · mgmt A | 3988 | **-0.240** | 0 | 11% vs 14% | 7765 | -0.159 | no |
| 4-candle sniper · M15 edge · mgmt B | 2205 | **-0.241** | 0 | 10% vs 15% | 4304 | -0.171 | no |
| 4-candle sniper · M5 edge · mgmt B | 6311 | **-0.243** | 0 | 11% vs 15% | 11195 | -0.213 | no |
| 4-candle sniper · M5 edge · mgmt A | 9459 | **-0.262** | 0 | 11% vs 15% | 17209 | -0.237 | no |
| 4-candle sniper · M15 mid · mgmt A | 2865 | **-0.288** | 0 | 11% vs 12% | 5484 | -0.261 | no |
| 4-candle sniper · M5 mid · mgmt B | 3750 | **-0.308** | 0 | 11% vs 14% | 6354 | -0.305 | no |
| 4-candle sniper · M5 mid · mgmt A | 7102 | **-0.325** | 0 | 11% vs 13% | 12668 | -0.298 | no |
| 4-candle sniper · M15 mid · mgmt B | 1018 | **-0.334** | 0 | 10% vs 13% | 1937 | -0.288 | no |
| 4-candle sniper · H4 mid · mgmt B | 7 | **-0.379** | 1 | 0% vs 16% | 14 | -0.846 | no |
| 4-candle sniper · D1 edge · mgmt B | 13 | **-0.403** | 1 | 8% vs 18% | 49 | -0.038 | no |
| 4-candle sniper · D1 mid · mgmt B | 0 | **+nan** | 0 | nan% vs nan% | 4 | -0.428 | no |

**Rows that count: 1 of 28.** All trades: SMT -0.237R (55,793 trades) vs no SMT -0.219R (94,526 trades).

| Model | SMT avg R | No-SMT avg R | SMT walk-forward |
|---|---|---|---|
| 4-candle sniper | -0.260 | -0.231 | blind -0.022R, 109 trades, 2 of 4 years → fail |
| induce → trap | -0.179 | -0.178 | blind -0.320R, 292 trades, 0 of 4 years → fail |

## Swapped-roles check (spec addendum): EUR/USD (partner GBP/USD) + silver (partner gold), unchanged
4-candle sniper · H4 edge · mgmt B **with SMT**: **−0.185R, 82 trades, 1 of 5 years positive, target 13% vs 16% chance** (EUR/USD −0.09R, silver −0.28R); without SMT −0.165R. **FAIL.**

## Reading
- **SMT doesn't improve the liquidity models.** Across all 150,000 trades: with SMT −0.24R, without −0.22R. On the short timeframes (M5/M15), SMT trades were slightly *worse*.
- A few H4/D1 rows look better with SMT (+0.1 to +0.3R), but on 20–200 trades, mostly in 2 of 5 years. The one row that met every rule (sniper H4 + SMT) lost −0.19R with roles swapped, the same row that failed in v14.
- Walk-forward on SMT trades fails for both models (−0.02R and −0.32R blind).
- This matches the earlier SMT test with CRT (v2): divergence between GBP/USD and EUR/USD, or gold and silver, appears on about a third of setups and doesn't separate winners from losers.

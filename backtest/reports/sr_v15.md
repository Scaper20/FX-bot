# Spec v15 result: simple support and resistance, before and after costs

Spec: `docs/spec-v15-support-resistance.md` (committed before the run). GBP/USD + gold, Nov 2021 – Nov 2026. Stop = 0.25 × average daily range beyond the level; target 1R / 2R / 3R. Win = target before stop (trades closed at the 3-day time limit count as not won).

| Level | Trade | Target | Trades | Win rate | Chance | Avg R, no costs | **Avg R, after spread** | Cost per trade | Years + (after spread) | Works? |
|---|---|---|---|---|---|---|---|---|---|---|
| daily swing | bounce | 1R | 560 | 45.9% | 50.0% | -0.082 | **-0.131** | -0.049 | 0 of 5 | no |
| daily swing | bounce | 2R | 560 | 28.5% | 33.3% | -0.144 | **-0.190** | -0.046 | 0 of 5 | no |
| daily swing | bounce | 3R | 560 | 21.2% | 25.0% | -0.122 | **-0.168** | -0.046 | 1 of 5 | no |
| daily swing | breakout | 1R | 549 | 52.1% | 50.0% | +0.042 | **+0.003** | -0.039 | 4 of 5 | YES |
| daily swing | breakout | 2R | 549 | 35.4% | 33.3% | +0.079 | **+0.045** | -0.034 | 3 of 5 | no |
| daily swing | breakout | 3R | 549 | 25.8% | 25.0% | +0.106 | **+0.069** | -0.036 | 3 of 5 | no |
| 4-hour swing | bounce | 1R | 3300 | 47.8% | 50.0% | -0.044 | **-0.087** | -0.043 | 1 of 5 | no |
| 4-hour swing | bounce | 2R | 3300 | 30.6% | 33.3% | -0.078 | **-0.120** | -0.042 | 1 of 5 | no |
| 4-hour swing | bounce | 3R | 3300 | 21.8% | 25.0% | -0.100 | **-0.143** | -0.044 | 0 of 5 | no |
| 4-hour swing | breakout | 1R | 3179 | 50.1% | 50.0% | +0.000 | **-0.034** | -0.034 | 1 of 5 | no |
| 4-hour swing | breakout | 2R | 3179 | 34.7% | 33.3% | +0.056 | **+0.014** | -0.042 | 4 of 5 | YES |
| 4-hour swing | breakout | 3R | 3179 | 25.0% | 25.0% | +0.075 | **+0.036** | -0.040 | 2 of 5 | no |
| yesterday high/low | bounce | 1R | 3037 | 48.5% | 50.0% | -0.030 | **-0.069** | -0.039 | 1 of 5 | no |
| yesterday high/low | bounce | 2R | 3037 | 31.4% | 33.3% | -0.054 | **-0.099** | -0.044 | 0 of 5 | no |
| yesterday high/low | bounce | 3R | 3037 | 23.3% | 25.0% | -0.045 | **-0.092** | -0.047 | 0 of 5 | no |
| yesterday high/low | breakout | 1R | 2742 | 49.1% | 50.0% | -0.018 | **-0.055** | -0.037 | 0 of 5 | no |
| yesterday high/low | breakout | 2R | 2742 | 32.9% | 33.3% | -0.001 | **-0.039** | -0.038 | 2 of 5 | no |
| yesterday high/low | breakout | 3R | 2742 | 23.7% | 25.0% | +0.016 | **-0.018** | -0.034 | 2 of 5 | no |
| round number | bounce | 1R | 4100 | 48.7% | 50.0% | -0.026 | **-0.063** | -0.037 | 1 of 5 | no |
| round number | bounce | 2R | 4100 | 32.5% | 33.3% | -0.021 | **-0.058** | -0.037 | 0 of 5 | no |
| round number | bounce | 3R | 4100 | 24.2% | 25.0% | -0.006 | **-0.042** | -0.036 | 2 of 5 | no |
| round number | breakout | 1R | 3732 | 50.3% | 50.0% | +0.006 | **-0.026** | -0.032 | 1 of 5 | no |
| round number | breakout | 2R | 3732 | 33.8% | 33.3% | +0.024 | **-0.005** | -0.029 | 3 of 5 | no |
| round number | breakout | 3R | 3732 | 24.3% | 25.0% | +0.039 | **+0.013** | -0.026 | 3 of 5 | no |

**Rows that work: 2 of 24.** Across all rows: average R with no costs -0.014, after spread -0.052; win rate minus chance -1.0 points on average.

| Pair | Avg R, no costs | Avg R, after spread |
|---|---|---|
| GBPUSD | -0.022 | -0.070 |
| XAUUSD | -0.002 | -0.030 |

## Fresh-market check (spec addendum): EUR/USD + silver, script unchanged
| Row | GBP/USD + gold (after spread) | EUR/USD + silver (after spread) | Verdict |
|---|---|---|---|
| Daily swing · breakout · 1R | +0.003R, 549 trades, 4 of 5 years | **+0.046R, 559 trades, 4 of 5 years** (no costs +0.134R, win 56.8% vs 50%) | **PASS** |
| 4-hour swing · breakout · 2R | +0.014R, 3,179 trades, 4 of 5 years | −0.101R, 3,184 trades, 1 of 5 years | FAIL |

Daily-swing breakouts by market (after spread, 1R / 2R / 3R): gold +0.11 / +0.22 / +0.28, silver +0.07 / +0.11 / +0.08, EUR/USD +0.02 / +0.12 / +0.06, **GBP/USD −0.09 / −0.11 / −0.13**. Positive on 3 of 4 markets, but the evidence is weak (t 0.1–1.9), and overnight swap isn't included (trades can be held up to 3 days).

## Reading: why everything comes out negative
1. **Before costs, almost every rule averages about zero.** Across all 24 rows: −0.014R with no costs, and win rates 1 point below chance on average. When the win rate equals chance, the average is zero whatever the rule.
2. **Then every trade pays the spread.** Here about 0.03–0.05R a trade (wide stops: a quarter of the daily range). In the CRT tests the stops were much tighter (M5 entries), so the same spread cost about 0.25R a trade: that's why those results were more negative.
3. **Fading a level (bounce) does worse than chance even before costs** (−0.02 to −0.14R): in this data, levels break slightly more often than they hold. CRT, liquidity sweeps, turtle soup and S/R bounces are all "price will reverse at the level" ideas, so they all sat at or below chance.
4. **Breaking out of a level is at or slightly above chance before costs** (+0.04 to +0.19R for daily swings). Daily-swing breakouts are the first simple rule that also held on markets it wasn't built on (EUR/USD + silver), though weakly and not on GBP/USD.

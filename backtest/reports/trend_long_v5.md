# Spec v5 result: weekly and monthly trend following (run 20 Nov 2026)

Spec: `docs/spec-v5-trend.md` (committed before the run). Script: `python -m backtest.trend_long`. Raw output: `backtest/out/trend_long.csv`.
Data: FRED daily FX 1971+ (EUR/USD 1999+), gold/silver futures 2000+. Each market sized to 10% yearly volatility (60-day, cap 3x), costs FX 0.02% / metals 0.05% per position change, trades start the day after each decision.

## Sharpe ratio after costs (yearly return / yearly volatility)

| Signal | Portfolio all | 1971-2012 | **2013-2026** | % years up 2013-26 | 2021-2026 | GBP/USD 2013-26 | GBP/USD 2021-26 | Gold all | Gold 2013-26 | Gold 2021-26 | Works? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M12 | 0.49 | 0.65 | -0.01 | 43% | -0.16 | -0.35 | -0.53 | 0.56 | 0.29 | 0.51 | No |
| M6 | 0.64 | 0.78 | 0.19 | 57% | -0.19 | -0.07 | -0.31 | 0.46 | 0.41 | 0.33 | No |
| M3 | 0.58 | 0.82 | -0.18 | 50% | -0.13 | 0.02 | -0.10 | 0.20 | 0.07 | 0.56 | No |
| M1 | 0.57 | 0.76 | -0.06 | 36% | -0.17 | -0.08 | -0.35 | 0.20 | 0.37 | 0.66 | No |
| SMA10 | 0.61 | 0.85 | -0.16 | 50% | -0.50 | -0.02 | -0.22 | 0.38 | 0.13 | 0.27 | No |
| W52 | 0.62 | 0.78 | 0.09 | 57% | 0.01 | -0.27 | -0.24 | 0.47 | 0.31 | 0.49 | No |
| W26 | 0.63 | 0.75 | 0.23 | 57% | 0.07 | -0.01 | -0.33 | 0.51 | 0.52 | 0.76 | No |
| W13 | 0.66 | 0.91 | -0.18 | 43% | -0.42 | 0.24 | -0.41 | 0.19 | 0.14 | 0.44 | No |
| W4 | 0.70 | 0.94 | -0.14 | 43% | 0.28 | 0.03 | 0.06 | 0.05 | -0.30 | 0.17 | No |
| DON | 0.66 | 0.83 | 0.07 | 50% | -0.02 | -0.08 | -0.29 | 0.35 | 0.23 | 0.68 | No |

Rule: "works" = portfolio Sharpe > 0.3 in 2013-2026 and up in at least 60% of those years. **0 of 10 pass.**

## Per market, best signal after 2013 (W26)

| Market | all | 1971-2012 | 2013-2026 | 2021-2026 |
|---|---|---|---|---|
| AUD/USD | 0.21 | 0.17 | 0.38 | 0.23 |
| EUR/USD | 0.35 | 0.35 | 0.36 | 0.09 |
| GBP/USD | 0.31 | 0.41 | -0.01 | -0.33 |
| NZD/USD | 0.40 | 0.57 | -0.29 | -0.46 |
| USD/CAD | 0.14 | 0.13 | 0.16 | -0.34 |
| USD/CHF | 0.13 | 0.42 | -0.76 | -0.55 |
| USD/JPY | 0.48 | 0.55 | 0.26 | 0.29 |
| USD/NOK | 0.22 | 0.22 | 0.23 | -0.31 |
| USD/SEK | 0.47 | 0.55 | 0.20 | -0.22 |
| Silver | 0.05 | 0.04 | 0.07 | 0.24 |
| Gold | 0.51 | 0.49 | 0.52 | 0.76 |

## Gold: trend following vs simply holding gold (same sizing, not in the spec, added as a fairness check)

| | 2000-2026 | 2000-2012 | 2013-2026 | 2021-2026 |
|---|---|---|---|---|
| Hold gold (long only) | 0.74 | 1.09 | 0.45 | 0.81 |
| Best trend signal (W26) | 0.51 | 0.49 | 0.52 | 0.76 |

## What it means
1. **Trend following on FX worked strongly 1971-2012** (Sharpe 0.65-0.94 for every signal). That's the edge the research found, and it's real in our data.
2. **After the research was published (2013 on) it mostly disappeared for currencies.** Best portfolio Sharpe 0.23, none pass, 2021-2026 negative for 8 of 10 signals.
3. **GBP/USD alone: no edge after 2013** under any signal (-0.35 to +0.24); negative in 2021-2026 for 9 of 10.
4. **Gold looks good, but holding gold did about as well.** Gold rose most of 2019-2026, so any rule that was usually long scores well. Picking the best of 10 signals on one market also flatters it. This is not evidence of a timing edge.

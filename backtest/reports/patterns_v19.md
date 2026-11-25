# Spec v19 result: classic reversal and continuation chart patterns

Spec: `docs/spec-v19-chart-patterns.md` (committed before the run). Main test GBP/USD + gold, fresh check EUR/USD + silver, Nov 2021 – Nov 2026, Ore's spreads, 1-minute scoring, stop first if both hit in a minute.

## By pattern (all timeframes, entries and targets pooled)

| Pattern | Type | Patterns found | Trades | Avg R no costs | **Avg R after spread** | Target hit vs chance | Fresh markets avg R |
|---|---|---|---|---|---|---|---|
| Double top / bottom | reversal | 3,056 | 11,212 | -0.030 | **-0.068** | 43.2% vs 44.6% | -0.122 |
| Head and shoulders | reversal | 3,198 | 10,722 | +0.021 | **-0.051** | 37.0% vs 36.8% | -0.137 |
| Flag | continuation | 5,100 | 19,544 | +0.002 | **-0.077** | 25.5% vs 26.3% | -0.179 |
| Triangle | continuation | 2,300 | 9,466 | -0.003 | **-0.066** | 34.2% vs 34.6% | -0.154 |

## All 64 rows (GBP/USD + gold)

| Pattern | TF | Entry | Target | Trades | No costs | **After spread** | t | Hit vs chance | 2022 | 2023 | 2024 | 2025 | 2026 | Yrs + | Consistent |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Double top / bottom | D1 | E1 | 2R | 21 | +0.010 | **+0.007** | +0.0 | 21% vs 33% | +1.50 | -0.59 | -0.14 | -1.00 | +0.59 | 2 | no |
| Double top / bottom | D1 | E1 | MM | 21 | +0.007 | **+0.004** | +0.0 | 57% vs 57% | +0.64 | +0.06 | -0.09 | -1.00 | +0.20 | 3 | no |
| Double top / bottom | D1 | E2 | 2R | 17 | -0.083 | **-0.087** | -0.3 | 27% vs 33% | — | +0.19 | -0.41 | -1.00 | +0.80 | 2 | no |
| Double top / bottom | D1 | E2 | MM | 17 | -0.064 | **-0.067** | -0.3 | 47% vs 50% | — | +0.19 | -0.15 | -1.00 | +0.33 | 2 | no |
| Double top / bottom | H1 | E1 | 2R | 562 | -0.033 | **-0.060** | -1.1 | 30% vs 33% | -0.17 | +0.09 | -0.10 | -0.00 | -0.12 | 1 | no |
| Double top / bottom | H1 | E1 | MM | 562 | -0.011 | **-0.028** | -0.8 | 58% vs 58% | -0.04 | +0.08 | +0.01 | -0.14 | -0.03 | 2 | no |
| Double top / bottom | H1 | E2 | 2R | 438 | -0.026 | **-0.059** | -0.9 | 31% vs 33% | -0.04 | -0.04 | -0.01 | -0.16 | -0.02 | 0 | no |
| Double top / bottom | H1 | E2 | MM | 438 | +0.051 | **+0.025** | +0.5 | 54% vs 51% | +0.01 | +0.08 | +0.11 | -0.12 | +0.08 | 4 | YES |
| Double top / bottom | H4 | E1 | 2R | 161 | -0.039 | **-0.046** | -0.4 | 29% vs 33% | +0.14 | -0.50 | +0.39 | -0.27 | -0.13 | 2 | no |
| Double top / bottom | H4 | E1 | MM | 161 | -0.043 | **-0.048** | -0.7 | 56% vs 58% | +0.01 | -0.25 | +0.08 | -0.02 | -0.12 | 2 | no |
| Double top / bottom | H4 | E2 | 2R | 118 | -0.072 | **-0.104** | -0.8 | 31% vs 33% | +0.21 | -0.29 | +0.02 | -0.12 | -0.50 | 2 | no |
| Double top / bottom | H4 | E2 | MM | 118 | -0.046 | **-0.054** | -0.6 | 49% vs 51% | +0.08 | -0.26 | +0.12 | -0.01 | -0.26 | 2 | no |
| Double top / bottom | M15 | E1 | 2R | 2361 | -0.025 | **-0.063** | -2.3 | 32% vs 33% | -0.04 | -0.06 | +0.03 | -0.12 | -0.12 | 1 | no |
| Double top / bottom | M15 | E1 | MM | 2361 | -0.042 | **-0.078** | -4.6 | 56% vs 59% | -0.06 | -0.11 | +0.01 | -0.11 | -0.10 | 1 | no |
| Double top / bottom | M15 | E2 | 2R | 1928 | -0.038 | **-0.088** | -2.9 | 32% vs 33% | -0.01 | -0.07 | +0.01 | -0.13 | -0.20 | 1 | no |
| Double top / bottom | M15 | E2 | MM | 1928 | -0.034 | **-0.082** | -4.0 | 51% vs 53% | -0.02 | -0.08 | -0.05 | -0.12 | -0.11 | 0 | no |
| Flag | D1 | E1 | 2R | 40 | +0.059 | **+0.053** | +0.2 | 35% vs 33% | -0.13 | +1.37 | -0.10 | -0.60 | +0.20 | 2 | no |
| Flag | D1 | E1 | MM | 40 | +0.013 | **+0.009** | +0.0 | 21% vs 24% | +0.20 | +1.11 | -0.30 | -0.93 | +0.67 | 3 | no |
| Flag | D1 | E2 | 2R | 35 | +0.114 | **+0.106** | +0.4 | 37% vs 33% | -0.01 | +1.49 | -0.34 | -0.26 | +0.20 | 2 | no |
| Flag | D1 | E2 | MM | 35 | +0.733 | **+0.718** | +1.2 | 22% vs 19% | +1.84 | +1.41 | +0.54 | -0.72 | +1.51 | 4 | YES |
| Flag | H1 | E1 | 2R | 1112 | +0.016 | **-0.032** | -0.8 | 34% vs 33% | -0.10 | -0.03 | -0.04 | -0.02 | -0.00 | 0 | no |
| Flag | H1 | E1 | MM | 1112 | +0.069 | **+0.020** | +0.3 | 19% vs 20% | -0.09 | +0.05 | +0.01 | +0.01 | +0.17 | 4 | no |
| Flag | H1 | E2 | 2R | 954 | +0.051 | **-0.021** | -0.5 | 35% vs 33% | -0.14 | -0.04 | -0.06 | +0.12 | +0.01 | 2 | no |
| Flag | H1 | E2 | MM | 954 | +0.109 | **+0.021** | +0.3 | 15% vs 15% | -0.17 | +0.13 | -0.02 | +0.08 | +0.16 | 3 | no |
| Flag | H4 | E1 | 2R | 275 | +0.105 | **+0.096** | +1.1 | 36% vs 33% | +0.03 | +0.00 | +0.07 | +0.24 | +0.29 | 5 | YES |
| Flag | H4 | E1 | MM | 275 | +0.148 | **+0.139** | +1.1 | 23% vs 24% | +0.17 | +0.13 | +0.10 | +0.09 | +0.24 | 5 | no |
| Flag | H4 | E2 | 2R | 210 | -0.027 | **-0.049** | -0.5 | 32% vs 33% | -0.12 | -0.02 | +0.10 | -0.08 | -0.00 | 1 | no |
| Flag | H4 | E2 | MM | 210 | +0.120 | **+0.113** | +0.7 | 17% vs 18% | +0.26 | +0.19 | +0.06 | +0.06 | -0.02 | 4 | no |
| Flag | M15 | E1 | 2R | 3850 | -0.057 | **-0.127** | -6.1 | 31% vs 33% | -0.04 | -0.19 | -0.18 | -0.05 | -0.18 | 0 | no |
| Flag | M15 | E1 | MM | 3850 | +0.000 | **-0.087** | -2.8 | 21% vs 21% | -0.06 | -0.16 | -0.13 | -0.05 | -0.04 | 0 | no |
| Flag | M15 | E2 | 2R | 3296 | -0.030 | **-0.129** | -5.7 | 32% vs 33% | -0.01 | -0.18 | -0.22 | -0.05 | -0.19 | 0 | no |
| Flag | M15 | E2 | MM | 3296 | -0.002 | **-0.107** | -2.8 | 17% vs 17% | -0.04 | -0.18 | -0.16 | -0.03 | -0.10 | 0 | no |
| Head and shoulders | D1 | E1 | 2R | 35 | +0.337 | **+0.324** | +1.5 | 42% vs 33% | +0.55 | +0.36 | -0.09 | +0.93 | +0.19 | 4 | YES |
| Head and shoulders | D1 | E1 | MM | 35 | +0.111 | **+0.108** | +0.6 | 48% vs 43% | -0.12 | -0.03 | -0.32 | +1.00 | +0.34 | 2 | no |
| Head and shoulders | D1 | E2 | 2R | 19 | -0.153 | **-0.155** | -0.6 | 20% vs 33% | -0.61 | +0.42 | -0.14 | -0.10 | -0.52 | 1 | no |
| Head and shoulders | D1 | E2 | MM | 19 | -0.256 | **-0.257** | -1.1 | 29% vs 36% | -0.61 | +0.16 | -0.30 | -0.10 | -0.47 | 1 | no |
| Head and shoulders | H1 | E1 | 2R | 604 | +0.067 | **+0.017** | +0.3 | 34% vs 33% | +0.03 | -0.06 | +0.06 | +0.10 | -0.01 | 3 | no |
| Head and shoulders | H1 | E1 | MM | 604 | +0.024 | **-0.028** | -0.5 | 43% vs 41% | -0.07 | -0.08 | +0.01 | +0.00 | +0.02 | 3 | no |
| Head and shoulders | H1 | E2 | 2R | 376 | +0.028 | **-0.036** | -0.5 | 33% vs 33% | -0.02 | +0.04 | +0.04 | +0.02 | -0.22 | 3 | no |
| Head and shoulders | H1 | E2 | MM | 376 | +0.097 | **+0.005** | +0.1 | 35% vs 34% | +0.14 | -0.08 | +0.08 | -0.08 | -0.02 | 2 | no |
| Head and shoulders | H4 | E1 | 2R | 181 | -0.066 | **-0.072** | -0.7 | 29% vs 33% | +0.11 | -0.22 | -0.37 | +0.15 | +0.07 | 3 | no |
| Head and shoulders | H4 | E1 | MM | 181 | -0.029 | **-0.046** | -0.5 | 44% vs 46% | +0.05 | -0.18 | -0.38 | +0.23 | +0.10 | 3 | no |
| Head and shoulders | H4 | E2 | 2R | 125 | -0.006 | **-0.027** | -0.2 | 32% vs 33% | +0.15 | +0.01 | -0.34 | -0.03 | +0.16 | 3 | no |
| Head and shoulders | H4 | E2 | MM | 125 | +0.028 | **+0.003** | +0.0 | 36% vs 37% | +0.10 | +0.34 | -0.32 | +0.27 | -0.30 | 3 | no |
| Head and shoulders | M15 | E1 | 2R | 2383 | +0.009 | **-0.057** | -2.1 | 33% vs 33% | +0.01 | -0.12 | -0.11 | +0.07 | -0.08 | 2 | no |
| Head and shoulders | M15 | E1 | MM | 2383 | +0.020 | **-0.045** | -1.7 | 44% vs 43% | -0.03 | -0.10 | -0.07 | +0.02 | +0.02 | 2 | no |
| Head and shoulders | M15 | E2 | 2R | 1638 | +0.017 | **-0.084** | -2.6 | 34% vs 33% | -0.03 | -0.16 | -0.09 | +0.02 | -0.09 | 1 | no |
| Head and shoulders | M15 | E2 | MM | 1638 | +0.020 | **-0.079** | -2.3 | 37% vs 37% | +0.01 | -0.16 | -0.13 | +0.02 | -0.08 | 2 | no |
| Triangle | D1 | E1 | 2R | 34 | +0.197 | **+0.195** | +0.9 | 33% vs 33% | +1.21 | -0.25 | -1.00 | +0.73 | -0.36 | 2 | no |
| Triangle | D1 | E1 | MM | 34 | +0.373 | **+0.371** | +1.4 | 48% vs 34% | +1.01 | -0.01 | -1.00 | +1.28 | -0.24 | 2 | no |
| Triangle | D1 | E2 | 2R | 24 | -0.058 | **-0.059** | -0.2 | 29% vs 33% | +1.25 | -0.25 | -1.00 | +0.56 | -0.60 | 2 | no |
| Triangle | D1 | E2 | MM | 24 | +0.190 | **+0.188** | +0.5 | 32% vs 27% | +1.64 | -0.47 | -1.00 | +1.31 | -0.39 | 2 | no |
| Triangle | H1 | E1 | 2R | 476 | +0.008 | **-0.018** | -0.3 | 32% vs 33% | -0.00 | +0.13 | -0.08 | -0.06 | +0.07 | 2 | no |
| Triangle | H1 | E1 | MM | 476 | -0.030 | **-0.055** | -0.9 | 34% vs 36% | -0.10 | +0.12 | -0.10 | -0.19 | +0.10 | 2 | no |
| Triangle | H1 | E2 | 2R | 404 | -0.015 | **-0.054** | -0.8 | 32% vs 33% | +0.09 | +0.11 | -0.18 | -0.07 | -0.11 | 2 | no |
| Triangle | H1 | E2 | MM | 404 | -0.054 | **-0.086** | -1.2 | 29% vs 31% | +0.02 | -0.01 | -0.16 | -0.19 | -0.01 | 1 | no |
| Triangle | H4 | E1 | 2R | 120 | +0.052 | **+0.045** | +0.4 | 34% vs 33% | -0.04 | -0.22 | -0.34 | +0.91 | -0.34 | 1 | no |
| Triangle | H4 | E1 | MM | 120 | +0.039 | **+0.033** | +0.2 | 38% vs 39% | -0.14 | -0.32 | -0.48 | +1.16 | -0.41 | 1 | no |
| Triangle | H4 | E2 | 2R | 99 | -0.003 | **-0.009** | -0.1 | 32% vs 33% | -0.04 | +0.00 | -0.13 | +0.74 | -0.45 | 2 | no |
| Triangle | H4 | E2 | MM | 99 | -0.129 | **-0.133** | -1.0 | 28% vs 34% | -0.09 | -0.48 | -0.55 | +0.90 | -0.35 | 1 | no |
| Triangle | M15 | E1 | 2R | 1941 | -0.005 | **-0.071** | -2.4 | 33% vs 33% | -0.07 | -0.14 | -0.08 | +0.10 | -0.16 | 1 | no |
| Triangle | M15 | E1 | MM | 1941 | +0.009 | **-0.061** | -2.1 | 40% vs 39% | -0.17 | -0.10 | -0.00 | +0.05 | -0.07 | 1 | no |
| Triangle | M15 | E2 | 2R | 1635 | -0.004 | **-0.083** | -2.6 | 33% vs 33% | -0.13 | -0.18 | -0.04 | +0.06 | -0.11 | 1 | no |
| Triangle | M15 | E2 | MM | 1635 | -0.006 | **-0.096** | -2.8 | 34% vs 34% | -0.21 | -0.10 | -0.05 | +0.03 | -0.09 | 1 | no |

**Consistent rows: 4 of 64.** Walk-forward (choose on past years, trade next year blind, 2023–26): +0.009R over 128 trades, positive in 2 of 4 years → **fail**.

## Consistent rows on fresh markets (EUR/USD + silver, same rule)

| Row | Main | Fresh trades | Fresh avg R | Fresh yrs + | Fresh hit vs chance | By market | Verdict |
|---|---|---|---|---|---|---|---|
| Double top / bottom H1 E2 MM | 438 · +0.025 | 441 | **+0.025** | 3 | 58% vs 53% | EURUSD +0.106 (225), XAGUSD -0.060 (216) | PASS |
| Flag D1 E2 MM | 35 · +0.718 | 35 | **+0.448** | 4 | 17% vs 17% | EURUSD +0.921 (20), XAGUSD -0.182 (15) | FAIL |
| Flag H4 E1 2R | 275 · +0.096 | 263 | **+0.047** | 3 | 34% vs 33% | EURUSD -0.014 (125), XAGUSD +0.102 (138) | PASS |
| Head and shoulders D1 E1 2R | 35 · +0.324 | 33 | **+0.292** | 4 | 39% vs 33% | EURUSD -0.048 (13), XAGUSD +0.513 (20) | PASS |

## By market (all rows pooled)

| Market | Trades | No costs | After spread |
|---|---|---|---|
| EURUSD | 26,086 | -0.038 | -0.138 |
| GBPUSD | 25,922 | -0.045 | -0.121 |
| XAGUSD | 25,334 | -0.046 | -0.169 |
| XAUUSD | 25,022 | +0.043 | -0.012 |

## Checks

- Independent audit (`backtest/chart_patterns.py`): 28,464 patterns, 102,364 trades. Every key swing is a real swing on its own candles, every decision is at least 3 candles after the last swing (no look-ahead), every stop is exactly 2 spreads beyond its spec anchor, and entry/stop/target are on the right sides. **0 problems.**
- Example charts (GBP/USD H1 and H4, one per pattern, GMT+0): `docs/pattern_examples/`.
- Unit tests with hand-made double top, head and shoulders and flag: `tests/test_patterns.py`.

## The three rows that passed the fresh-market check, pooled over all 4 markets (checked after the main result)

| Row | Trades | Avg R after spread | t | Years + (of 5) | Without the 5 best trades |
|---|---|---|---|---|---|
| Flag H4, market entry, 2R | 538 | +0.072 | 1.2 | 3 | +0.054 |
| Double top/bottom H1, retest, measured move | 879 | +0.025 | 0.8 | 3 | +0.019 |
| Head and shoulders D1, market entry, 2R | 68 | +0.309 | 2.1 | 5 | +0.175 |

## Reading

- **Before costs, every pattern is at about zero** (−0.03R to +0.02R a trade) and hits its target at the chance rate (e.g. double tops 43% vs 45% chance, flags 26% vs 26%). The spread then makes all four patterns negative (−0.05R to −0.08R; M15 worst, as always with tight stops).
- **4 of 64 rows were consistent**: about what luck gives (~3). Three of them held on EUR/USD + silver, but the walk-forward over the 64 rows fails (+0.01R, 2 of 4 years), so **by the pre-registered rule no row counts**.
- **Leads worth watching, not edges:**
  - **Flag on H4, enter at the breakout close.** The only pattern positive in all 5 years on GBP/USD + gold with both targets (2R +0.10R, measured move +0.14R), and still positive on EUR/USD + silver (+0.05R). Pooled t 1.2: not distinguishable from luck yet.
  - **Head and shoulders on D1, market entry, 2R.** +0.31R, t 2.1, positive all 5 years, but only 68 trades in 5 years across 4 markets (about 3 a year per market), chosen from 64 rows.
  - Double top H1 retest: +0.025R, effectively zero.
- **Verdict: no edge.** Classic chart patterns behave like everything tested before on these markets: at chance before costs, negative after. Continuation patterns on higher timeframes lose least, which fits the earlier finding that breakouts do slightly better than reversals.

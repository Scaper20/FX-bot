# Spec v4 result: Romeo's discretionary models, full MSnR, mixing — all years

Rules: `docs/spec-v4-advanced.md` (committed before the run, commit de3f9a4). Script: `backtest/advanced.py`.
Nov 2021 – Nov 2026, GBP/USD and gold, New York clock, D1 (M15 entries) and H4 (M5 entries), spread included, half off at 50% then stop to entry where a 50% target applies. Average R per trade by year.

| Model | Trades | 2022 | 2023 | 2024 | 2025 | 2026 | Avg R | Total R | Target 2 hit vs chance (z) |
|---|---|---|---|---|---|---|---|---|---|
| MSnR full | 914 | -0.11 | -0.03 | -0.13 | +0.00 | -0.07 | -0.068 | -62 | 58.4% vs 58.3% (+0.1) |
| rejection block | 2940 | -0.09 | -0.03 | -0.14 | -0.06 | -0.06 | -0.075 | -212 | 56.9% vs 56.9% (+0.1) |
| control C2 close | 5351 | -0.09 | -0.10 | -0.10 | -0.05 | -0.05 | -0.083 | -438 | 42.0% vs 42.8% (-1.3) |
| OTE | 3800 | -0.11 | -0.09 | -0.09 | -0.07 | -0.08 | -0.091 | -343 | 33.4% vs 35.2% (-2.3) |
| RTM1 | 1317 | -0.03 | -0.10 | -0.05 | -0.15 | -0.15 | -0.099 | -130 | 18.2% vs 19.0% (-0.8) |
| MIX 2+ agree | 3193 | -0.10 | -0.14 | -0.18 | -0.10 | -0.14 | -0.129 | -410 | 32.7% vs 33.7% (-1.3) |
| KOD | 3568 | -0.15 | -0.15 | -0.20 | -0.12 | -0.12 | -0.149 | -532 | 37.4% vs 39.2% (-2.3) |
| PORTFOLIO (all models) | 15360 | -0.18 | -0.17 | -0.18 | -0.15 | -0.12 | -0.164 | -2488 | 35.4% vs 36.4% (-3.1) |
| M1 | 817 | -0.10 | -0.14 | -0.19 | -0.30 | -0.16 | -0.179 | -146 | 17.8% vs 20.9% (-2.2) |
| fake MSS fade | 2004 | -0.68 | -0.66 | -0.51 | -0.48 | -0.28 | -0.531 | -1064 | 12.4% vs 12.4% (-0.1) |

**Consistent** (positive average R in at least 4 of 2022–2026, and positive overall): **none**.

Closest (by timeframe):
- OTE D1: avg -0.008 R, positive in 2 of 5 years
- control C2 close D1: avg -0.030 R, positive in 3 of 5 years
- MSnR full D1: avg -0.042 R, positive in 2 of 5 years
- rejection block D1: avg -0.063 R, positive in 1 of 5 years

## Reading
- Every model loses after spread in total. None is positive in more than 2 of the 5 years.
- **Target 2 is hit at the chance rate or slightly below** for every model (z between −2.3 and +0.2). After a sweep and a confirmation, price is no more likely to reach the far side than a coin flip with the same distances.
- **Fake MSS fade:** stopped just below the last 5 candles, so the risk is tiny and the spread turns stops that would not trigger without costs into losses (−0.53 R).
- **Mixing does not help:** "2+ models agree" is −0.13 R. Combining signals that each have no edge gives a signal with no edge. The portfolio of all models is −0.16 R per trade.
- **All years are now used** (Ore's decision). There is no unseen data left; any future rule change must be judged on live forward results.

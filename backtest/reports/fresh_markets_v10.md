# Spec v10 result: the v9 candidate on EUR/USD and silver (run 20 Nov 2026)

Spec: `docs/spec-v10-fresh-markets.md` (committed before the run). Rule frozen from v9: Romeo loose 3 filters + MSnR, H4 → M5 breaker, classic stop. Script: `python -m backtest.fresh_markets`. Spreads: EUR/USD 1 pip, silver 3 cents.

| Row (classic stop) | Market | Trades | Avg R | Target 2 hit vs chance | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|
| **edge (main row)** | both | 91 | **−0.22** | 48% vs 44% (z +0.9) | −0.06 | −0.45 | +0.28 | −0.21 | −0.44 |
| edge | EUR/USD | 37 | −0.24 | 38% vs 40% | −0.20 | −0.49 | +0.69 | −0.30 | −0.40 |
| edge | silver | 54 | −0.21 | 54% vs 46% (z +1.3) | +0.03 | −0.41 | +0.04 | −0.12 | −0.46 |
| confirm | both | 73 | −0.19 | 51% vs 48% | −0.20 | −0.49 | +0.33 | −0.09 | −0.34 |
| mid | both | 75 | −0.25 | 38% vs 36% | −0.23 | −0.53 | +0.66 | −0.25 | −0.49 |

Tight-stop rows: −0.26 to −0.70R (full table in `backtest/out/fresh_markets_summary.csv`).

**Pass rule:** edge classic > 0: **no** (−0.22R). 2 of 3 classic rows > 0: **no** (0 of 3). Target 2 at least chance: yes (48% vs 44%). **FAIL.**

## Reading
On markets it had never seen, the rule loses about 0.2R a trade, in 4 of 5 years, with roughly the same number of trades as on GBP/USD and gold. Silver hit Target 2 a bit more often than chance (z +1.3), but not enough to cover the stop losses and the spread. EUR/USD was at chance. As the spec says, v9's good result is therefore treated as luck from looking at many versions: the pattern didn't carry over.

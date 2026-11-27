# Spec v25 result: Ore's reversal model after a fresh higher-timeframe POI tap

Spec: `docs/spec-v25-htf-poi.md` (committed before the run). Pattern, orders, stop and hold as spec v24. Main test GBP/USD + gold, check EUR/USD + silver, Nov 2021 – Nov 2026, Ore's spreads, 1-minute scoring.

Grid: 864 rows with an HTF POI (+ 72 no-POI baselines). Rows with ≥ 30 trades on GBP/USD + gold: 104. Of those, 0 have t ≥ 2 (about 3 expected by luck alone if rows were independent; they overlap heavily, so more).

## Top 10 rows on GBP/USD + gold (ranked by t), each checked unchanged on EUR/USD + silver

| # | HTF POI | LTF | Structure | Entry | Target | Bias | Trades | No costs | **After spread** | t | Hit vs chance | Yrs + | EUR/USD + silver (trades · avg · yrs+ · hit) | Holds? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | H4 any | H1 | wick | nearest | 3R | none | 34 | +0.647 | **+0.605** | +1.8 | 41% vs 25% | 4 | 51 · -0.228 · 2 · 20% | no |
| 2 | H4 any | H1 | wick | nearest | 5R | none | 34 | +0.757 | **+0.709** | +1.6 | 28% vs 17% | 3 | 51 · -0.157 · 1 · 12% | no |
| 3 | H4 FVG | M15 | wick | nearest | 5R | D1 trend | 38 | +0.737 | **+0.616** | +1.5 | 29% vs 17% | 4 | 29 · +0.141 · 3 · 21% | no |
| 4 | H4 FVG | M15 | wick | nearest | 3R | D1 trend | 38 | +0.474 | **+0.374** | +1.3 | 37% vs 25% | 4 | 29 · +0.395 · 4 · 38% | no |
| 5 | either FVG | M15 | wick | nearest | 3R | D1 trend | 48 | +0.417 | **+0.320** | +1.2 | 35% vs 25% | 5 | 35 · +0.358 · 4 · 37% | **YES** |
| 6 | either FVG | M15 | wick | BB | 5R | none | 33 | +0.636 | **+0.525** | +1.2 | 27% vs 17% | 3 | 21 · +0.570 · 4 · 29% | no |
| 7 | either any | M15 | wick | nearest | 3R | D1 trend | 59 | +0.356 | **+0.277** | +1.2 | 34% vs 25% | 4 | 47 · +0.411 · 4 · 40% | **YES** |
| 8 | either FVG | M15 | wick | nearest | 5R | D1 trend | 48 | +0.515 | **+0.411** | +1.2 | 26% vs 17% | 4 | 35 · +0.098 · 2 · 20% | no |
| 9 | H4 any | M15 | wick | nearest | 3R | D1 trend | 46 | +0.391 | **+0.309** | +1.2 | 35% vs 25% | 4 | 39 · +0.321 · 4 · 38% | **YES** |
| 10 | H4 FVG | M15 | wick | nearest | 5R | none | 68 | +0.412 | **+0.318** | +1.1 | 24% vs 17% | 4 | 59 · +0.151 · 3 · 20% | **YES** |

**Walk-forward over the whole grid** (each year pick the best row on past years, trade it blind): +0.121R over 61 trades, positive in 2 of 4 years → **fail**. Picks: 2023: None; 2024: H4|any|M5|wick|nearest|3R|none; 2025: H4|any|M5|wick|nearest|3R|none; 2026: H4|FVG|M15|wick|nearest|5R|D1 trend.

## Does the HTF POI tap help? (D1 trend, entry = nearest, all LTF / structure / targets pooled)

| Filter | Trades | No costs | After spread | Hit vs chance | EUR/USD + silver avg (trades) |
|---|---|---|---|---|---|
| no POI requirement | 3296 | +0.120 | -0.006 | 23% vs 21% | -0.159 (3306) |
| H4 OB | 52 | +0.133 | +0.113 | 24% vs 21% | -0.252 (72) |
| H4 BB | 42 | +0.952 | +0.882 | 40% vs 21% | +0.036 (32) |
| H4 FVG | 276 | +0.371 | +0.272 | 28% vs 21% | +0.175 (312) |
| H4 any | 348 | +0.349 | +0.267 | 28% vs 21% | +0.091 (394) |
| D1 OB | 12 | +0.068 | +0.039 | 18% vs 21% | -0.297 (32) |
| D1 BB | 22 | +1.700 | +1.587 | 60% vs 21% | -0.156 (16) |
| D1 FVG | 104 | -0.044 | -0.117 | 21% vs 21% | -0.310 (120) |
| D1 any | 134 | +0.211 | +0.135 | 25% vs 21% | -0.267 (162) |
| either OB | 64 | +0.121 | +0.099 | 23% vs 21% | -0.266 (104) |
| either BB | 56 | +0.811 | +0.753 | 39% vs 21% | +0.061 (44) |
| either FVG | 346 | +0.242 | +0.156 | 26% vs 21% | +0.122 (382) |
| either any | 434 | +0.232 | +0.159 | 26% vs 21% | +0.064 (496) |

## Clean check (one target, one structure version, all four markets; run after the main result)
D1 trend, nearest entry, 3R, the 4 markets pooled. The H4 POI tap improves the pattern in every slice:

| Slice | No HTF POI | After the first tap of a fresh H4 POI |
|---|---|---|
| wick breaks, M15 | +0.06R (518) | +0.31R (85) |
| wick breaks, M5 | −0.10R (1,720) | +0.14R (113) |
| wick breaks, H1 | +0.13R (171) | +0.15R (53) |
| close breaks, M15 | −0.20R (173) | +0.04R (38) |
| close breaks, M5 | −0.11R (643) | −0.02R (59) |
| close breaks, H1 | −0.09R (76) | +0.52R (23) |

**Pattern completes soon after the tap** (post-hoc split, prompted by a chart where the MSS came 4 days after the tap):

| Group | GBP/USD + gold | EUR/USD + silver |
|---|---|---|
| Pattern completes within 30 LTF candles of the tap | +0.21R (128) | +0.25R (142) |
| Later | +0.33R (46) | −0.27R (55) |

The within-30 group pooled over all four markets: t +2.16.

## Reading
- **The HTF POI tap is the first condition in all these tests that improves a pattern on both test sets.**
  - Pooled across timeframes (D1 trend): no POI −0.01R; H4 POI +0.27R on GBP/USD + gold and +0.09R on EUR/USD + silver.
  - H4 FVG: +0.27R and +0.18R. H4 breaker: +0.88R (42 trades) and +0.04R.
  - D1 POIs do worse than H4 (D1 FVG −0.12R).
- **4 of the top 10 rows hold on EUR/USD + silver.** The best that held is "either FVG, M15, wick breaks, nearest entry, 3R, D1 trend": +0.32R (48) and +0.36R (35), positive in 5 and 4 of 5 years.
- **But nothing is proven:**
  - No single row reaches t ≥ 2 on GBP/USD + gold (each has only 30–70 trades).
  - The grid walk-forward fails (+0.12R over 61 trades, 2 of 4 years).
  - The "within 30 candles" split was chosen after seeing the data.
- **Verdict: the strongest lead so far, and consistent with Ore's description.** It needs the live forward record to confirm it. There is no unseen history left to test it on.


## Correction and live version (spec v26, 27 Nov 2026)
**Flaw found in the "nearest" entry rows above.** Orders that never filled were dropped before the breaker-else-order-block
choice, so when the breaker order did not fill, the row fell back to the order block. Live can't know that when the order is
placed. The OB-only and BB-only rows are not affected.

`backtest/ore_v26.py` re-scores the live rules with the exact live function (`engine.smc_models.ore_poi_setups`): D1
trend, H4 OB or FVG first tap (breakers ignored, Ore's rule), M15 wick breaks, breaker else OB **chosen at the
decision**, pattern within 30 candles of the top, 3R.

| Set | Setups | Filled trades | Avg R | Target hit vs chance | Years positive |
|---|---|---|---|---|---|
| GBP/USD + gold | 89 | 34 | +0.32 | 35% vs 25% | 4/6 |
| EUR/USD + silver | 80 | 30 | +0.50 | 40% vs 25% | 4/6 |
| GBP/USD | 42 | 15 | +0.02 | 27% | 3/6 |
| Gold | 47 | 19 | +0.56 | 42% | 4/5 |
| EUR/USD | 49 | 21 | +0.11 | 29% | 4/6 |
| Silver | 31 | 9 | +1.40 | 67% | 3/4 |

The fix changed almost nothing (33 → 34 trades; the BB entry is 35% of trades). The live rules were chosen after
seeing v25, so these numbers are in-sample for that choice. Too few trades to call it an edge; the live record is
the real test.

# Spec v21 result: order-block strategy rebuilt on real market structure

Spec: `docs/spec-v21-orderblock-rebuild.md` (committed before the run). MSS on the entry timeframe in the direction of the D1 + H4 external trend; stop beyond the top/bottom of the move + 2 spreads; 3R. Main test GBP/USD + gold, fresh check EUR/USD + silver, Nov 2021 – Nov 2026, Ore's spreads, 1-minute scoring.

For comparison, the **old** live strategy (v16, tiny-swing MSS): H1 OB open with D1+H4 bias +0.27R over 234 trades on GBP/USD + gold, −0.12R on EUR/USD + silver.

## Test A: draft order block (last opposite candles at the top/bottom)

| TF | Entry | Bias | Trades | No costs | **After spread** | t | Hit vs 25% chance | 2022 | 2023 | 2024 | 2025 | 2026 | Yrs + | Consistent | Fresh (trades · avg · yrs+ · hit) | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H1 | market at MSS close | D1+H4 | 220 | -0.039 | **-0.047** | -0.7 | 10% | +0.06 | +0.11 | -0.07 | -0.35 | +0.10 | 3 | no | 205 · -0.106 · 1 · 7% |  |
| H1 | market at MSS close | none | 894 | -0.009 | **-0.018** | -0.5 | 11% | -0.01 | +0.04 | -0.11 | -0.08 | +0.09 | 2 | no | 953 · -0.033 · 2 · 10% |  |
| H1 | OB body edge | D1+H4 | 89 | +0.078 | **+0.059** | +0.4 | 15% | +0.06 | +0.28 | +0.46 | -0.42 | +0.14 | 4 | no | 83 · -0.154 · 2 · 12% |  |
| H1 | OB body edge | none | 358 | +0.124 | **+0.103** | +1.4 | 20% | -0.06 | +0.14 | +0.34 | +0.02 | +0.33 | 4 | no | 371 · -0.066 · 2 · 17% |  |
| M15 | market at MSS close | D1+H4 | 877 | -0.068 | **-0.088** | -2.0 | 15% | -0.17 | -0.10 | +0.08 | -0.19 | -0.01 | 1 | no | 788 · -0.032 · 1 · 18% |  |
| M15 | market at MSS close | none | 3083 | -0.010 | **-0.032** | -1.3 | 18% | -0.07 | -0.02 | -0.07 | -0.00 | +0.01 | 1 | no | 3021 · -0.077 · 0 · 16% |  |
| M15 | OB body edge | D1+H4 | 390 | -0.222 | **-0.252** | -3.5 | 17% | -0.47 | -0.31 | -0.14 | -0.16 | -0.07 | 0 | no | 359 · -0.112 · 2 · 22% |  |
| M15 | OB body edge | none | 1271 | -0.068 | **-0.107** | -2.5 | 21% | -0.17 | -0.00 | -0.27 | -0.05 | -0.11 | 0 | no | 1262 · -0.189 · 1 · 19% |  |

Walk-forward (choose on past years, trade next year blind, 2023–26): -0.125R over 200 trades, positive in 2 of 4 years → **fail**.

## Test B: Ore's order block (2-candle engulfing or candle + pin bar + engulfing)

| TF | Entry | Bias | Trades | No costs | **After spread** | t | Hit vs 25% chance | 2022 | 2023 | 2024 | 2025 | 2026 | Yrs + | Consistent | Fresh (trades · avg · yrs+ · hit) | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H1 | first candle's body | D1+H4 | 24 | -0.333 | **-0.369** | -1.3 | 17% | -0.36 | +0.09 | -0.08 | -1.00 | -1.00 | 1 | no | 25 · -0.276 · 1 · 18% |  |
| H1 | first candle's body | none | 97 | +0.003 | **-0.024** | -0.1 | 24% | +0.29 | -0.19 | +0.16 | -0.32 | +0.26 | 3 | no | 116 · -0.240 · 2 · 18% |  |
| H1 | first candle's near edge | D1+H4 | 28 | -0.571 | **-0.591** | -2.6 | 11% | -1.00 | -0.52 | +0.26 | -1.00 | -1.00 | 1 | no | 29 · -0.366 · 1 · 12% |  |
| H1 | first candle's near edge | none | 115 | +0.175 | **+0.146** | +0.9 | 29% | +0.25 | +0.02 | +0.18 | -0.16 | +0.89 | 4 | YES | 141 · -0.236 · 1 · 18% | fresh FAIL |
| M15 | first candle's body | D1+H4 | 102 | -0.088 | **-0.179** | -1.2 | 23% | -0.24 | -0.28 | +0.17 | +0.04 | -0.67 | 2 | no | 81 · -0.172 · 3 · 22% |  |
| M15 | first candle's body | none | 320 | +0.006 | **-0.051** | -0.6 | 25% | +0.19 | -0.04 | -0.25 | +0.08 | -0.20 | 2 | no | 322 · -0.246 · 1 · 23% |  |
| M15 | first candle's near edge | D1+H4 | 123 | -0.080 | **-0.152** | -1.1 | 23% | -0.09 | -0.52 | +0.13 | +0.12 | -0.28 | 2 | no | 105 · -0.146 · 2 · 23% |  |
| M15 | first candle's near edge | none | 382 | -0.051 | **-0.104** | -1.3 | 23% | +0.06 | -0.17 | -0.10 | +0.01 | -0.24 | 2 | no | 398 · -0.177 · 2 · 23% |  |

Walk-forward (choose on past years, trade next year blind, 2023–26): +0.002R over 82 trades, positive in 3 of 4 years → **PASS**.

Order blocks found in test B: 2-candle 771, 3-candle 265 (counted on the edge-entry rows, all markets, bias on and off).


## Checks
- Independent audit (`backtest/chart_ob_v21.py`): 13,104 trades. MSS candle is the first close beyond the broken level; nothing went beyond the top/bottom of the move before it; test B formations meet the 2-candle / 3-candle rule, contain the top/bottom and are complete by the MSS candle; levels on the right sides. **0 problems** (the first run had 3 formations finishing after the MSS candle, a look-ahead; fixed and re-run).
- Example charts (random, not chosen): `docs/smc_review/v21_*.png`. Unit tests: `tests/test_smc_structure.py`.

## Reading
- **The old live strategy's +0.27R does not survive a correct build.** On real market structure the same idea (D1+H4 trend, H1 MSS, order block at the top/bottom) gives +0.06R with the draft order block and −0.37 to −0.59R with Ore's order block when the D1+H4 filter is on, on only 24–89 trades in 5 years. The old result came from picks on tiny internal swings.
- **With D1+H4 bias, setups are rare**: a real H1 MSS in the direction of both higher-timeframe trends happens ~45 times a year across both pairs, and Ore's 2/3-candle block is present at the top/bottom on about 1 in 8 of them (24–28 trades on H1 in 5 years).
- **Best rows are without the bias filter**: test A H1 order block +0.10R (358 trades, 4/5 years, but target hit 20% vs 25% chance); test B H1 first-candle edge +0.15R (115 trades, 4/5 years, hit 29%) — the only consistent row — but on EUR/USD + silver both lose (−0.07R and −0.24R).
- Test B's walk-forward "pass" is flat (+0.002R over 82 trades) and means nothing.
- Hit rates for market entries are low (10–18%) because many trades end at the 3-day time limit; the stop sits beyond the whole move, so 3R is far.
- **Verdict: no edge in either version.** Ore's order block is drawn correctly now (see charts) but does not make the strategy profitable on these markets.

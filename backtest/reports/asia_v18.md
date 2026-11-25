# Spec v18 result: Asian-session trades

Spec: `docs/spec-v18-asia.md` (committed before the run). Asia = trigger / MSS candle closing 00:00–07:00 London time. GBP/USD + gold, Nov 2021 – Nov 2026, after Ore's spreads. Existing trade logs only.

## Summary

| Strategy | Asia | London/NY | Late |
|---|---|---|---|
| CRT, all options (Ore's other rules) | 40543 · **-0.334** · 0/5 · 5% vs 10% | 47459 · **-0.134** · 1/5 · 6% vs 11% | 1412 · **-0.563** · 1/5 · 2% vs 9% |
| Order block H1 OB open (live strategy) | 62 · **+0.184** · 2/5 · 31% vs 25% | 166 · **+0.322** · 5/5 · 34% vs 25% | 6 · **-0.333** · 1/5 · 17% vs 25% |
| Order block, all TFs and entries | 4855 · **-0.107** · 0/5 · 24% vs 25% | 9346 · **-0.051** · 1/5 · 23% vs 25% | 749 · **-0.058** · 2/5 · 25% vs 25% |

CRT trades by session: Asia 45%, London/NY 53%, Late 2%.

Order block before costs (no spread): Asia -0.040R, London/NY +0.000R, Late +0.021R.

### CRT by range timeframe · entry · management

Each cell: trades · avg R after spread · years positive · target hit vs chance. ✓ = consistent.

| Row | Asia | London/NY | Late |
|---|---|---|---|
| All options | 40543 · **-0.334** · 0/5 · 5% vs 10% | 47459 · **-0.134** · 1/5 · 6% vs 11% | 1412 · **-0.563** · 1/5 · 2% vs 9% |
| D1 · E1 · M1_T1 | 21 · **+0.392** · 1/5 · 29% vs 11% | 0 · **—** · 0/5 · —% vs —% | 0 · **—** · 0/5 · —% vs —% |
| D1 · E1 · M1_T2 | 177 · **+1.111** · 3/5 · 32% vs 17% | 0 · **—** · 0/5 · —% vs —% | 6 · **-1.000** · 0/5 · 0% vs 21% |
| D1 · E1 · M1_T3 | 642 · **+0.270** · 3/5 · 10% vs 16% | 15 · **-0.615** · 0/5 · 0% vs 13% | 12 · **-1.000** · 0/5 · 0% vs 12% |
| D1 · E1 · M2_T2 | 177 · **+0.832** · 4/5 · 23% vs 17% ✓ | 0 · **—** · 0/5 · —% vs —% | 6 · **-1.000** · 0/5 · 0% vs 21% |
| D1 · E1 · M2_T3 | 592 · **+0.246** · 3/5 · 9% vs 16% | 3 · **-1.000** · 0/5 · 0% vs 12% | 6 · **-1.000** · 0/5 · 0% vs 8% |
| D1 · E2 · M1_T1 | 184 · **+0.458** · 3/5 · 14% vs 4% | 3 · **-1.000** · 0/5 · 0% vs 2% | 5 · **-1.000** · 0/5 · 0% vs 5% |
| D1 · E2 · M1_T2 | 405 · **+0.675** · 4/5 · 15% vs 11% ✓ | 8 · **-1.000** · 0/5 · 0% vs 8% | 13 · **-1.000** · 0/5 · 0% vs 11% |
| D1 · E2 · M1_T3 | 529 · **+0.526** · 3/5 · 10% vs 10% | 8 · **-1.000** · 0/5 · 0% vs 7% | 12 · **-1.000** · 0/5 · 0% vs 6% |
| D1 · E2 · M2_T2 | 395 · **+0.602** · 4/5 · 12% vs 11% ✓ | 8 · **+0.198** · 2/5 · 0% vs 8% | 13 · **-0.730** · 0/5 · 0% vs 11% |
| D1 · E2 · M2_T3 | 519 · **+0.376** · 4/5 · 5% vs 11% | 8 · **+0.198** · 2/5 · 0% vs 7% | 12 · **-0.708** · 0/5 · 0% vs 6% |
| D1 · E3 · M1_T1 | 227 · **-0.006** · 3/5 · 9% vs 4% | 3 · **-1.000** · 0/5 · 0% vs 1% | 11 · **-0.089** · 0/5 · 18% vs 7% |
| D1 · E3 · M1_T2 | 411 · **+0.409** · 3/5 · 13% vs 10% | 7 · **-1.000** · 0/5 · 0% vs 7% | 13 · **-1.000** · 0/5 · 0% vs 8% |
| D1 · E3 · M1_T3 | 552 · **-0.133** · 1/5 · 9% vs 10% | 7 · **-1.000** · 0/5 · 0% vs 6% | 12 · **-1.000** · 0/5 · 0% vs 4% |
| D1 · E3 · M2_T2 | 407 · **+0.307** · 3/5 · 11% vs 10% | 7 · **+0.041** · 1/5 · 0% vs 7% | 13 · **-0.538** · 0/5 · 0% vs 8% |
| D1 · E3 · M2_T3 | 548 · **-0.122** · 2/5 · 4% vs 10% | 7 · **+0.041** · 1/5 · 0% vs 6% | 12 · **-0.499** · 0/5 · 0% vs 4% |
| D1 · E4 · M1_T1 | 355 · **-0.337** · 2/5 · 13% vs 9% | 0 · **—** · 0/5 · —% vs —% | 8 · **-1.000** · 0/5 · 0% vs 7% |
| D1 · E4 · M1_T2 | 556 · **-0.324** · 1/5 · 10% vs 13% | 0 · **—** · 0/5 · —% vs —% | 8 · **-1.000** · 0/5 · 0% vs 7% |
| D1 · E4 · M1_T3 | 571 · **-0.477** · 1/5 · 6% vs 9% | 0 · **—** · 0/5 · —% vs —% | 8 · **-1.000** · 0/5 · 0% vs 3% |
| D1 · E4 · M2_T2 | 556 · **-0.282** · 1/5 · 10% vs 13% | 0 · **—** · 0/5 · —% vs —% | 8 · **-1.000** · 0/5 · 0% vs 7% |
| D1 · E4 · M2_T3 | 571 · **-0.382** · 0/5 · 6% vs 9% | 0 · **—** · 0/5 · —% vs —% | 8 · **-1.000** · 0/5 · 0% vs 3% |
| D1 · E5 · M1_T1 | 423 · **-0.406** · 1/5 · 9% vs 8% | 0 · **—** · 0/5 · —% vs —% | 8 · **-1.000** · 0/5 · 0% vs 5% |
| D1 · E5 · M1_T2 | 555 · **-0.509** · 1/5 · 5% vs 10% | 0 · **—** · 0/5 · —% vs —% | 8 · **-1.000** · 0/5 · 0% vs 5% |
| D1 · E5 · M1_T3 | 544 · **-0.661** · 1/5 · 0% vs 7% | 0 · **—** · 0/5 · —% vs —% | 8 · **-1.000** · 0/5 · 0% vs 2% |
| D1 · E5 · M2_T2 | 555 · **-0.445** · 1/5 · 5% vs 10% | 0 · **—** · 0/5 · —% vs —% | 8 · **-1.000** · 0/5 · 0% vs 5% |
| D1 · E5 · M2_T3 | 544 · **-0.545** · 0/5 · 0% vs 7% | 0 · **—** · 0/5 · —% vs —% | 8 · **-1.000** · 0/5 · 0% vs 2% |
| H4 · E1 · M1_T1 | 20 · **-0.032** · 1/5 · 20% vs 10% | 33 · **-0.502** · 1/5 · 0% vs 10% | 2 · **-1.000** · 0/5 · 0% vs 9% |
| H4 · E1 · M1_T2 | 454 · **-0.268** · 1/5 · 13% vs 19% | 472 · **-0.284** · 0/5 · 6% vs 19% | 6 · **-1.000** · 0/5 · 0% vs 16% |
| H4 · E1 · M1_T3 | 2621 · **-0.265** · 0/5 · 6% vs 15% | 3330 · **-0.138** · 1/5 · 4% vs 17% | 55 · **-0.056** · 3/5 · 2% vs 17% |
| H4 · E1 · M2_T2 | 454 · **-0.233** · 0/5 · 8% vs 19% | 472 · **-0.132** · 1/5 · 6% vs 19% | 6 · **-1.000** · 0/5 · 0% vs 16% |
| H4 · E1 · M2_T3 | 2115 · **-0.131** · 0/5 · 1% vs 15% | 2918 · **-0.055** · 0/5 · 2% vs 16% | 49 · **-0.434** · 2/5 · 2% vs 17% |
| H4 · E2 · M1_T1 | 339 · **-0.660** · 1/5 · 4% vs 4% | 678 · **-0.473** · 1/5 · 7% vs 5% | 13 · **-1.000** · 0/5 · 0% vs 3% |
| H4 · E2 · M1_T2 | 856 · **-0.791** · 0/5 · 3% vs 11% | 1577 · **-0.143** · 1/5 · 9% vs 11% | 33 · **-0.927** · 0/5 · 0% vs 11% |
| H4 · E2 · M1_T3 | 1397 · **-0.570** · 0/5 · 4% vs 10% | 2524 · **-0.030** · 3/5 · 5% vs 11% | 50 · **-0.436** · 1/5 · 6% vs 10% |
| H4 · E2 · M2_T2 | 848 · **-0.663** · 0/5 · 2% vs 11% | 1556 · **-0.158** · 1/5 · 7% vs 11% | 33 · **-0.701** · 0/5 · 0% vs 11% |
| H4 · E2 · M2_T3 | 1365 · **-0.432** · 0/5 · 2% vs 10% | 2484 · **-0.054** · 1/5 · 4% vs 11% | 50 · **-0.476** · 1/5 · 6% vs 10% |
| H4 · E3 · M1_T1 | 474 · **-0.772** · 0/5 · 3% vs 4% | 925 · **-0.622** · 0/5 · 6% vs 4% | 18 · **-1.000** · 0/5 · 0% vs 3% |
| H4 · E3 · M1_T2 | 1047 · **-0.678** · 0/5 · 5% vs 10% | 1771 · **-0.392** · 0/5 · 6% vs 10% | 41 · **-0.889** · 0/5 · 0% vs 10% |
| H4 · E3 · M1_T3 | 1607 · **-0.477** · 0/5 · 4% vs 10% | 2654 · **-0.251** · 0/5 · 4% vs 10% | 55 · **-0.432** · 1/5 · 5% vs 9% |
| H4 · E3 · M2_T2 | 1033 · **-0.580** · 0/5 · 3% vs 10% | 1747 · **-0.338** · 0/5 · 5% vs 10% | 41 · **-0.690** · 0/5 · 0% vs 10% |
| H4 · E3 · M2_T3 | 1586 · **-0.376** · 0/5 · 2% vs 10% | 2618 · **-0.211** · 0/5 · 2% vs 10% | 55 · **-0.369** · 1/5 · 5% vs 9% |
| H4 · E4 · M1_T1 | 673 · **-0.402** · 1/5 · 8% vs 8% | 984 · **+0.005** · 3/5 · 15% vs 9% | 45 · **-0.388** · 1/5 · 7% vs 6% |
| H4 · E4 · M1_T2 | 1333 · **-0.554** · 0/5 · 5% vs 12% | 2212 · **-0.046** · 2/5 · 10% vs 13% | 71 · **-0.625** · 1/5 · 3% vs 9% |
| H4 · E4 · M1_T3 | 1563 · **-0.232** · 1/5 · 4% vs 8% | 2536 · **-0.142** · 1/5 · 4% vs 10% | 72 · **-0.611** · 1/5 · 3% vs 7% |
| H4 · E4 · M2_T2 | 1333 · **-0.451** · 0/5 · 4% vs 12% | 2212 · **-0.039** · 2/5 · 8% vs 13% | 71 · **-0.457** · 1/5 · 0% vs 9% |
| H4 · E4 · M2_T3 | 1563 · **-0.327** · 0/5 · 3% vs 8% | 2536 · **-0.130** · 1/5 · 2% vs 10% | 72 · **-0.465** · 1/5 · 0% vs 7% |
| H4 · E5 · M1_T1 | 946 · **-0.564** · 1/5 · 6% vs 7% | 1508 · **-0.003** · 3/5 · 13% vs 8% | 62 · **-0.050** · 2/5 · 11% vs 6% |
| H4 · E5 · M1_T2 | 1449 · **-0.641** · 0/5 · 3% vs 10% | 2357 · **-0.036** · 2/5 · 9% vs 11% | 71 · **-0.560** · 1/5 · 3% vs 8% |
| H4 · E5 · M1_T3 | 1501 · **-0.375** · 0/5 · 2% vs 6% | 2457 · **-0.047** · 2/5 · 4% vs 8% | 72 · **-0.544** · 1/5 · 3% vs 6% |
| H4 · E5 · M2_T2 | 1449 · **-0.582** · 0/5 · 3% vs 10% | 2357 · **-0.056** · 2/5 · 7% vs 11% | 71 · **-0.467** · 1/5 · 0% vs 8% |
| H4 · E5 · M2_T3 | 1501 · **-0.464** · 0/5 · 2% vs 6% | 2457 · **-0.078** · 1/5 · 2% vs 8% | 72 · **-0.474** · 1/5 · 0% vs 6% |

### Order block by timeframe · entry (D1+H4 bias)

Each cell: trades · avg R after spread · years positive · target hit vs chance. ✓ = consistent.

| Row | Asia | London/NY | Late |
|---|---|---|---|
| H1 · market at MSS close | 575 · **-0.045** · 2/5 · 23% vs 25% | 1244 · **-0.032** · 1/5 · 19% vs 25% | 42 · **-0.072** · 2/5 · 23% vs 25% |
| H1 · FVG near edge | 132 · **-0.150** · 2/5 · 22% vs 25% | 248 · **+0.163** · 5/5 · 29% vs 25% ✓ | 13 · **-0.451** · 1/5 · 9% vs 25% |
| H1 · FVG middle | 127 · **-0.187** · 1/5 · 22% vs 25% | 231 · **+0.241** · 5/5 · 31% vs 25% ✓ | 13 · **-0.246** · 2/5 · 17% vs 25% |
| H1 · OB open | 62 · **+0.184** · 2/5 · 31% vs 25% | 166 · **+0.322** · 5/5 · 34% vs 25% ✓ | 6 · **-0.333** · 1/5 · 17% vs 25% |
| H1 · OB middle | 55 · **-0.040** · 3/5 · 25% vs 25% | 135 · **+0.240** · 4/5 · 34% vs 25% ✓ | 5 · **-0.200** · 1/5 · 20% vs 25% |
| M15 · market at MSS close | 2143 · **-0.071** · 1/5 · 25% vs 25% | 4256 · **-0.064** · 0/5 · 23% vs 25% | 384 · **-0.036** · 2/5 · 26% vs 25% |
| M15 · FVG near edge | 563 · **-0.119** · 0/5 · 24% vs 25% | 1011 · **-0.125** · 0/5 · 23% vs 25% | 92 · **-0.151** · 2/5 · 23% vs 25% |
| M15 · FVG middle | 516 · **-0.169** · 0/5 · 23% vs 25% | 932 · **-0.102** · 0/5 · 24% vs 25% | 87 · **-0.159** · 2/5 · 22% vs 25% |
| M15 · OB open | 372 · **-0.204** · 0/5 · 23% vs 25% | 611 · **-0.112** · 1/5 · 24% vs 25% | 56 · **+0.080** · 4/5 · 30% vs 25% ✓ |
| M15 · OB middle | 310 · **-0.253** · 0/5 · 22% vs 25% | 512 · **-0.115** · 1/5 · 24% vs 25% | 51 · **+0.165** · 3/5 · 33% vs 25% |

### Pairs separately (headline rows)

| Row | Pair | Asia | London/NY |
|---|---|---|---|
| CRT all options | GBPUSD | 21733 · **-0.354** · 0/5 · 5% vs 10% | 23246 · **-0.140** · 1/5 · 5% vs 11% |
| CRT all options | XAUUSD | 18810 · **-0.311** · 0/5 · 5% vs 11% | 24213 · **-0.128** · 1/5 · 6% vs 11% |
| Order block H1 OB open | GBPUSD | 31 · **+0.233** · 3/5 · 32% vs 25% | 81 · **+0.190** · 4/5 · 31% vs 25% |
| Order block H1 OB open | XAUUSD | 31 · **+0.135** · 2/5 · 29% vs 25% | 85 · **+0.447** · 4/5 · 38% vs 25% |

## Asia rows that passed the consistency rule

- CRT by range timeframe · entry · management: **D1 · E1 · M2_T2**: 177 · **+0.832** · 4/5 · 23% vs 17%.
  - Fresh markets (EUR/USD + silver): CRT trade logs for those markets don't exist; not run.
- CRT by range timeframe · entry · management: **D1 · E2 · M1_T2**: 405 · **+0.675** · 4/5 · 15% vs 11%.
  - Fresh markets (EUR/USD + silver): CRT trade logs for those markets don't exist; not run.
- CRT by range timeframe · entry · management: **D1 · E2 · M2_T2**: 395 · **+0.602** · 4/5 · 12% vs 11%.
  - Fresh markets (EUR/USD + silver): CRT trade logs for those markets don't exist; not run.

## Checks on the passing rows (run after the main result)

| Row | Setups (options repeat a setup) | Avg R | Without its 10 best trades | Share of profit from 10 best | Median reward:risk | 2026 |
|---|---|---|---|---|---|---|
| D1 · E1 · M2_T2 | 32 | +0.832 | +0.631 | 28% | 4.9 | -0.442 |
| D1 · E2 · M1_T2 | 104 | +0.675 | +0.042 | 94% | 8.5 | -0.563 |
| D1 · E2 · M2_T2 | 100 | +0.602 | +0.126 | 80% | 8.3 | +0.045 |

D1 decision times: 93% at 00:00 UTC (the daily close); so 'Asia' for D1 means 'decided at the daily close', and London/NY D1 rows hold only 84 trades.

## Order block H1 OB open on fresh markets (EUR/USD + silver), by session

| Session | Result |
|---|---|
| Asia | 52 · **-0.391** · 1/5 · 14% vs 25% |
| London/NY | 169 · **-0.057** · 3/5 · 26% vs 25% |
| Late | 1 · **+2.685** · 1/5 · 100% vs 25% |

## Reading

- **H4 CRT in Asia is worse than in London/NY.** Every H4 row is negative in Asia, and almost all are more negative than London/NY (e.g. H4 market entry, target 3: −0.27R Asia vs −0.14R London/NY). Ore's session rule is doing its job for H4.
- **D1 CRT "Asia" rows are not really Asian-session trades.** 93% of D1 setups are decided at 00:00 UTC, the daily close, so they land in the Asia clock window by construction. Three D1 rows passed the consistency rule, but:
  - D1 · FVG near edge rows: 80–94% of the profit comes from 10 far runners (median reward:risk 8:1); without them +0.04 / +0.13R; 2026 negative for one of them. Same pattern as the earlier v8/v9 D1 "wins".
  - D1 · market at trigger, half at 50% then T2: +0.83R, +0.63R without the 10 best, but only **32 setups** (177 rows are options of the same setups), 2026 −0.44R.
  - None has been checked on EUR/USD + silver (no CRT trade logs exist there). Many rows were tested; 3 passes out of ~60 CRT Asia rows is about what luck gives.
- **Order block in Asia is weaker than in London/NY.** H1 OB open (the live strategy): Asia +0.18R (62 trades, 2 of 5 years) vs London/NY +0.32R (166 trades, 5 of 5). On EUR/USD + silver: Asia −0.39R (52 trades, target hit 14% vs 25% chance) vs London/NY −0.06R. M15 is negative in every session. Before costs the order block is ~0 in all sessions.
- **Verdict: no Asian-session edge.** Asia does not improve either strategy; for the order block, the Asia part is the weakest part. Lead to watch, not an edge: D1 CRT market entry at the daily close (32 setups).

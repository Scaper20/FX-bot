# Spec v27: test the leads from the loss analysis (pre-registered 27 Nov 2026, before these runs)

The 2025–26 replay (live scanner) suggested three changes. Each was found after seeing results, so each is
tested here on data it was not found on, with the pass rule fixed now. A rule changes live only if it passes.

## 1. Toni Iyke: trade only in the New York session
Already looked at (27 Nov, before this spec): v22 Toni H1, D1 trend, swing-point target, 2021–2024 fills.
GBP/USD + gold New York +0.50R (29 trades); EUR/USD + silver New York −0.66R (19). Recorded as **FAIL**: it does
not hold on the second pair of markets. No further run.

## 2. CRT: skip setups in the London/New York overlap
Data: CRT trades under Ore's rules (`backtest.pattern_stats.ore_rules`), body-close rule.
- Set A: GBP/USD + gold, 2021–2024 (`backtest/out/trades_design.csv` + `trades_check.csv`).
- Set B: EUR/USD + silver, all years (`backtest/out/fvg_fresh_trades.csv`, pairs EURUSD/XAGUSD).
Unit: one number per setup = the average R of its filled options (so a setup with many option rows counts once).
"Overlap" = the CRT `session` column is `overlap` (decision time).
**Pass (adopt "skip the overlap")**: in BOTH sets, overlap setups average below 0R AND at least 0.10R below
the non-overlap setups, with at least 30 overlap setups in each set.

## 3. Order block: D1 trend only instead of D1 + H4 (more trades)
Data: v22 order-block trades, H1, 3R (`backtest/out/v22_*.csv`, model `smc_ob`), all years 2021–2026.
- Set A: GBP/USD + gold. Set B: EUR/USD + silver.
**Pass (switch the bias to D1 only)**: in BOTH sets, D1-only trades average above 0R with at least 30 trades,
and not below the D1 + H4 average.

Results are appended below; nothing above is edited after the runs.

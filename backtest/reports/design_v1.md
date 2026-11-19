# Backtest report: spec v1.1, Design period only

Period: range candles from 1 Nov 2021 to 31 Dec 2023. 2024 (Check) and 2025–2026 (Final) were **not** loaded.
Data: Dukascopy 1-minute bid, GBPUSD and XAUUSD. Day = 00:00 UTC (Exness GMT+0).
Costs: GBPUSD 1.0 pip, XAUUSD $0.35 per trade (assumption), also run at double.
Run: 20 Nov 2026, code at this commit. 30 tests pass (incl. future-price-mutation look-ahead test).

## Headline
**No edge found.** The rules as written do no better than chance after costs.

| Check | Result |
|---|---|
| Setups found | GBPUSD 1,723, XAUUSD 1,640 (1,045 / 1,009 led to at least one filled trade) |
| Variants with ≥ 1 trade | 32,139; with ≥ 60 trades: 3,644 |
| Pass rule (≥ 60 trades, average R > 0 after costs) | 324 (9%): GBPUSD 289, XAUUSD 35. Still positive at double cost: 78 |
| Best t-score among the 3,644 | 1.61. With 3,644 tries, luck alone typically produces about 3.5. **Nothing stands out from chance.** Median t-score −1.48 |
| Same trades, random direction, same stop/target distance | GBPUSD strategy −0.21 R vs random −0.23 R; XAUUSD −0.48 R vs random −0.36 R |
| Noise check (shuffled 1-minute returns) | GBPUSD: 2,018 setups, −0.30 R on noise vs 1,723 setups, −0.22 R real. XAUUSD: 1,881 setups, −0.34 R noise vs 1,640, −0.46 R real |

## Average result by option (all variants pooled, expiry 2; trades overlap, so read as direction only)
| | GBPUSD avg R | XAUUSD avg R |
|---|---|---|
| D1 range / H4 range | −0.07 / −0.26 | −0.38 / −0.48 |
| Entry H1 / M15 / M5 | +0.12 / −0.23 / −0.25 | −0.42 / −0.40 / −0.50 |
| E1 market / E2 FVG edge / E3 FVG mid / E4 OB open / E5 OB mid | −0.06 / −0.37 / −0.62 / −0.04 / +0.02 | −0.14 / −0.44 / −0.60 / −0.38 / −0.62 |
| Stop S1 sweep extreme / S2 tight | −0.02 / −0.42 | −0.33 / −0.59 |

## Why it loses
1. **Spread vs tight stops.** Median cost as a share of risk: M5 with tight stop = 48% (GBPUSD) and 80% (gold). Even M5 with the sweep stop costs 14% / 23% of risk per trade.
2. **The pattern is very common.** A CRT by the v1 definition appears on about 1 in 9 range candles, and just as often on random data. Tiny sweeps count (example: gold 20 May 2022, sweep of $0.25).
3. **Entries often happen at the sweep candle's close**, because the CISD already formed inside it, including Friday closes held over the weekend gap.

## Not done yet (on purpose)
- The Check period (2024) was **not run**. The design evidence already shows no edge; running it now would use up 2024 on a version we expect to change.
- Final period untouched.

## Example charts
`backtest/reports/examples/` (8 random setups, with a text description of each).

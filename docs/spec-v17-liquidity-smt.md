# Spec v17: liquidity models + SMT divergence (pre-registered 25 Nov 2026, before any result)

Ore's request: test the liquidity concept with SMT. Uses the two Inter Equity liquidity models exactly as in spec v14 (same setups, same orders, same scoring after Ore's spreads), and adds an **SMT** check from the correlated market: **GBP/USD ↔ EUR/USD**, **gold ↔ silver**. Script: `backtest/liq_smt.py`. Nov 2021 – Nov 2026, Exness candles (GMT+0).

## SMT, defined so it is known before the entry (sell shown; buy is the mirror)
- **4-candle sniper:** GBP/USD's C2 trades above C1's high (the liquidity sweep). **SMT = on the same candles, EUR/USD's C2 does NOT trade above its own C1 high.** Known when C2 closes, before the entry in C4.
- **Induce → trap:** the entry is when price takes the retail high. **SMT = from that high's candle until the minute the order fills, EUR/USD does NOT trade above its own high of that same candle.** Checked on 1-minute data up to the fill minute (no look-ahead).
- If the partner has no candle at the same time, the SMT check is "unknown" and the trade is left out of both groups.

## Compared
For every v14 "alone" row (model × entry × timeframe × management, all sessions): **SMT trades vs no-SMT trades**, average R after spread, per year, target hit vs chance.

## Judged
An SMT row counts only if: at least 30 trades, average after spread > 0 and positive in at least 4 of the 5 years 2022–2026, target hit at least as often as chance, **and** better than the same row without SMT. Walk-forward on the SMT trades (spec v7 rule). Anything that passes is run with the roles swapped (**EUR/USD with GBP/USD as partner, silver with gold as partner**), unchanged, before it counts.

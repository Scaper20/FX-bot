# Spec v5: weekly and monthly trend following (pre-registered 20 Nov 2026, before any result)

Ore asked to try longer timeframes. Rules are the **classic published ones, used as published (no tuning)**. Script: `backtest/trend_long.py`. Data: `data/long/` (FRED FX from 1971, gold/silver futures from 2000).

**Markets:** GBP/USD, EUR/USD (from 1999), USD/JPY, USD/CHF, USD/CAD, AUD/USD, NZD/USD, USD/SEK, USD/NOK, gold, silver.

**Signals** (long when the signal is up, short when down; re-decided at each period end, held to the next):
| Code | Rule | Source |
|---|---|---|
| M12 | Sign of the last **12 months'** return, monthly rebalance | Moskowitz, Ooi & Pedersen (2012) |
| M3, M6, M1 | Same with 3 / 6 / 1 month lookbacks | same paper's variants |
| SMA10 | Month-end close above its **10-month average**: long, below: short | Faber (2007) |
| W52, W26, W13, W4 | Sign of the last 52 / 26 / 13 / 4 weeks' return, weekly rebalance (Friday close) | weekly version of the same idea |
| DON | Weekly close above the 26-week high: long until a close below the 13-week low (mirror for shorts) | Donchian channel |

**Sizing:** each market is scaled to 10% yearly volatility (using its last 60 days), capped at 3×. The portfolio is the average across all markets available at the time.

**Costs per change of position:** FX 0.02% of the position, gold/silver 0.05%.

**Judged on:**
- the **portfolio** and on **GBP/USD and gold alone**;
- in four windows: whole history; **1971–2012** (before the main paper); **2013–2026** (after publication, the honest test for a published rule); **2021–2026** (the period we've been trading).

"Works" = Sharpe ratio > 0.3 after costs **in 2013–2026**, and positive in at least 60% of those years. Sharpe = yearly return ÷ yearly volatility; 0.3 is modest, and well-run trend funds have historically managed 0.3–0.8.

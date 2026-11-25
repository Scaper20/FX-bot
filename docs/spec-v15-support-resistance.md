# Spec v15: simple support and resistance (pre-registered 25 Nov 2026, before any result)

Ore asked to test plain support/resistance and to understand why results keep coming out negative. Every trade is scored **twice: with no costs and with Ore's spreads** (GBP/USD 1.0 pip, gold $0.24), so the effect of costs is visible on its own. GBP/USD and gold, Nov 2021 – Nov 2026, Exness candles (GMT+0), events found on M15, outcomes on 1-minute data (stop first if both hit in a minute). Script: `backtest/sr_simple.py`.

## Levels (four common kinds)
| Level | Definition | Active |
|---|---|---|
| **Daily swing** | D1 swing high/low (2 candles each side), known 2 days later | 20 trading days |
| **4-hour swing** | H4 swing high/low (2 candles each side), known 2 candles later | 5 trading days |
| **Yesterday's high/low** | previous D1 candle's high and low | the next day |
| **Round number** | GBP/USD every 50 pips (x.xx00, x.xx50); gold every $10 | each day, the nearest one above and below the day's open |
A level below price when it becomes active is **support**, above is **resistance**.

## Two trades per level (first event only)
- **Bounce:** limit order at the level on the first touch (buy at support, sell at resistance).
- **Breakout:** the first M15 candle that **closes beyond** the level: enter at that close in the break direction.
- **Stop:** 0.25 × the 14-day average daily range beyond the level (other side of the level for both).
- **Targets:** 1R, 2R and 3R (all out), reported separately, with the chance win rate for each (1R 50%, 2R 33%, 3R 25%).

## Reported
Trades, win rate vs chance, average R **before** and **after** spread, years positive (2022–2026). "Works" = after spread positive in at least 4 of 5 years and in total, with at least 100 trades, and win rate above chance. 4 levels × 2 trades × 3 targets = 24 rows per pair, pooled over both pairs.

## Addendum (25 Nov 2026, after the main run, before this check)
2 of 24 rows met the rule (daily-swing breakout 1R, 4-hour-swing breakout 2R), and breakouts beat bounces in every level type. Same script, unchanged, on **EUR/USD (1.0 pip, round numbers every 50 pips) and silver ($0.025, round numbers every $0.50)**. The two rows pass only if, on the new markets pooled, average R after spread > 0 and positive in at least 3 of 5 years. Also reported: whether breakouts still beat bounces before costs.

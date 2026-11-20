# SMT test (pre-registered 20 Nov 2026, before any result)

Romeo's notes, section 9: one market takes a high or low and its correlated partner does not.
Pairs: **GBP/USD with EUR/USD**, **gold with silver** (both move together, so a divergence at a sweep is the "signal").
Data: Dukascopy 1-minute bid, `data/eurusd-…zip`, `data/xagusd-…zip`. Script: `backtest/smt.py`.

**SMT at a CRT** (bearish; bullish is the mirror): during the sweep candle C2, our market's high goes above C1's high, but the partner's C2 high stays **at or below the partner's own C1 high**. The candles are the same New York-clock D1 or H4 candles on both markets. Romeo: only "bullish SMT in a bullish market", so it is also tested together with the HTF-bias condition.

**Groups compared:** SMT present vs absent; SMT + HTF bias; for both entries (at C2's close, Candle-3 trap + Model #1), D1 and H4, both of Ore's pairs. That makes 2 entries × 2 timeframes × 2 SMT groups = 8 tests on the main question.

**Pass mark, fixed now:**
- Design (Nov 2021 – Dec 2023): SMT-present trades reach Target 1 more often than chance with **z ≥ 2.5** and at least 40 trades, **and** beat the no-SMT trades of the same group.
- Then 2024 once (z ≥ 2). Then, only with Ore's go-ahead, 2025–2026 once.

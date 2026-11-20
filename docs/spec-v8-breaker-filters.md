# Spec v8: breaker entry with Ore's v1.2 filters, and with Romeo's 3 filters, each with and without MSnR
(pre-registered 20 Nov 2026, before any result)

Ore's request: test separately, not stacked: (1) v1.2 filters + breaker, (2) Romeo's 3 filters + breaker, (3) = 1 + MSnR, (4) = 2 + MSnR. Script: `backtest/breaker_filters.py`.

**Frame (same as v6 context A):** CRT on the New York clock, D1 → M15 entries, H4 → M5 entries. C2 swept C1 and closed back inside. The first breaker that shifts after C2's close and before C3's close. Entries **edge / mid / confirm** × stops **classic / tight** (definitions in `spec-v6-breaker.md`). Targets: half at 50% of C1 (stop to entry), rest at C1's far side. 1-minute outcomes, spread included. All filters use only what is known when the order is placed.

**Ore's v1.2 filters (all required):**
- Sessions: the order is placed (the shift candle's close; for confirm, the confirming candle's close) in London 07:00–16:00 London time or New York 08:00–17:00 New York time.
- Not Friday from 15:00 New York.
- Direction: **with** the daily direction (NY daily close below a falling 20-day average for shorts; mirror for longs, the option v1.2 picked), **or** against/unclear only if the sweep band (C1's high to C2's high) overlaps an older intact bearish FVG or order block on the range timeframe (last 60 candles, `htf_zone_overlap`).
- Sweep depth: C2's high at least 0.1 × the 14-candle average range beyond C1's high (the size option v1.2 picked).

**Romeo's 3 filters (all required; each alone also shown for information):**
- F1: higher-timeframe bias agrees (Romeo's next-candle rule on the last closed W1 candle for D1 ranges, D1 candle for H4).
- F2: the sweep also takes the highest high of the previous 10 range candles.
- F3: D1 range candle on Monday/Tuesday (New York); H4 range candle opens 01:00 NY and sweep candle 05:00 NY, with the entry by 10:30 NY on C3's day.

**MSnR (added in tests 3 and 4):** the storyline agrees (last close-break of an A/V level on W1 for D1 / D1 for H4, as v4), and a fresh A-level sits in the sweep band (within 0.1 ATR), as v4 "MSnR full". Targets stay the CRT targets so only the filter changes.

**Judged:**
- Per test, per row (timeframe × entry × stop): trades, average R after spread per year, total.
- **Consistent** = positive in at least 4 of 5 years (2022–2026) and in total, with at least 30 trades.
- Walk-forward per test (spec v7 rule: units = timeframe × entry × stop × pair, at least 30 training trades); if no unit ever has 30 training trades, that's reported as "too few trades to walk forward".
- Trade counts are always shown.

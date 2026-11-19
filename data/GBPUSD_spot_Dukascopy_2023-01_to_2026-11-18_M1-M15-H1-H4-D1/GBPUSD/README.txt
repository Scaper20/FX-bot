GBP/USD historical data - Dukascopy Bank SA spot feed (BID prices)
Range: 2023-01-01 23:04:00 UTC to 2026-11-18 21:59:00 UTC (ends at the 2026-11-18 New York 17:00 close, last complete trading day)
Rows: M1 1443718 | M15 96768 | H1 24195 | H4 6051 | D1 1010

THIS IS SPOT, NOT FUTURES. Source: datafeed.dukascopy.com (Swiss bank/ECN, BID side quotes).

TIME CONVENTIONS
- M1, M15, H1: Time_UTC = bar OPEN time in UTC.
- H4: Time_UTC = bar OPEN time in UTC, but bars are aligned to the forex trading day (New York 17:00 close),
  i.e. the same H4 bars you see on a typical MT4/MT5 broker running GMT+2 (winter) / GMT+3 (US summer time).
  In UTC the H4 opens are 22,02,06,10,14,18 in winter and 21,01,05,09,13,17 in summer.
- D1: Date = trading date. Each day runs New York 17:00 -> 17:00, so there are 5 bars per week and no Sunday stub bar
  (the Sunday-evening open belongs to Monday's bar). Matches MT4/MT5 GMT+2/+3 broker daily candles.

HOW IT WAS BUILT
- All timeframes are aggregated from the same M1 bars (Open=first, High=max, Low=min, Close=last, Volume=sum), so they are
  internally consistent: every D1 bar equals the aggregate of its H4 bars, volume totals match across all files.
- Minutes with zero ticks (weekends, holiday closures, gold's daily 1-hour break) were removed rather than filled with flat bars.
- Volume = Dukascopy tick-volume (relative activity measure, not exchange volume). Prices are BID; add spread if you need ASK.

QUALITY CHECKS PASSED
- No duplicate or unsorted timestamps, all on the minute grid, no zero/negative prices, no OHLC inconsistencies (High>=Open/Close>=Low).
- No missing day files. Every weekday has data except genuine market closures
  (Christmas, New Year; for gold also Good Friday and US-holiday early closes).
- Largest 1-minute moves checked: they line up with scheduled US data releases (13:30 UTC NFP/CPI) and genuine news events,
  not bad ticks.
- Cross-checked against Dukascopy's own official daily candles (2023-2025): GBP/USD 935/938 days identical, the 3 others differ
  by <=0.5 pip on the final minute; XAU/USD 933/934 identical, the 1 exception (2024-12-12) is an error in Dukascopy's daily
  candle - their hourly candles confirm these figures.

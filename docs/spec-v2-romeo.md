# Spec v2: Romeo's CRT, as written in Ore's training pack (pre-registered 20 Nov 2026, before any v2 result)

Source: `Romeotpt_CRT_Strategy_Notes.md` and `CRT_Visual_Reference_and_Gap_Topics.md` (Ore, 20 Nov 2026).
Test data: Design period only (Nov 2021 – Dec 2023). Bearish rules shown; bullish is the mirror.

## Clock (Romeo: "all times are New York time")
- D1 = New York day, 00:00–24:00 NY. The short Sunday-evening piece is dropped (Romeo treats Monday 00:00 as the true open).
- H4 = New York grid 01, 05, 09, 13, 17, 21 (the "1/5/9" candles).
- Week = Monday–Friday on New York dates.

## The CRT (C1, C2, C3)
- C1 = range candle. C2 = the next candle; its high goes above C1's high and it **closes back inside** C1 (low not below C1's low). k = 1 only ("the next candle").
- C3 = the candle after C2. Romeo: "tape-read C2, trade C3", so nothing is entered before C2 has closed.

## Entry model: Candle 3 trap + Model #1 (the new part)
On the entry timeframe (D1 → M15, H4 → M5), inside C3 only (D1: until 16:00 NY, Romeo's action window):
1. Price must first trade **above C3's open** ("sell above the open").
2. **Model #1 candle** = the up-close candle that made the highest high of C3 so far, and it must be **thick**: body ≥ 50% of its own range and ≥ the median body of the previous 20 candles.
3. **Trigger** = a later candle **closes below the Model #1 candle's body low** (its open). A wick does not count.
4. Entry at the trigger close. **Stop** above C3's high so far. **Target 1** = 50% of C1, **Target 2** = C1's low.
5. Skip if price already reached 50% of C1 before the trigger ("two-candle CRT: log it as a miss").

## Filters tested (each alone, then combined)
| Code | Rule |
|---|---|
| F1 HTF bias | The last closed higher candle (W1 for D1 CRTs, D1 for H4 CRTs) points the same way: bearish if it closed below the previous candle's low, or wicked above its high and closed back inside |
| F2 Key level | C2's high also takes an **older high**: above the highest high of the 10 candles before C1 (Romeo: pair the key level with an old high) |
| F3 Time | D1: C1 on Monday or Tuesday, sweep on Tuesday or Wednesday (weekly profile). H4: C1 = the 01:00 NY candle, C2 = 05:00, entry in the 09:00 candle before 10:30 NY (1/5/9 model) |
| ALL | F1 + F2 + F3 |

Also reported, as a control: the old entry at C2's close (v1), on the New York clock.

## How it is judged (fixed now)
- Main measure, no costs: how often price reaches Target 1 / Target 2 before the stop, against the chance rate `risk / (risk + reward)` for each trade (the method of `backtest/reports/diagnosis.md`). Then average R after spread with Romeo's management: half off at 50%, stop to entry, rest to C1's opposite side.
- 2 pairs × 2 timeframes × 6 variants = 24 tests, so a result counts only with **z ≥ 3** (pooled over both pairs) and at least 60 trades.
- A survivor goes to 2024 once (z ≥ 2 required there; 2024 was used once before for v1.2, so this is weaker evidence and will be said so). Only then, with Ore's go-ahead, the untouched 2025–2026 Final.

## Not testable yet
- **SMT** needs a correlated market (EUR/USD for GBP/USD, silver for gold). Not in our data.
- Key-level ranking, "6 candle shapes", exact timing windows: not public (pack section 14).

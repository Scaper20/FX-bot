# Spec v19: classic reversal and continuation chart patterns (pre-registered 25 Nov 2026, before any run)

Ore asked: "Let's test patterns now. Reversal and continuation patterns." Ore gave no definitions, so these are
the **textbook definitions** (Edwards & Magee / Bulkowski style), made exact so a computer can find them without
looking ahead. Nothing here is tuned; numbers are fixed before the run.

## Building blocks
- Markets: GBP/USD and spot gold (main test); EUR/USD and silver (fresh-market check, same code, never used to
  choose anything). Dukascopy M1, Nov 2021 – Nov 2026, Exness GMT+0 candles. Spreads: GBP/USD and EUR/USD 1.0 pip,
  gold $0.24, silver $0.025 (Ore's).
- Timeframes: M15, H1, H4, D1.
- **Swing high / low:** a candle whose high (low) is above (below) the 3 candles on each side. It is only *known*
  3 candles later; nothing is used before that.
- **ATR:** average true range of the last 14 closed candles.
- Every pattern is coded in its bearish form; bullish versions are the exact mirror (prices flipped).

## Reversal patterns
1. **Double top / bottom.** Two swing highs 5–60 candles apart, within 0.25 ATR of each other, nothing higher in
   between; neckline = lowest low between them; height = higher top − neckline ≥ 1 ATR; prior trend up (the
   30 candles before the first top went below the neckline). Breakout = first close below the neckline within
   30 candles after the second top, before any high above the higher top. Stop above the higher top.
2. **Head and shoulders (and inverse).** Three swing highs: head above both shoulders, shoulders within 1 ATR of
   each other, 10–120 candles from left shoulder to right; neckline = line through the lowest low between left
   shoulder and head and the lowest low between head and right shoulder; height = head − neckline under the head
   ≥ 1 ATR; prior trend up (30 candles before the left shoulder went below both neckline lows). Breakout = first
   close below the neckline within 30 candles after the right shoulder, before any high above the head. Stop above
   the right shoulder.

## Continuation patterns
3. **Flag.** Pole: a swing low reached from the highest high of the 15 candles before it, a fall of ≥ 3 ATR.
   Flag: the next 5–25 candles, never retracing more than 50% of the pole, drifting flat or against the pole
   (slope of a straight line fitted to the closes ≥ 0). Lower line: line fitted to the flag's lows, moved down
   to touch the lowest. Breakout = first close below the lower line. Stop above the flag's highest high.
4. **Triangle (symmetrical or descending; mirrored: symmetrical or ascending).** Latest two swing highs falling,
   latest two swing lows flat or rising (second ≥ first − 0.1 ATR), all four within 10–80 candles; prior trend
   down (the 30 candles before the triangle reached ≥ 1 ATR above its first high). Lower line through the two
   lows, upper line through the two highs. Breakout = first close below the lower line within 30 candles after the
   last swing is known, before any close above the upper line. Height = first high − lower line under it. Stop
   above the last swing high.

All stops get + 2 spreads (as in every spec since v1.2).

## Entries, targets, holding
- **E1** market at the breakout candle's close (or at the candle when the last swing became known, if later).
- **E2** limit at the broken line (retest), valid 10 candles.
- **Targets:** **MM** = the textbook measured move (pattern height, or pole length for flags, projected from the
  breakout price; from the line price for E2); **2R**.
- Close after M15 2 days, H1 5 days, H4 15 days, D1 45 days if neither stop nor target is hit.
- Scored on 1-minute data: stop first if both are hit in one minute; spread paid; results also shown with no costs.

## Rows and pass rule
4 patterns × 4 timeframes × 2 entries × 2 targets = 64 rows (GBP/USD + gold pooled), also reported by pair.
A row is **consistent** if it has ≥ 30 trades, average R after spread > 0 in total and in ≥ 4 of the 5 years
(2022–2026), and its target hit rate ≥ chance (risk / (risk + reward)).
A consistent row then has to hold, unchanged, on EUR/USD + silver (positive average, ≥ 3 of 5 years, hit ≥ chance),
and pass the walk-forward (spec v7, family = all 64 rows). Only a row passing all three counts as a lead worth
watching live. With 64 rows, about 3 can look consistent by luck.

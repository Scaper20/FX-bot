# Spec v25: Ore's model after a higher-timeframe POI tap, plus variations (pre-registered 27 Nov 2026, before any run)

Ore (27 Nov, three sketches): "Price initially taps into an HTF OB or BB or FVG or relevant point ... once it
taps into it, then you implement the pattern. The pattern is basically an entry model to enter a trade on the
lower time frames. But before you use the pattern, the price has to reach a higher time frame point of interest
(a 4-hour or daily order block, or price action) ... run the test and see if you can make other variations as
well. Whatever produces the best results, show it to me."

## HTF POI (strict, unlike v24)
On H4 and D1 (external structure, close breaks):
- **OB**: Ore's 2/3-candle order block at the origin of each structure event. A sell zone at tops, a buy zone at
  bottoms. Known at the close of the event candle.
- **BB**: an HTF OB that a later HTF candle closed through (failed). It becomes a zone the other way, known at
  that close.
- **FVG**: a three-candle fair value gap; a bearish one is a sell zone. Known at its third candle's close.

A reversal setup (spec v24 pattern) qualifies when:
- the HTF zone points the trade's way;
- it was known before the lower-timeframe top (sell) / bottom (buy) candle;
- the top's high (bottom's low) is **inside the zone**;
- this was the zone's **first tap**: the first H1 candle to reach the zone after it formed is within 20
  lower-timeframe candles before the top, or is the top itself.

## Variation grid
| Dimension | Options |
|---|---|
| HTF | H4 / D1 / either |
| POI type | OB / BB / FVG / any |
| LTF | H1 / M15 / M5 |
| LTF structure | close breaks / wick breaks ("a break is a break") |
| Entry POI | OB at the top / BB at the broken swing / nearest |
| Target | 3R / 5R |
| Bias | D1 trend / none |

That is 864 rows, plus the same LTF rows with **no HTF POI** requirement (the baseline). Markets: GBP/USD + gold
(main), EUR/USD + silver (check). Nov 2021 – Nov 2026, Ore's spreads, 1-minute scoring. The pattern, orders, stop
and hold are exactly spec v24.

## How the "best" is chosen (fixed now, to limit luck)
1. On GBP/USD + gold only:
   - take the rows with ≥ 30 trades;
   - rank them by t-statistic (average R after spread ÷ its standard error);
   - keep the **top 10**.
2. Each of the 10 is run unchanged on EUR/USD + silver. It **holds** if the average there is > 0, it is positive
   in ≥ 3 of 5 years, and its target hit rate is ≥ chance.
3. **Walk-forward over the whole grid:**
   - each year, choose the best row on the past years only (≥ 30 trades);
   - trade it blind the next year (2023–26);
   - pass = positive overall and in ≥ 3 of 4 years.
4. **Luck check:** count how many rows are positive with t ≥ 2. Under no edge, about 2.5% of rows reach t ≥ 2 by
   chance (more, because the rows overlap).

A row counts as a real lead only if it is in the top 10, holds on EUR/USD + silver, **and** the grid passes the
walk-forward. Ore sees the top rows whatever happens, with these checks next to them.

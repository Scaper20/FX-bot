# Spec v24: Ore's liquidity model, reversal and continuation (pre-registered 27 Nov 2026, before any run)

Source: Ore's four sketches (27 Nov 2026). In his words: it should "always be in line with the daily bias and
market direction"; it "aims to come at the beginning of a move", so it suits swing trades and bigger R; the best
trades start at a higher-timeframe POI (OB or FVG), with the pattern then forming on the lower timeframe (M15, M5,
H1). It "waits for a fake move to first occur and trap early trades, then capitalises on them as liquidity". The
last sketch is a continuation pattern using a breaker block in the market direction.

Structure = `engine/smc_structure.external_structure` (close breaks; main swings only). Sell version below; buy
is the mirror.

## Model R: reversal
1. **MSS** (event 1): the lower-timeframe uptrend's protected higher low is closed through. The top of that move
   is the event's origin.
2. **BOS** (event 2): the very next structure event, in the same direction. It closes below the low made after
   the MSS. Its protected swing (the lower high in between) is **Liq**.
3. **POI**, which must sit above Liq, so that price has to take Liq first (the fake move):
   - **OB** = Ore's 2/3-candle order block at the top of the move (event 1's origin). Entry at the first
     candle's near edge; stop above the block / top.
   - **BB** = Ore's 2/3-candle *bullish* order block at the higher low that the MSS closed through (a failed OB,
     so now a breaker). Entry at its near edge from below (its low); stop above its high.
   - Variants: **OB**, **BB**, and **nearest** (BB if valid, else OB: the first one price reaches).
4. **Order:** limit placed at event 2's close, valid 30 candles of the pattern timeframe. Stop + 2 spreads.

## Model C: continuation with a breaker
1. Two structure events in a row in the same direction: BOS A, then BOS B.
2. **Liq** = event B's protected swing (the pullback between them).
3. **BB** = the zone at the swing that BOS A broke:
   - Ore's 2/3-candle block containing that swing, in the opposite direction (a supply block at a broken high,
     which failed);
   - else that swing candle, wick to wick.
4. For a buy, the BB must sit below Liq. Entry at the BB's near edge (its top for a buy); stop beyond it.
   Limit placed at B's close, valid 30 candles.

## Shared
- **Timeframes:** H1, M15, M5.
- **Bias:**
  - **D1 trend** (D1 external trend, main);
  - **none** (information).
- **Targets:** 3R and 5R. Hold: H1 10 days, M15 5 days, M5 3 days (swing-style).
- **Information split (reversal model only):** whether the top of the move traded into a higher-timeframe POI.
  That means an unfilled H4 FVG on the right side, or Ore's H4 order block at an H4 structure origin, formed
  before the top.
- **Markets and data:** GBP/USD + gold (main), EUR/USD + silver (fresh check). Nov 2021 – Nov 2026, Ore's
  spreads, 1-minute scoring.

## Pass rule (unchanged)
A row is **consistent** if:
- it has ≥ 30 trades;
- its average R after spread is > 0 overall and in ≥ 4 of 5 years;
- its target hit rate is ≥ chance.

A consistent row must then hold on EUR/USD + silver, and each model family must pass the walk-forward.

Random example charts (zone boxes, BOS/MSS lines, Liq marked) go to Ore for checking before anything goes live.

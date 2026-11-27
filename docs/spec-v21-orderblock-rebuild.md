# Spec v21: order-block strategy rebuilt on real market structure (pre-registered 27 Nov 2026, before any run)

Why: Ore's review (27 Nov) showed the SMC drawings were wrong. Every 5-bar fractal counted as structure, so the
v16 "MSS" (the live order-block strategy) was often a break of a tiny internal swing, and its order block a minor
candle. Ore asked for two tests: **A** = the rebuilt strategy without his order-block update, **B** = with it.

## Shared (A and B)
- Markets: GBP/USD + spot gold (main), EUR/USD + silver (fresh check, same code). Dukascopy M1 Nov 2021 – Nov 2026,
  Exness GMT+0 candles, Ore's spreads, 1-minute scoring (stop first if both hit in a minute).
- **Structure** (`engine/smc_structure.py: external_structure`, close breaks), on every timeframe:
  - **BOS** = a close beyond the fixed extreme of the current leg. The extreme is fixed once 2 lower highs (or
    higher lows) follow it.
  - **MSS** = a close beyond the protected swing: the higher low (or lower high) that launched the last BOS.
  - "A break is a break" (Ore): the broken level counts even if it is a single spike wick, and the breaking
    candle counts even if it is a news candle.
- **Bias** = D1 and H4 external trends both point the trade's way, known at the decision candle's close (variant:
  no bias).
- **Trigger** = an MSS on the entry timeframe (H1, live; M15 variant) in the bias direction. The **origin** is the
  extreme of the move the MSS came from (the top for a sell).
- Orders:
  - Stop beyond the origin extreme (or the order block's extreme if further) + 2 spreads.
  - Target 3R.
  - Limit valid 12 entry-timeframe candles; closed after 3 days. No cancel at 50% (as v16).

## A: draft order block
- OB = the last opposite-colour candle at or up to 5 candles before the origin, plus any opposite-colour candles
  directly before it, marked wick to wick.
- Entries:
  - **E1** = market at the MSS close (structure-only reference).
  - **OB** = limit at the block's near body edge.

## B: Ore's order block (his words, 27 Nov)
"Most of the time two candles, sometimes three": a formation where the last candle's momentum takes over the
previous one or two candles; the rectangle is drawn from the first candle. Made exact (sell version; buy = mirror):
- **2-candle**: an up-close candle, then a down-close candle that closes below the first candle's body (below its
  open). This is the engulfing.
- **3-candle**: a candle, then a pin bar (upper wick at least 2 × its body and at least half its range), then a
  down-close candle that closes below the bodies of both earlier candles.
- The formation must contain the origin candle (the top of the move). If both kinds fit, the 3-candle one is used.
  No formation → no setup.
- Box: from the first candle, from the first candle's low up to the formation's high.
- Entries:
  - **edge** = limit at the first candle's low (the box's near edge).
  - **body** = limit at the first candle's body bottom.

## Rows and pass rule
- A: TF (H1/M15) × entry (E1/OB) × bias (on/off) = 8 rows.
- B: TF × entry (edge/body) × bias = 8 rows.
- Same rule as since v7:
  - **Consistent** = ≥ 30 trades, average R after spread > 0 overall and in ≥ 4 of 5 years (2022–26), and
    target hit rate ≥ chance (25% at 3R).
  - A consistent row must then hold on EUR/USD + silver (positive, ≥ 3 of 5 years, hit ≥ chance).
  - Each test (A, B) must pass the walk-forward.
- Old v16 numbers are shown beside the new ones for comparison only.
- Example charts drawn with the new drawing code (zone boxes, BOS/MSS lines) for Ore to check, before anyone
  relies on the numbers.

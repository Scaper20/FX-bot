# Spec v22: Toni Iyke and Lingard rebuilt on real market structure, then live (pre-registered 27 Nov 2026)

Ore asked to push the strategies live. v20 (Toni, Lingard) used the flawed tiny-swing structure, so both are
rebuilt first on `engine/smc_structure.external_structure` and Ore's order block, re-tested, then put live with
the corrected order-block strategy (v21 test B). The rules live in `engine/smc_models.py`; the backtest and
the live scanner both call it.

## Shared
- Markets: GBP/USD + gold (main), EUR/USD + silver (fresh check).
- Data: Dukascopy M1, Nov 2021 – Nov 2026, Ore's spreads.
- Stops: + 2 spreads beyond the far edge.
- Scoring: 1-minute data; stop first if both are hit in one minute.
- Hold limits: H4 10 days, H1 5 days, M15 2 days.

## Order block (v21 test B, unchanged)
- **Bias:** D1 and H4 external trends agree.
- **Trigger:** an H1 MSS.
- **Order block:** Ore's 2- or 3-candle block at the top or bottom of the move, complete by the MSS candle.
- **Entry:** limit at the first candle's near edge, valid 12 candles.
- **Stop and target:** stop beyond the block or the move's extreme; target 3R.

## Toni Iyke (trading TF H1, M15)
- **Structure (body closes):**
  - MSS (reversal).
  - Multiple BOS: a BOS whose leg closed beyond **≥ 2 swing levels** that were intact when the leg began (the
    external level plus at least one more). A single BOS is ignored.
- **Inducement:** the first pullback after the structure candle (an opposite-colour candle, or a wick beyond the
  previous candle). It is valid once a later candle body-closes beyond the structure candle's close, within 30
  candles.
- **POIs:**
  - **Breakers:** the body of each level broken. Entry at the body edge; stop beyond that candle.
  - **Order block:** Ore's 2- or 3-candle block at the origin. Entry at its wick end if the wick is shorter than
    the body, else at the body; stop beyond the whole block.
- **Picking the POI (the 4 rules):** the POI must not have been reached by the inducement leg (body), and the
  one closest to the inducement is used.
- **Targets:**
  - **liq:** the swing-point extreme between the structure candle and the inducement confirmation.
  - **5R.**
- **Bias:** D1 external trend (on / off).
- **Rows:** structure (MSS / multiple BOS) × TF × target × bias = 16.

## Lingard (setup TF H4, H1)
- **Structure:** wick breaks (his rule).
- **Liquidity:** the first BOS after an MSS in the same direction. Its pullback (the protected swing) is the
  first-pullback liquidity.
- **POI:** Ore's 2- or 3-candle order block beyond that liquidity and nearest to it (within 1.5 ATR), inside the
  move that started the new trend.
- **Entry and stop:** limit at its near edge, stop beyond it.
- **Targets:**
  - **liq:** the BOS extreme, kept only if reward:risk ≥ 5 (his minimum).
  - **5R.**
- **Session:** London or New York.
- **Bias:** D1 external trend (on / off).
- **Rows:** TF × target × bias = 8.
- **Not tested:** his pattern B (first pullback after the BOS) and breakers.

## Pass rule (unchanged since v7)
A row is **consistent** if:
- it has ≥ 30 trades;
- its average R after spread is > 0 overall and in ≥ 4 of 5 years;
- its target hit rate is ≥ chance.

A consistent row must then hold on EUR/USD + silver, and each strategy must pass the walk-forward.

## Going live
Ore's decision (27 Nov 2026): all three go live whatever the result. Each card and strategy page shows this
test's result honestly. Live versions use the main rows:
- **Order block:** D1+H4, H1.
- **Toni:** D1 bias, H1, liq target.
- **Lingard:** D1 bias, H4, 5R.

Example charts are drawn with zone boxes and BOS/MSS lines for Ore to check.

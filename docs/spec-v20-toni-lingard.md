# Spec v20: Toni Iyke and Lingard SMC models (pre-registered 27 Nov 2026, before any run)

Ore supplied two packs (`docs/toni_pack/`, `docs/lingard_pack/`) and asked: compare Toni Iyke's official-channel notes
with the student's notes from his paid classes (merge or keep separate?), then test Toni and Lingard.

## Part 1: Toni Iyke, official vs paid classes

| Topic | Official channel (`toni_pack/ToniIyke_…Notes.md`) | Paid classes (`toni_pack/classes/`) | Same? |
|---|---|---|---|
| Model | Bias → HTF zone → MSS → inducement → POI | Same, plus continuation via **multiple BOS** | Same idea |
| Structure break | "takes out the last high/low" | **Body close** required (MSS, multiple BOS, inducement) | Classes add detail |
| Continuation entries | Repeat the MSS → inducement → POI model | **Multiple BOS** (≥ 2 levels; single BOS ignored) | Classes add detail |
| Inducement | First pullback after the MSS | First pullback, **valid only once a candle body-closes beyond the MSS/BOS candle's close** | Classes add detail |
| POI choice | Unmitigated **breaker first, else OB** (third-party PipslayerFX explainer) | **4 rules**: structure, inducement, unmitigated (body touch), **closest to the inducement** (breaker or OB) | **Conflict** |
| OB definition | Last opposite candle before the move | Opposite candle **engulfed** by the next candle; entry at wick or body (wick-length rule) | Classes add detail |
| Timeframes | 4H bias, 15m–1H entries | Daily (mostly) bias, **1H** analysis and entry on one timeframe | Small difference |
| FVG | Not mentioned | **Not used** | Same |
| Targets | Nearest liquidity, trendline liquidity, bias target | Same; swing-point liquidity "highest hit rate" | Same |

**Decision:** one Toni strategy. The paid classes are the detailed version of the same model, with nothing in them
that contradicts the official videos except the POI choice. That one conflict is tested both ways (variant
`closest` = classes, variant `breaker_first` = official/explainer).

## Part 2: the models made exact (bearish form; bullish = mirror)

Shared: GBP/USD + gold (main), EUR/USD + silver (fresh check, same code). Dukascopy M1, Nov 2021 – Nov 2026,
Exness GMT+0 candles, Ore's spreads (1.0 pip; gold $0.24; silver $0.025), every stop + 2 spreads, scored on
1-minute data (stop first if both hit in a minute). Swings = the engine's 5-bar fractal (known 2 candles later).
**Bias** = engine D1 structure direction (last close beyond a confirmed D1 swing), known before the decision.
Each row is run with and without the bias filter. Limit orders stay valid 20 candles of the trading timeframe.
Hold: H4 10 days, H1 5 days, M15 2 days.

### Toni Iyke (trading TF: H1, M15)
1. **Structure.**
   - **MSS** = the candle where the trading-TF structure turns bearish (first body close below the latest swing
     low while structure was bullish).
   - **Multiple BOS** = within one down leg (reset at every new swing high), the candle whose body close makes the
     count of swing lows broken reach 2.
2. **Inducement.** After the structure candle *j*: the first pullback candle *p* (high above the previous high),
   then the first candle *v* after it that body-closes below *c[j]*. Inducement level *I* = highest high from j+1
   to v. None within 30 candles → no setup.
3. **POI candidates** (formed by the structure leg, from the swing high that started it to *j*):
   - **Breakers** = the body of each swing-low candle the leg broke. Entry = body bottom; stop = that candle's
     high.
   - **OB** = the bullish candle engulfed by the next (bearish) candle, nearest the top of the leg. Entry = its
     low if its lower wick is shorter than its body, else its body bottom; stop = the pair's high.
4. **POI rules.** A candidate is disqualified if any candle from j+1 to v reached its body (mitigated; a wick is
   fine). It must sit above *I*.
   - Variant **closest**: pick the lowest valid entry.
   - Variant **breaker_first**: the closest valid breaker, else the closest valid OB.
5. **Order and targets.** Sell limit placed at the close of v.
   - **Swing** target = lowest low from j to v (the last swing low before the POI triggers).
   - **5R** target (his "smallest ~1:5").

Rows: structure (MSS / multiple BOS) × TF (H1 / M15) × POI rule (closest / breaker_first) × target × bias
(on / off) = 32.

### Lingard (setup TF: H4, H1; standard entry at the POI, no lower-timeframe confirmation)
1. **BOS** = a candle whose low goes below the latest confirmed swing low (wick counts, his rule).
2. **Pattern A.** A swing high (pullback) formed between the broken swing low and the BOS. The **first** such
   pullback high *PH* is the liquidity. Setup known at the BOS candle's close.
3. **Pattern B.** No pullback before the BOS. Then the first swing high after the BOS is the liquidity *PH*, and
   the setup is known when a later candle's low breaks the low made after the BOS ("breaks another low"), within
   30 candles.
4. **POI** = an order block above *PH*: a run of bullish candles followed by a bearish candle, taken from the leg
   that the liquidity sits in (from the leg's starting swing high down to the BOS), marked wick to wick. The one
   nearest *PH* (lowest), with its low within 1.5 ATR(14) of *PH*. Entry = OB low; stop = OB high. None → no setup.
5. **Targets.**
   - **Liquidity** = the lowest low between the BOS and the setup time (next liquidity in his direction).
     **Only kept if reward:risk ≥ 5**, his minimum.
   - **5R**.
6. **Session.** The setup must be known in London or New York hours (he avoids night trading).

Rows: pattern (A / B) × TF (H4 / H1) × target × bias (on / off) = 16.

**Not tested (no objective rule or no data):** Toni's HTF zone/trendline confirmation, the "liquidity pool" and
first-time-reversal filters, and trendline/range targets; Lingard's 3M/1M/W top-down bias, breaker blocks,
inducement/fake zones, the lower-timeframe confirmation entry, and the daily loss limits. These are discretionary
parts. They can be measured through Ore's reviews (My test), not here.

## Part 3: pass rule (unchanged since v7)
A row is **consistent** if it has ≥ 30 trades, average R after spread > 0 in total and in ≥ 4 of 5 years
(2022–2026), and a target hit rate ≥ chance (risk / (risk + reward)).
- A consistent row must then hold unchanged on EUR/USD + silver: positive average, ≥ 3 of 5 years, hit ≥ chance.
- Each family (Toni, Lingard) must pass the walk-forward (spec v7).
- Only a row passing all three is a candidate to add to the site as a live strategy.
- About 5% of rows can look consistent by luck (≈ 2 of 48).

# Spec v31: do breaker blocks make Ore's model better? (pre-registered 28 Nov 2026, before any run)

Ore: "If you can prove breaker blocks make the Ore model perform better, you can add it back."
Live Ore's model (spec v26): D1 trend; the M15 top/bottom forms on the first tap of a fresh **H4 order block or FVG**
(H4 breakers ignored, Ore's rule of 27 Nov); M15 wick-break MSS -> BOS -> liquidity; entry = the **M15 breaker if
valid, else the M15 order block**; pattern within 30 M15 candles of the top; 3R; valid 30 candles; 5-day hold.

## Variants (everything else exactly as live)
1. **H4 breakers back:** the H4 POI may also be a fresh H4 breaker (`engine.smc_poi` type "BB").
2. **Breaker-only entry:** take the trade only when the M15 breaker is valid (no order-block fallback).
3. Both 1 and 2.

## Test and pass rule
Markets: A = GBP/USD + gold, B = EUR/USD + silver, Nov 2021 – Nov 2026, 1-minute scoring, Ore's spreads.
A variant replaces the live rule only if in **both** A and B it has at least 20 trades, averages above 0R, and
averages at least **0.10R above** live **and** makes at least as much total R as live (so it cannot win by trading
much less). Results are appended below; nothing above is edited after the run.

## Results (run 28 Nov 2026, `python -m backtest.ore_breakers_v31`; filled trades, 3R, after spreads)
| Variant | A: GBP/USD + gold | B: EUR/USD + silver | Verdict |
|---|---|---|---|
| Live | +0.322 × 34 = +10.9R | +0.497 × 30 = +14.9R | |
| 1: H4 breakers back | +0.249 × 36 = +8.9R (3 trades from H4 breakers) | +0.449 × 31 = +13.9R (3) | **FAIL** |
| 2: breaker-only entry | +0.880 × 12 = +10.6R | +0.616 × 11 = +6.8R | **FAIL** (too few trades, less total R) |
| 3: both | +0.736 × 13 = +9.6R | +0.616 × 11 = +6.8R | **FAIL** |

H4 breakers add only 2–3 trades per set and they lose, so Ore's 27 Nov rule (ignore H4 breakers) stands. The M15
breaker stays the first-choice entry (as live): per trade it is the best zone, but dropping the order-block fallback
cuts trades by two thirds and the total falls, which also matters for the prop plan (fewer trades = slower challenge).

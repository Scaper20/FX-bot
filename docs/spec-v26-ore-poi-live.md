# Spec v26: Ore's model, live version (Ore's decision, 27 Nov 2026)

Ore: "set it up as its own strategy" and "ignore some POI: a breaker block, if it fails as an order block,
ignore it and look for the next order block ... be selective."

Rules (`engine/smc_models.ore_poi_setups`, HTF zones `engine/smc_poi.py`, shared by backtest and live):
1. **Bias:** D1 external trend.
2. **HTF POI:** a fresh **H4 order block (Ore's 2/3-candle) or H4 FVG** pointing the trade's way. HTF breakers
   (failed OBs) are ignored (Ore). The top (sell) / bottom (buy) of the M15 move forms inside it, on its first tap
   (first touch within 20 M15 candles before the top).
3. **Entry model on M15** (wick breaks, "a break is a break"): MSS → the next event is a BOS the same way → its
   pullback is Liq. Entry zone beyond Liq:
   - the LTF breaker at the swing the MSS broke if valid (the best part of the backtest);
   - else Ore's order block at the top of the move.
4. The pattern must complete within **30 M15 candles** of the top (it should come at the start of the move).
5. **Order:** limit at the zone's near edge, placed at the BOS close, valid 30 M15 candles. Stop beyond the zone
   + 2 spreads; target 3R; closed after 5 days.

Evidence (spec v25 data, D1 trend, 3R; post-hoc selection, so the live record is the real test):
- **All lower timeframes, breakers ignored:** +0.20R over 123 trades on GBP/USD + gold; +0.27R over 137 on
  EUR/USD + silver.
- **M15 alone:** +0.24R (33 trades) and +0.50R (30).

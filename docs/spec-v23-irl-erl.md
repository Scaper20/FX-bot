# Spec v23: IRL → ERL bias for the order-block strategy (pre-registered 27 Nov 2026, before any run)

Ore (27 Nov): "The market always moves from an internal range liquidity to an external range liquidity ... once
it takes the internal range liquidity, everything is going to go to the external range liquidity. External
range liquidity are always the extremes ... internal range liquidity are mostly ... fair value gaps. Do your
research and implement." For the H1 order block + D1/H4 bias strategy.

## The concept made exact (ICT "price delivery from ERL to IRL and back")
On a higher timeframe (**H4**; variant **D1**):
- **Dealing range** = the external range from `engine/smc_structure.external_structure` (close breaks): the
  external high (fixed, or the running leg high) and the external / protected low, known at each candle's
  close (`dealing_range`).
- **ERL (external range liquidity)** = the stops beyond the range high (buy-side) and the range low (sell-side).
  "Taken" = a candle trades beyond the previous candle's range high or low (a wick counts).
- **IRL (internal range liquidity)** = unfilled fair value gaps inside the range. A bullish FVG is candles
  x, x+1, x+2 with low[x+2] > high[x]. "Reached" = a later candle trades into it. A gap is used up once
  traded into.
- **Bias** = the last liquidity event (`irl_erl_bias`). If both happen on one candle, ERL counts first.

| Last event | Bias | Next draw |
|---|---|---|
| took the range high (buy-side ERL) | **sell** | IRL below |
| took the range low (sell-side ERL) | **buy** | IRL above |
| traded into a bullish FVG (IRL) | **buy** | ERL high |
| traded into a bearish FVG (IRL) | **sell** | ERL low |

## Test
The order-block strategy exactly as live (v22: H1 MSS, Ore's 2/3-candle block at the top/bottom of the move,
limit at the first candle's near edge, stop beyond + 2 spreads, 3R, 12-candle validity, 5-day hold).

Bias variants:
1. **IRL/ERL on H4**
2. **IRL/ERL on D1**
3. **IRL/ERL on H4 and D1 agreeing**
4. **D1 + H4 trend (current live rule)**
5. **IRL/ERL H4 + D1 trend agreeing**
6. **none**

Markets: GBP/USD + gold (main), EUR/USD + silver (fresh check). Nov 2021 – Nov 2026, Ore's spreads,
1-minute scoring.

Also reported for information: market entry at the MSS close with the same bias variants. That is many more
trades, so it shows whether the bias itself points the right way.

## Pass rule (unchanged)
A row is **consistent** if:
- it has ≥ 30 trades;
- its average R after spread is > 0 overall and in ≥ 4 of 5 years;
- its target hit rate is ≥ 25% chance.

A consistent row must then hold on EUR/USD + silver. The IRL/ERL family must pass the walk-forward.

Only then does IRL/ERL replace the live D1+H4 trend bias. If it does not pass, it is still added to the setup
card as information (the current IRL/ERL state and the next draw), so Ore can judge it live.

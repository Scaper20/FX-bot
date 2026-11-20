# Why the strategy loses: diagnosis (Design data, Nov 2021 – Dec 2023)

Scripts: `backtest/diagnose.py`. No costs unless stated. 1-minute data.

## The test
If the CRT idea works, then after a sweep that closes back inside, price should reach the 50% level or the opposite side **before** it takes out the sweep extreme more often than chance.
On a random price path, the chance of reaching a target before the stop is exactly `risk / (risk + reward)`. Random entries with the same stop and target distances confirm the formula is accurate on this data.

## 1. The CRT pattern itself carries no information
2,550 CRTs (both pairs, D1 and H4 ranges, sweep on the next or second candle, both directions). Entry at the sweep candle's close, stop at the sweep extreme:

| Target, within 5 range candles | Reached first | Chance (formula) | Chance (random entries) |
|---|---|---|---|
| 50% level | 57.9% | 57.0% | ≈ same |
| Opposite side of the range | 41.8% | 41.7% | ≈ same |
| 1R / 2R / 3R | 51.8% / ~32% / ~22% | 50% / 33% / 25% | ≈ same |

Split by pair and timeframe, session, daily direction (both definitions), how deep the close is inside the range, sweep depth, sweep candle size, reward-to-risk, sweep on candle 1 or 2, long or short: **every one of about 40 groups is within ±3 points of chance**, apart from tiny groups (for example 51 setups with no clear trend), which is what luck looks like across 40 tries.

## 2. Entering during the sweep does not help either
Entering inside the sweep candle at the first lower-timeframe CISD that closes back inside the range ("turtle soup" timing), stop at the highest point so far: 7,677 entries, again **at or slightly below chance** for every pair and timeframe (to 3R: 21–26% vs 25%). After a sweep, price is if anything slightly more likely to keep going than to reverse.

## 3. Where the losses come from
With no edge, each trade's expected result is minus its costs, and the rules then add some damage of their own:
1. **Spread.** On M5 with tight stops, the spread is about half the risk (GBPUSD) or 80% (gold). Every trade pays it.
2. **The 1:3 rule picks the weakest CRTs.** Only 25% of CRTs offer 1:3 from the sweep close to the opposite side. Those are the ones that closed right at the swept edge (median close 8% into the range vs 31% for the rest) with tiny sweeps (0.08 vs 0.23 daily ATR).
3. **Limit entries (FVG / order block) miss the moves that work.** Of limit orders: 41% never filled, 24% were cancelled because price ran to the 50% level without coming back, and the fills that did happen were the ones where price came back towards the stop.
4. **Filters and confluences reshuffle stop and target distances, not edge.** That is why the Design winners failed in 2024.

## What this means
- The losses do not come from a wrong setting. As a mechanical rule, a sweep and close back inside on D1/H4 does not predict direction on GBP/USD or gold in 2021–2023.
- If Ore's trading has an edge, it is in what he sees that these rules do not capture. The journal measures exactly that, using the same chance formula as the benchmark for every trade.

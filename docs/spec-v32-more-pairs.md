# Spec v32: do more pairs help the prop plan? (written 27 Nov 2026, before the prop simulation was run)

Ore's question: "Does adding more pairs to trade like the EURUSD and silver help to have more trades... also check if
we can handle it."

## What is already known (so this is not a blind test)
The live-scanner replay (`backtest/replay_live.py --pairs EURUSD,XAGUSD --only ore_poi,irl_erl`, 1 Jun 2022 to
18 Nov 2026) was run before this spec was written. Its trade totals:

| pair | Ore's model | IRL/ERL |
|---|---|---|
| EUR/USD | 19 trades, +1.0R | 13 trades, +3.0R |
| silver | 8 trades, +12.0R | 16 trades, -4.0R |

The prop simulation below has **not** been run yet. Its rule is fixed here first.

## Test
- **Trades:** the prop plan, Ore's model + IRL/ERL, from the live-scanner replays.
  - GBP/USD + gold: `replay_2022_24.csv` + `replay_2025_26.csv`.
  - New pairs: their own replay.
  - Common window: 1 Jun 2022 to 18 Nov 2026.
- **Simulator:** `backtest/prop_sim.py`, with Equity Edge Swift rules and each pair's leverage:
  - 1:30 for FX, 1:10 for metals.
  - USD/JPY pays in yen, converted at the price.
- **Baskets:**
  - A = GBP/USD + gold (today's plan).
  - A + EUR/USD.
  - A + silver.
  - A + EUR/USD + silver.
  - Later, the same with USD/JPY and AUD/USD once their data is in.
- **Risk:** 1%, 1.5% and 2%.
- **Measures:**
  - Pass rate over challenges started every Monday (6-month horizon).
  - Week-block bootstrap pass rate (2,000 paths, 26 weeks).
  - Median days to pass.
  - Funded-stage average payout (6 months, payouts every 14 days).

## Adoption rule (per pair, whole pair, both strategies; no picking one strategy on one pair)
A pair is added to the prop plan only if all three hold:
1. Its own plan trades are net positive after spread over the window.
2. At 1.5% risk, A + that pair has a pass rate at least 3 points above A, and the bootstrap pass rate is not lower.
3. The funded average payout is not lower than A's.

If a pair passes, the live feed must also carry it inside the free Twelve Data limits (two keys, 800 credits a day
each). This is checked separately and reported. Passing here does not by itself put the pair live.

## Results
(appended after the run)

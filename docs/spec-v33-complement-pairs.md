# Spec v33: two more pairs to go with EUR/USD and silver (written 28 Nov 2026, before any candidate was replayed)

## Ore's decision (28 Nov 2026)
Add EUR/USD and silver to the scanner **and** to the prop plan, against the spec v32 verdict. With both added, v32
measured:
- Pass rate 33.8% (31.9% without them).
- Funded breaches 84% (50% without them).
- Silver alone lowered the pass rate to 21.1%.

Ore was shown these numbers before deciding. Then: "look for another maybe 2 pairs to complement it".

## Candidates (fixed now)
GBP/JPY, EUR/JPY, USD/CAD, USD/CHF, NZD/USD, EUR/GBP, and platinum (XPT/USD) if the Twelve Data free plan carries it.
- Chosen because Equity Edge lists FX majors, FX crosses and metals.
- Indices and oil need a paid Twelve Data plan (v32).
- USD/JPY and AUD/USD already failed in v32 and are not retried.

## Data and costs
- 5-minute Twelve Data history from 1 Nov 2021 (mid prices), `data/td/`.
- Assumed spreads, Ore's choice to assume ("Use your assumptions"); to be replaced by his real spreads later:

| pair | spread |
|---|---|
| USD/CAD, USD/CHF, NZD/USD, EUR/GBP | 1.5 pips |
| EUR/JPY | 2.0 pips |
| GBP/JPY | 2.5 pips |
| platinum | $2.00 |

- Leverage: 1:30 FX, 1:10 platinum.
- Contract: 100,000 FX; 100 oz platinum (assumed).
- Prop-sim conversions for crosses use fixed rates: USD/JPY 150, EUR/USD 1.10, GBP/USD 1.30. These only affect the
  leverage cap; profit and loss are in R times the dollar risk.

## Test
- **Replay:** the live scanner (`backtest/replay_live.py --only ore_poi,irl_erl`), 1 Jun 2022 to 18 Nov 2026, as in
  v32.
- **Simulator:** `backtest/prop_sim.py`, 1.5% risk.
- **Baseline B:** GBP/USD + gold + EUR/USD + silver (the new plan).
- **Measured:** pass rate over challenges started every Monday (6 months) and the funded average payout.

## Selection rule
1. A candidate qualifies only if its own plan trades are net positive after its spread.
2. It must also leave neither the pass rate nor the funded payout lower than B's, when B + that candidate is run.
3. Of the qualifying candidates, the two-pair combination (B + X + Y) with the highest pass rate is chosen, if it too
   keeps the pass rate and funded payout at or above B's. Otherwise the single best qualifying pair is chosen.
4. If nothing qualifies, nothing is added and Ore is told.

## Warning, stated before the run
Each pair gives about 25–35 plan trades in 4.5 years. Picking the best 2 of up to 7 by backtest will partly pick luck,
so the live record is the real test.

## Amendment (28 Nov 2026, before any candidate was replayed)
Twelve Data answered XAG/USD with "This symbol is available starting with the Grow or Venture plan". Silver can't
be scanned live on the free plan; EUR/USD can.

- Every result is reported against both baselines:
  - **B**: GBP/USD + gold + EUR/USD + silver, as fixed above.
  - **B'**: GBP/USD + gold + EUR/USD, what can run live today.
- The selection rule is applied to each baseline. If they disagree, Ore is shown both.
- A candidate the free plan does not carry is reported but marked "needs a paid plan".

## Results
(appended after the run)

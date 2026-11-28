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

## Results (run 28 Nov 2026, `backtest/complement_v33.py`, 1.5% risk)
Platinum: Twelve Data answered "not found" for XPT/USD, so it was not tested. EUR/GBP gave 18 plan trades.

**Each candidate's own plan trades (after the assumed spread)**

| Pair | Trades | Net R | Rule 1 |
|---|---|---|---|
| GBP/JPY | 24 | −20.9 | fails |
| EUR/JPY | 27 | −3.0 | fails |
| USD/CAD | 34 | −17.3 | fails |
| USD/CHF | 29 | +11.5 | passes |
| NZD/USD | 24 | −2.5 | fails |
| EUR/GBP | 18 | −4.7 | fails |

**Prop pass rate and funded payout**

| Basket | Pass | Funded avg paid | Failed on trailing limit |
|---|---|---|---|
| B (GBP/USD, gold, EUR/USD, silver) | 33.8% | $165.0 | 45.6% |
| B + USD/CHF | 24.5% | $101.4 | 56.4% |
| B + EUR/JPY | 28.4% | $158.8 | 55.4% |
| B + GBP/JPY | 27.5% | $132.5 | 53.9% |
| B + USD/CAD | 23.8% | $103.1 | 57.3% |
| B + EUR/GBP | 20.6% | $149.5 | 52.9% |
| B + NZD/USD | 20.1% | $102.2 | 64.2% |
| B' (GBP/USD, gold, EUR/USD) | 36.3% | $165.6 | 35.3% |
| B' + USD/CHF | 25.5% | $126.4 | 45.6% |
| B' + EUR/JPY | 26.5% | $145.5 | 44.1% |
| B' + GBP/JPY | 25.5% | $126.2 | 56.4% |
| B' + USD/CAD | 20.9% | $103.4 | 51.0% |
| B' + EUR/GBP | 20.6% | $150.2 | 44.6% |
| B' + NZD/USD | 18.6% | $117.6 | 51.5% |

## Verdict
**Nothing qualifies against either baseline, so nothing is added (rule 4).** B and B' agree.
- Only USD/CHF is net positive on its own (+11.5R over 29 trades). Adding it still lowers the pass rate by about
  10 points and the funded payout, against both B and B'. More challenges end on the trailing limit (45.6% to 56.4%
  against B).
- Every other candidate loses money on its own.
- With 18–34 trades a pair, none of these numbers is precise; the verdict is what the pre-registered rule gives.

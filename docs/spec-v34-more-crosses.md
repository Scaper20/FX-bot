# Spec v34: 13 more pairs for the prop plan (pre-registered 28 Nov 2026)

## Why
Ore, 28 Nov 2026: "add USDCHF to it either ways, then check AUDJPY GBPCHF GBPNZD GBPAUD AUDCHF NZDCHF GBPCAD
CADJPY CADCHF EURCAD EURNZD AUDCAD BTCUSD."

USD/CHF is now live (engine v2.1) even though spec v33 did not select it. This spec tests the 13 new pairs the same
way as v33.

## Candidates and assumed spreads
Spreads are my assumptions (Ore chose "use your assumptions" in v33) until he gives his real ones.

| Pair | Spread |
|---|---|
| AUD/JPY, CAD/JPY | 2.0 pips |
| AUD/CHF, AUD/CAD | 2.0 pips |
| GBP/CHF, GBP/AUD, NZD/CHF, CAD/CHF, EUR/CAD | 2.5 pips |
| GBP/CAD | 3.0 pips |
| GBP/NZD, EUR/NZD | 3.5 pips |
| BTC/USD | $30 (1 BTC contract) |

## Data
- **Source:** Twelve Data 5-minute history, 1 Nov 2021 onward (`scripts/fetch_twelvedata_history.py`, mid prices).
- **Weekends:** weekend candles are dropped, as in the live feed.
- **BTC/USD:** the scanner only runs Sunday 17:00 to Friday 17:00 New York, so BTC is tested on weekdays only, like it
  would be scanned.
- **Pairs not available:** a pair the free plan doesn't carry is reported as "needs a paid plan" and not tested.

## Test (as v33)
- **Replay:** the live scanner (`backtest/replay_live.py --only ore_poi,irl_erl`), 1 Jun 2022 to 18 Nov 2026.
- **Simulator:** `backtest/prop_sim.py` at 1.5% risk, using `backtest/complement_v33.py --spec v34`.
- **Leverage cap:**
  - FX crosses: 1:30, priced with fixed rates (AUD 0.65, NZD 0.59, CAD 0.72, CHF 1.13, JPY 1/150 USD).
  - BTC/USD: 1:2, assumed (unverified crypto leverage for Equity Edge; Ore to confirm).
- **Baselines:**
  - **C:** GBP/USD + gold + EUR/USD + USD/CHF (what runs live now).
  - **C+silver:** C plus silver (paid plan only).

## Selection rule (same as v33)
1. A candidate qualifies only if its own plan trades are net positive after its spread.
2. Baseline + the candidate must have a pass rate and a funded payout both at or above the baseline's.
3. Of the qualifying candidates, the two-pair combination with the highest pass rate is chosen, if it also meets
   rule 2. Otherwise the single best qualifying pair is chosen.
4. If nothing qualifies, nothing is added and Ore is told.

The rule is applied to C and to C+silver. If they disagree, Ore is shown both.

## Warning, stated before the run
- **Few trades:** each pair gives about 20–35 plan trades in 4.5 years.
- **Many tries:** with v32 and v33 this is now 21 pairs tried for the same plan. The best of 13 will partly be luck.
- **The real test:** a pair that "qualifies" here still has to prove itself live.

## Results
(appended after the run)

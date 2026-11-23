# Spec v12 result: C2 must close inside C1's body (Ore's correction), full retest (run 23 Nov 2026)

Spec: `docs/spec-v12-body-close.md` (committed before any run). One shared rule now (`engine/structure.py: crt_inside`), used by the live scanner and every backtest; `CRT_CLOSE=range` reproduces the old tests. Costs: Ore's spreads (GBP/USD 1.0 pip, gold $0.24). Old (range-rule) outputs kept in `backtest/out/range_rule/`.

**How much changed:** 219 of the 400 old practice setups (55%) closed inside C1's wick only. They're retired from practice (answers kept for stats). On all CRTs 2021–2026: 6,088 with the old rule → 2,810 with the body rule.

## 1. Premise (entry at C2's close, stop beyond the sweep, Exness candles)
| Rule | Setups | 50% reached | Chance | Far side reached | Chance | Avg R | Years + |
|---|---|---|---|---|---|---|---|
| **Body (Ore)** | 2,810 | 67.9% | 66.2% (z +1.8) | 45.1% | 45.8% | −0.04 | 2 of 5 |
| Old range | 6,088 | 59.0% | 58.4% | 41.3% | 42.2% | −0.05 | 0 of 5 |
| Removed (wick-only closes) | 3,278 | 51.8% | 52.1% | 38.0% | 39.2% | −0.07 | 0 of 5 |
The body rule keeps the better half: the 50% level is reached slightly more often than chance (z 1.8, gold H4 z 2.3), the far side still at chance; after spread about zero.

## 2. Models and walk-forward
- **Romeo models (v4):** all 9 negative after spread (−0.04 to −0.42R), none consistent.
- **Breakers (v6/v6b):** 0 of 84 rows consistent; walk-forward 1 of 4 blind years.
- **Breakers with filters (v8/v9):** Ore's v1.2 filters all negative; Romeo's 3 strict filters: 78 trades in 5 years. Loose Romeo + MSnR (the v9 candidate) again 3 "consistent" H4 rows (+0.19 to +0.28R) but only 33–44 trades; **frozen and rerun on EUR/USD + silver: −0.17 to −0.20R → fails again.**
- **Walk-forward (v7 rule), blind 2023–2026:** v1.2 engine −0.13R (2 of 4 years), Romeo v2 −0.20R (0/4), search + SMT −0.30R (1/4), v4 models −0.09R (1/4), breakers −0.15R (1/4). All fail. (Edge hunt is not a CRT test; its rollover-artifact pass is unchanged.)
- **Market entry (v11):** all setups +0.02 / +0.08R (3 of 5 years); with Ore's rules −0.41 / −0.24R.

## 3. One candidate: limit at the FVG, with Ore's rules (spec v12b)
With Ore's rules, stop = sweep + 2 spreads, half at 50% then the far side, one trade per setup:
| | GBP/USD + gold (where found) | EUR/USD + silver (never used) |
|---|---|---|
| **E3, limit at FVG middle** | +0.22R, 116 setups, 5 of 5 years, t 1.4 | **+0.17R, 71 setups, 3 of 5 years, t 0.8**, both markets positive |
| E2, limit at FVG edge | +0.31R, 86 setups, 4 of 5 years, t 1.7 | +0.21R, 62 setups, 3 of 5 years |
**Pre-registered rule: FAIL**, on one criterion: the far target was hit less often than chance (14% vs 20%). That criterion suits "all out at the far side" badly (moving the stop to entry after 50% cuts some trades before the far side), but it was the rule set in advance, so it stands. The other three criteria passed. Evidence is weak (t 0.8 on new markets); it is the most consistent result in the project, not a proven edge.

**Bottom line:** with the correct CRT definition the picture is the same: no fixed rule shows a reliable edge after spread. The FVG-middle limit with Ore's rules is the one pattern worth watching in the live log.

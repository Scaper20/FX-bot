# Spec v12: C2 must close inside C1's BODY (Ore's correction), and a full retest (pre-registered 23 Nov 2026, before any result)

**Ore's rule (23 Nov 2026):** a CRT needs C2 to **sweep** C1 (trade beyond C1's high for a sell, its low for a buy) and then **close inside C1's body**: between C1's open and close, not merely inside C1's high–low range. Until now every test and the live scanner accepted any close inside the full range: 219 of the 400 practice setups (55%) break the corrected rule.

Unchanged: the sweep is beyond C1's **wick** (high/low); C2 must not break the other side; for a 2-candle setup the middle candle stays inside C1's range; targets stay 50% of C1's full range and C1's far side; stops beyond the sweep extreme.

**Costs:** Ore's real Exness spreads (23 Nov 2026, London session): GBP/USD 1.0 pip, gold $0.24 (was assumed $0.35).

**One shared rule** (`engine/structure.py: crt_close_ok`) used by the live scanner and every backtest script; `CRT_CLOSE=range` reproduces the old results.

## Retested (all years Nov 2021 – Nov 2026, same scoring as before)
1. **Premise:** CRTs on Exness candles (GMT+0), entry at C2's close, stop beyond the sweep: does price reach 50% / the far side more often than chance? Body rule vs old range rule side by side.
2. **v1.2 engine** (CRT + ICT triggers + entries, Ore's rules) on all periods → yearly results and the **walk-forward** (spec v7 rule).
3. **v4 Romeo models** (Model #1, RTM1, OTE, KOD, fake MSS, rejection block, MSnR full, mixing).
4. **Breakers in a CRT** with no filter, Ore's v1.2 filters, Romeo's 3 filters (strict and loose), each ± MSnR (specs v8/v9), including the v9 candidate (loose + MSnR, H4, classic stop).
5. **Romeo v2 and the combination search + SMT** through the walk-forward.

**Judged by the earlier rules:** a model/row is consistent with 30+ trades, positive in 4 of 5 years (2022–2026) and in total; a family passes the walk-forward with positive blind results in 3 of 4 test years. Any pass must also beat chance on target hits. With this many rows, one or two lucky passes are expected, so a pass is a lead to check on EUR/USD + silver (as v10), not a result.

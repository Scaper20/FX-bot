# Spec v1.3: assisted mode (20 Nov 2026)

Based on `backtest/reports/diagnosis.md`. The system **recommends**; Ore decides. Nothing here claims an edge.

## What the scanner shows
A setup = one CRT: a range candle (D1 or H4) and a sweep on the next or second candle that closed back inside (v1.1 definitions). It becomes **ready** when a lower-timeframe trigger (CISD or MSS) has fired. It is **armed** while it waits for the trigger.

**Recommended** (top list) only if all of Ore's rules hold:
1. Trigger in the London (07:00–16:00 London) or New York (08:00–17:00 New York) session, not Friday from 15:00 New York.
2. With the daily direction (swing-break definition), **or**, if against it or unclear, the sweep ran into an older higher-timeframe order block or FVG on the left.
3. At least one entry option reaches 1:3 after spread.

CRTs that fail a rule are still listed in a collapsed "filtered out" section with the reason, so Ore can see what the rules removed.

Shown as checklist items, not filters (no evidence either way): sweep candle bigger than the range candle (Ore's chart 3 concern), sweep depth, ICT confluences (FVG, OB, killzone, CISD + MSS), HTF MSS, MSnR level.

## Entry options
Entries E1–E5 as in v1.1. Stops:
- **S1p, the default:** sweep extreme + 2 spreads.
- **S1a:** sweep extreme + 0.1 × entry-TF ATR.
- **S2, tight:** shown only if the spread is under 15% of the risk.

Targets: half off at the 50% level then the opposite side (M2_T2), or full to the opposite side (M1_T2), or to the next swing beyond it (T3). Only options at 1:3 or better are listed (Ore's rule).

For every option the card shows:
- entry, stop, target, reward:risk after spread, and lot size from Ore's balance and risk %;
- the **win rate needed to break even** after spread, and the **chance win rate** `risk / (risk + reward)`;
- the historical result of that exact option, 2021–2024, with Ore's rules applied: number of trades, win rate, average R. Options are ranked by it (Ore's answer to Q17). Fewer than 30 trades shows "too few to rank".

## Measuring Ore's judgment (the real test)
- Every ready setup is logged the first time it is shown, before the outcome is known, then scored automatically on later candles: filled or not, stop or target, R.
- Ore records take / skip / unsure, the option, reasons and notes. Optionally he adds the real fill and result.
- **Practice mode:** about 400 past setups (Nov 2021 – Dec 2024, Ore's rules applied) shown only up to the moment of decision. Ore reviews them blind, then the outcome is revealed. This builds a large sample of his judgment quickly. 2025–2026 is never used here.
- The Performance page compares, for live and practice separately, Ore's "take" picks, his "skips" and all recommended setups. Each trade is measured against its own chance win rate: hits, expected hits by chance, the difference, a z-score, and average R after spread.

## Unchanged
- 2025–2026 stays untouched until a candidate rule set has earned a one-time Final test.
- Data: live candles from Twelve Data (H1, M15, M5); D1 and H4 are built from H1 with the Exness GMT+0 day. Twelve Data prices can differ slightly from Exness; the site says so.

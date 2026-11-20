# Spec v1.2: Ore's chart feedback + Claude's next tests (written 20 Nov 2026, BEFORE any v1.2 result)

Everything in v1.1 stays unless changed here.

## New rules from Ore's chart review (always on)
| Rule | Definition |
|---|---|
| Sessions | Entry decision must be in London (07:00–16:00 London time) or New York (08:00–17:00 New York time); the overlap is when both are open. Daylight saving handled |
| Market direction | A trade **with** the daily direction is allowed. A trade **against** it (a reversal), or when the direction is unclear, is allowed **only if** the sweep runs into an older higher-timeframe order block or FVG on the left (the `htf_ob` / `htf_fvg` checks) |
| Weekend | No entry decision on Friday from 15:00 New York time |

## Options tested
| Option | Choices |
|---|---|
| Daily direction | `struct`: last daily close beyond a confirmed swing high (up) or swing low (down). `ema`: daily close above a rising 20-day average (up) or below a falling one (down) |
| Session subset | all three · London + overlap · New York + overlap · overlap only |
| Sweep size (Ore: "sweeping candle too large") | none · sweep candle no bigger than the range candle (`ratio ≤ 1`) · sweep at least 0.1 range-TF ATR beyond the range (`depth ≥ 0.1`) · both |
| Stop (Ore: "optimal for spread") | S1 sweep extreme · S1p sweep extreme + 2 spreads · S1a sweep extreme + 0.1 entry-TF ATR · S2 tight. Each with or without a minimum risk of 10 spreads |
| Kept from v1.1 | pair, range/entry timeframe, trigger (CISD/MSS), entry E1–E5, management M1_T1…M2_T3. Expiry fixed at 2 candles; sweep candle 1 and 2 both allowed |

## How the winner is chosen (fixed now)
**Stage A, filters (Design data, pooled):** for each pair, pick the one combination of daily direction × session subset × sweep size with the highest average R over all its trades, among combinations with ≥ 300 trades. Pooling over all entries/stops/targets keeps samples large and luck small.

**Stage B, variants (Design data):** inside that filter, a variant (timeframes × trigger × entry × stop+min-risk × management) qualifies if it has ≥ 40 trades, average R > 0 after costs **and** > 0 at double cost. Finalists = the top 10 per pair by t-score. The number of variants tried is reported.

**Stage C, Check (2024, run once):** a finalist passes if it has ≥ 20 trades in 2024 and average R > 0 after costs. Expected by luck alone if nothing works: about half of finalists positive, so the report also states how far results beat that.

Thresholds were lowered from v1 (60/25 to 40/20) because the new filters remove most setups; this was decided before seeing v1.2 numbers.

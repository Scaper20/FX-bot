# Spec v30: Ore's PD array priority order inside the strategies (pre-registered 28 Nov 2026, before any run)

Ore: "The PD array is not a strategy on its own. It tells you the priorities: order block is above the fair value
gap, so you prioritise order blocks over fair value gaps. Test the strategies according to the PD array, e.g. Ore's
model and IRL/ERL." His order, from the extreme of the range to equilibrium:
1. old highs / lows (liquidity) · 2. rejection block · 3. order block · 4. fair value gap / liquidity void ·
5. breaker block · 6. mitigation block.

## How it is applied
For every setup the strategy finds (same rules as live: Ore's model = D1 trend, first tap of a fresh H4 OB or FVG,
M15 MSS → BOS → liquidity, pattern within 30 candles; IRL/ERL = H4 IRL/ERL draw + D1 trend, H1 MSS), the candidate
entry zones on the move are built (sell shown; buys mirrored):
- **Rejection block (RB):** the extreme candle of the move (its top) if its upper wick is at least 50% of the candle's
  range and at least 0.5 × ATR(14). Zone = body top to the high. (Conventions vary; this is the LuxAlgo-style one.)
- **Order block (OB):** Ore's 2/3-candle block at the top (as live).
- **Fair value gap (FVG):** the first bearish three-candle gap in the move from the top to the decision candle.
- **Breaker (BB):** Ore's model only: Ore's opposite block at the swing the MSS broke (as live).
- Old highs/lows are the liquidity the move must take (already a condition of Ore's model), not an entry zone.
  Mitigation blocks wait for an agreed definition.

Entry = the zone's near edge (limit, placed at the decision candle's close, same validity as live). Stop = beyond the
move's extreme + 2 spreads for RB / OB / FVG; the breaker keeps its own far edge (as live). Target 3R, closed after 5
days. Ore's model also needs the entry beyond the liquidity level and ahead of price; every zone must be ahead of price.

## Variants compared
- **Live:** Ore's model = breaker if valid, else OB; IRL/ERL = OB.
- **PD priority:** the highest-priority zone that exists: RB → OB → FVG → BB.
- **Each zone alone** (only setups that have it).
- **PD priority + premium/discount:** the chosen zone's entry must be in premium (sell) / discount (buy) of the H4
  dealing range (spec v28 definition).

## Test sets and pass rule
- A: GBP/USD + gold, all years (Nov 2021 – Nov 2026). B: EUR/USD + silver, all years. 1-minute scoring, Ore's spreads.
- **Pass (switch a strategy to the PD priority order):** in both A and B, PD priority averages above 0R with at least
  20 trades and at least 0.10R above the live version.
Results are appended below; nothing above is edited after the runs.

## Results (run 28 Nov 2026, `python -m backtest.pd_array_v30 PAIR` then no args; filled trades, 3R, after spreads)
The live versions reproduce their earlier tests exactly (Ore's model 34 / +0.32R and 30 / +0.50R; IRL/ERL 24 / +0.46R
and 32 / +0.10R), so the setups are the same ones.

| Strategy · variant | A: GBP/USD + gold | B: EUR/USD + silver |
|---|---|---|
| Ore's model · live (breaker, else OB) | +0.322 (34) | +0.497 (30) |
| Ore's model · **PD priority** (RB → OB → FVG → BB) | +0.125 (27) | +0.536 (25) |
| Ore's model · PD + premium/discount | +0.107 (13) | +0.813 (11) |
| Ore's model · RB / OB / FVG / BB alone | +0.33 (9) / +0.06 (25) / +0.38 (25) / **+0.88 (12)** | −0.22 (10) / +0.29 (21) / +0.21 (22) / **+0.62 (11)** |
| IRL/ERL · live (OB) | +0.459 (24) | +0.095 (32) |
| IRL/ERL · **PD priority** | +0.243 (22) | +0.070 (26) |
| IRL/ERL · PD + premium/discount | +0.439 (19) | −0.056 (21) |
| IRL/ERL · RB / FVG alone | +1.67 (3) / +0.11 (24) | −1.00 (5) / +0.46 (21) |

**Verdict: FAIL for both; no live change.** Taking the highest-priority zone lowers Ore's model on GBP/USD + gold
(+0.32 → +0.13R) and IRL/ERL on both sets. Inside Ore's model the breaker, the lowest entry on Ore's list, is the best
zone in both sets, and the order block the weakest: these lower zones sit deeper in the move, so the stop is tighter
and only the deeper pullbacks fill. Rejection blocks are rare at the move's extreme (3-10 per set) and mixed.
Samples are small (10-35 trades per cell); read as "no evidence that the priority order helps here", not as proof
that it hurts.

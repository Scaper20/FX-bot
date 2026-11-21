# Spec v11: instant market entry vs limit orders on the same setups (pre-registered 21 Nov 2026, before any result)

Ore's observation: many practice setups were cancelled because price ran to the 50% level before the limit filled. Question: **would entering at market immediately, when the setup forms, do better?**

Data: the v1.2 engine's trade logs (`backtest.run`, design + check + final = Nov 2021 – Nov 2026, both pairs). **E1 = market at the trigger candle's close** (the moment the setup is complete); E2–E5 = limits at the FVG edge/middle and order-block open/middle. Every setup was simulated with every entry, so they can be compared on the same setups. Spread included. Script: `backtest/market_entry.py`.

**Compared, same stop and management on both sides:**
1. **All setups:** E1 vs each limit entry, average R after spread, per year and in total.
2. **The cancelled ones:** setups where a limit did **not** fill. What E1 made on exactly those setups (Ore's question), and on the setups where the limit **did** fill (E1 vs the limit there).
3. **With Ore's rules** (London/NY session, not Friday late, with the daily direction or an HTF order block/FVG on the left): the same comparisons.
Reported for the default stop (sweep extreme + 2 spreads) and both main managements (all out at the opposite side; half at 50% then the rest), plus target hit rate vs chance for E1.

**Market entry "works"** if E1's average R after spread is > 0 in total **and** in at least 4 of 5 years (2022–2026), for all setups or Ore's-rules setups, on at least 100 trades.

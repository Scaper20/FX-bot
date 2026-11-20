# Spec v4: Romeo's discretionary models, full MSnR, mixing; all years (20 Nov 2026)

Ore's decision (20 Nov 2026): test on **all years** (Nov 2021 – Nov 2026), "move forward rather than gatekeep". So no unseen data remains after this; the evidence is **year-by-year consistency**. Script: `backtest/advanced.py`.

Context for every model: a CRT on the New York clock (D1 → M15 entries, H4 → M5 entries). C2 swept C1's high (bearish case; bullish is the mirror) and closed back inside. Entries only **after C2 has closed**, until C3 closes. Outcomes on 1-minute data, spread included. Target 1 = 50% of C1, Target 2 = C1's far side.

| Model | Coded as (bearish) | Stop | Target |
|---|---|---|---|
| **M1** (Model #1, control) | Thick up-close candle makes the high; a later candle closes below its open | above the high | T1 / T2 |
| **RTM1** | After the Model #1 trigger, price comes back up to the Model #1 candle's open: sell there (limit) | above the Model #1 candle's high | T1 / T2 |
| **OTE / failure swing** | True MSS: close below the swing low that formed before the high. Leg 1 = drop from the high to its lowest point. Sell when price retraces to 50% of leg 1 (zone 0.5–0.79) | above the high | T1 / T2 |
| **Kiss of Death** | Price has reached 50% of C1 and bounced. A later push takes a minor swing high formed after that touch, then a Model #1 trigger: sell | above the KOD high | T2 (C1's far side) |
| **Fake MSS (fade)** | After reaching the lower half of C1, a bearish MSS prints in the lowest 25% of C1 (a "discount"): buy it (Romeo: a bearish MSS at a discount is a bullish turtle soup) | below the lowest low of the last 5 entry candles | back to 50% of C1 |
| **Rejection block** | Turtle soup of the **bodies**: C2's high goes above C1's body top (not its wick high) and C2 closes back below that body top. Sell at C2's close | above C2's high | C1 body middle / body bottom |
| **MSnR full** | Storyline = direction of the last close-break of an A- or V-level on the higher timeframe (W1 for D1, D1 for H4); trade only with it. The sweep must reach a fresh A-level (A, V and gap levels from closes; fresh until a wick touches; a body close through refreshes). Entry at C2's close | above C2's high | next fresh V-level below (else T2) |

**Mixing:**
- **2+ agree:** a CRT is traded only when at least two different models have triggered. Entry happens at the moment the second one triggers, using that model's levels (no knowledge of the future).
- **Portfolio:** all models' trades together, equally weighted.

**Reported per year (2021 Nov–Dec, 2022, 2023, 2024, 2025, 2026 to 19 Nov):** trades, Target 1/2 hit rate vs chance (z), average R after spread (half off at 50%, stop to entry), total R. A model is called **consistent** only if its average R after spread is positive in at least 4 of the 5 full or near-full years (2022–2026) **and** positive in total.

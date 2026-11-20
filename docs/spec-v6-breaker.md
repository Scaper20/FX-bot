# Spec v6: breaker blocks (pre-registered 20 Nov 2026, before any result)

Ore asked to test ICT breaker blocks. All years (Nov 2021 – Nov 2026) are already used, so a good result here is a **lead to confirm on the live log**, not proof. Script: `backtest/breaker.py`. Same scoring as v4: 1-minute outcomes, spread included, stop counts first when both are hit in a minute; GBP/USD and gold.

## Definition (bearish; bullish is the mirror)
On the entry timeframe, with swings confirmed by 2 candles each side (known only 2 candles later, no look-ahead):
1. A swing low **SL** forms, after a swing high **SH**.
2. Price then trades **above SH** (the liquidity grab / higher high). **Top** = the highest high since.
3. A candle **closes below SL** (market structure shift). The leg from SL to Top is now broken.
4. **Breaker** = the last down-close candle (close < open) from the candle that made SL back to SH. If there is none, no trade.
5. **Entry:** sell limit at the breaker's **low** (first touch when price comes back up), valid for 20 entry candles after the shift. Cancelled if Top is exceeded first (the limit is then never placed).
6. **Stop:** above Top (classic). Variant **tight**: above the breaker's high.

## Contexts
- **A. Inside a CRT** (v4 frame): bearish CRT on the NY clock (C2 swept C1's high and closed back inside); D1 → M15 entries, H4 → M5 entries; the breaker must form and fill between C2's close and C3's close. Targets: half at 50% of C1 (stop to entry), rest at C1's far side.
- **B. Standalone**: every breaker on M15 and on H1, all hours. Target: **3R** (Ore's minimum), full exit; trades held up to 20 hours (M15) or 3 days (H1). Also reported for London/NY hours only (07:00–16:00 UTC entry).

## Judged
Per year 2021 (Nov–Dec) to 2026, average R after spread, trades, target hit rate vs chance (z). A variant is **consistent** only if average R after spread is positive in at least **4 of the 5** years 2022–2026 **and** in total. 8 variants (A: 2 stops; B: 2 timeframes × 2 stops, each also with the London/NY slice).

## Addendum v6b: breaker as entry, three ways (pre-registered 20 Nov 2026, before running them)
Ore asked to test the breaker as the entry in more ways. Same detection, contexts, stops, targets and scoring as above; only the entry changes.
- **edge** (as v6): sell limit at the breaker's low.
- **mid**: sell limit at the breaker's 50% (middle of its high–low).
- **confirm**: price trades up into the breaker (high reaches its low), then a candle **closes back below the breaker's low**: sell at that close (market). Same 20-candle window, ended by a trade above Top.
Context A takes the first breaker after C2's close in each CRT (as in the v6 run). 24 variants in total (3 entries × 2 stops × 4 contexts); same "consistent" rule. With this many tries, one or two "passes" are expected by luck, so any pass must also survive the walk-forward (spec v7).

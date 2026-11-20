# Edge hunt v3: result (rules in `docs/spec-v3-edge-hunt.md`, committed before the run, commit e2f6263)

Four markets (GBP/USD, gold, EUR/USD, silver), Nov 2021 onwards, costs included, 592 strategy variants across 7 families:
trend following, time-of-day drift, Asian-range breakout/fade, CRT continuation, big-day follow-up, day of week, Donchian breakout.

| Hurdle | Passed |
|---|---|
| Design 2021–2023 | 2 (both time-of-day, EUR/USD only) |
| Check 2024 | **0** |
| Final 2025–2026 | not run: nothing qualified (the final period stays unused) |

The two design survivors, both EUR/USD only (not Ore's markets):
- Long 21:00 UTC for 3 hours: +0.016 ATR per trade, t 4.4 (2022–23) → 2024: +0.005, t 1.0. **Failed.** Tiny anyway (≈ 1 pip), and 21:00 UTC is the daily rollover, when real spreads widen.
- Short 11:00 UTC for 1 hour: +0.020 ATR, t 3.6 → 2024: −0.013, t −1.7. **Failed** (reversed).

Best of the other families in 2021–23 (none near the t ≥ 3 bar): long Wednesday +0.05 ATR (t 1.8); 5-day trend, 5-day hold +0.10 ATR (t 1.4).
Clearly negative after costs: Asian-range breakouts (t −4 to −6), CRT continuation on H4 (t −4.8). Breakouts pay the spread and get faded.

Note on the luck test: sign-flipping returns while keeping costs makes random strategies lose the spread, so it produced 0 passes. That makes it a weak benchmark here; the 2024 hurdle did the real work.

Conclusion: across 7 families of well-known effects on 4 markets, nothing survived an unseen year. 2025–2026 is still untouched.

# Edge hunt v3 (pre-registered 20 Nov 2026, before any result)

Ore: "run series of tests and find patterns… go all the way to 2026". Everything about CRT so far tested at chance, so this looks wider, at effects that published research has found in FX and metals. Script: `backtest/edge_hunt.py`.

## Markets and costs (per trade, round trip)
GBP/USD 1.0 pip · EUR/USD 0.8 pip · gold $0.35 · silver $0.03. Results are in **ATR units**: net return ÷ the 14-day average daily range known at entry, so markets can be pooled.

## Strategy families (fixed list; each variant is one row)
| Family | Rule | Variants |
|---|---|---|
| A Trend (time-series momentum) | Daily (New York 17:00 close). Direction = sign of the last N days' return; hold H days; trade every H days | N ∈ {5, 10, 20, 60} × H ∈ {1, 5} = 8 |
| B Time-of-day drift | Hold long (or short) from UTC hour h for L hours, every weekday | 24 hours × L ∈ {1, 3, 6} × long/short = 144 per market |
| C Asian-range breakout | Asian range 00–07 UTC. First H1 close beyond it 07–16 UTC: trade the break (or fade it). Stop = range middle or far side; exit 1R, 2R, or 20:00 UTC | 2 × 2 × 3 = 12 |
| D CRT continuation | After a CRT (C2 swept C1's high and closed inside), if C3 trades beyond C2's sweep extreme, go WITH the break. Stop at C1's 50%; exit 1R, 2R, or C3's close. D1 and H4, New York clock | 3 × 2 = 6 |
| E Big-day follow-up | Day range ≥ k × ATR (k ∈ {1.5, 2}): next day continue or reverse the big day's direction | 4 |
| F Day of week | Long or short Mon…Fri close-to-close | 10 |
| G Donchian breakout | Close above the N-day high (below the low): enter; exit after 10 days or on the opposite N/2-day break | N ∈ {20, 55} × 2 exits = 4 |

## Hurdles (fixed now)
1. **Design, Nov 2021 – Dec 2023.** Pooled families (A, C–G): net mean > 0, **t ≥ 3.0**, positive in ≥ 3 of 4 markets, and positive in both 2022 and 2023. Family B is judged per market: **t ≥ 3.5** and positive in 2022 and 2023.
2. **Check, 2024:** net mean > 0 and t ≥ 2.0 (pooled, or that market for B).
3. **Final, 2025–2026, run once** (Ore's explicit request): net mean > 0 and t ≥ 2.0.

**Luck test:** the design hurdle is rerun 30 times on sign-flipped trade returns (gross, before costs; then costs). This shows how many "winners" chance produces.

Only something that clears all three hurdles is reported as an edge, with its numbers, not a promise.

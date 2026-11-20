# Spec v9: why Romeo's 3 filters leave so few trades, and looser versions (pre-registered 20 Nov 2026, before any result)

Ore asked to find what makes Romeo's filters so rare, loosen them, then add the breaker entry. Script: `backtest/breaker_filters.py` (extended). Same frame, breaker entries, stops, targets and scoring as spec v8.

## Why they are rare (measured on the v8 run, CRTs that produced a breaker trade, 2021–2026)
| | D1 (577 CRTs) | H4 (2,449 CRTs) |
|---|---|---|
| F1 HTF bias | 45% | 42% |
| F2 older high (10 candles) | 27% | 28% |
| F3 time | 42% | **9%** |
| F1 + F2 | 5.2% (12% if unrelated) | 6.2% (12% if unrelated) |
| All three | **1.9% (11)** | **0.7% (16)** |
1. F3 on H4 (01:00 range, 05:00 sweep, entry by 10:30 NY) allows one specific sequence per day.
2. F1 and F2 work against each other: taking an old high happens mostly when the higher timeframe is rising, and F1 asks for it to be bearish.

## Looser versions (each from Romeo's notes, `docs/romeo_pack/Romeotpt_CRT_Strategy_Notes.md`)
| Filter | Strict (v8) | **Loose (v9)** | Romeo's basis |
|---|---|---|---|
| F1 bias | last HTF candle bearish (closed below the previous low, or wicked above the previous high and closed inside) | bearish **or inside bar** (just **not bullish**) | §3: an inside bar means "the range continues", it isn't a signal against; "trade with the HTF CRT" = don't trade against it |
| F2 key level | sweep takes the highest high of the 10 candles before C1 | sweep takes the highest high of the **5** candles before C1, **or** the previous HTF candle's high (previous week's for D1, previous day's for H4), **or** runs into an older intact bearish FVG / order block | §1: key levels are "old highs and lows … FVGs", HTF levels |
| F3 time | D1: C1 Mon/Tue. H4: C1 01:00, C2 05:00 NY, entry by 10:30 | D1: the sweep (C2) on **Mon–Wed**. H4: C2 opens at **01:00, 05:00 or 09:00 NY**, entry before **16:00 NY** | §8: one weekly extreme forms Mon–Wed; the action window is 00:00–16:00 NY; the 1/5/9 candles |

## Tests (each with the 3 breaker entries × 2 stops × D1/H4)
5. Romeo **loose** 3 filters (all required) + breaker
6. Test 5 + MSnR
7. Romeo **any 2 of the 3 strict** filters + breaker (another way to get more trades without changing the definitions)
8. Test 7 + MSnR
Each loose filter alone is shown for information.

**Judged as v8:** consistent = 30+ trades, positive in 4 of 5 years (2022–2026) and in total; walk-forward (spec v7 rule) must not fail. With 4 new tests × 12 rows = 48 rows, about one "consistent" row is expected by luck, so a single consistent row without a walk-forward pass means nothing.

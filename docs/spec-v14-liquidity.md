# Spec v14: Inter Equity "liquidity + inducement" strategy, alone and paired with CRT (pre-registered 25 Nov 2026, before any result)

Source: Ore's notes and training pack (`docs/interequity_pack/`, from the Inter Equity Trading YouTube channel). His results are his own claims, unchecked. Data: Dukascopy 1-minute bid, Nov 2021 – Nov 2026, GBP/USD and gold, candles on Exness time (GMT+0), Ore's spreads (GBP/USD 1.0 pip, gold $0.24). Scoring as always: 1-minute outcomes, stop first if both hit in a minute, only the stop checked on the fill minute, spread included. Script: `backtest/liquidity_ie.py`. Every detected setup is re-checked by an independent audit (`backtest/audit_liquidity.py`) and example charts are drawn for Ore to check the candle formation.

## Choices for what his notes leave to judgment (notes §10), fixed now
| Point | Choice |
|---|---|
| Swing high/low | 5-bar fractal (2 candles each side), known only 2 candles later (no look-ahead) |
| "Respected"/intact liquidity | a swing low (high) not traded through since it formed |
| Stop buffer | 2 spreads beyond the liquidity block (as the CRT tests) |
| Minimum reward:risk | 1:3 to the final target (Ore's rule); nearer levels can be partial targets |
| Time stop | close the trade after 20 candles of the setup timeframe if nothing hit |
| News filter | none (no calendar data); noted as a limitation |
| Which LB / refinement | the one in the model definition below; no lower-timeframe refinement |

## Model 1: the 4-candle "sniper" entry (notes §3.2, schematic 03). Buy shown; sell is the mirror.
- **C1** any candle. **C2** trades **below C1's low** and **closes back above C1's low** (the sweep; C2's low is the liquidity block).
- **C3** has its low **above C2's low** and **closes bullish** (close > open).
- **Entry:** buy limit at **C3's low**, valid **only during C4**. Variant: limit at the **middle of the C3 low – C2 low zone**.
- **Stop:** below **C2's low** − 2 spreads.
- **Target:** the nearest **intact swing high** above the entry that gives at least 1:3 (checking up to 3 levels); if none, no trade. Management A: all out at that target. Management B: half off at the nearest intact swing high (if nearer), stop to entry, rest at the target.
- Timeframes: D1, H4, H1, M15, M5.

## Model 2: induce → trap → trade (notes §2, schematic 01). Sell shown; buy is the mirror.
1. **Sellers induced:** price trades below the latest confirmed swing low.
2. The **low of that down-leg** is tracked; if price makes a lower low, the leg extends.
3. **Retail sell high:** the first swing high confirmed after the leg's low.
4. **Sellers trapped = entry:** sell limit **at that high** (filled when price trades above it), placed once the high is confirmed, valid for 20 candles, cancelled if price breaks below the leg low first.
5. **Stop (liquidity block, "the high from the left"):** above the nearest earlier swing high that is higher than the entry high, + 2 spreads. No such high within 300 candles → no trade ("no LB, no trade").
6. **Targets:** first the **leg low** (lows left intact), then older intact swing lows below it; the final target is the first giving at least 1:3. Management A and B as in Model 1.
- Timeframes: H4, H1, M15, M5.

## Filters (reported as separate rows)
- **New York session:** the order is placed 08:00–17:00 New York time (his session). Intraday timeframes only.
- **Daily bias (notes §4):** bullish if yesterday traded below the day-before's low and not above its high (buyers trapped); bearish = mirror; trade only with it.

## Paired with CRT (notes §11)
CRT with Ore's rule (C2 swept C1 and closed inside C1's **body**), Exness candles, D1 → M15 entries and H4 → M5 entries. Inside the CRT's Candle-3 window (after C2 closes, before C3 closes), take Model 1 or Model 2 entries **in the CRT's direction** only. Stop = the model's liquidity-block stop. Targets: (a) CRT targets (half at C1's 50%, rest at C1's far side, far side ≥ 1:3), or (b) the model's liquidity targets.

## Judged (same rules as every earlier test)
- **Consistent** = at least 30 trades, average R after spread positive in at least 4 of the 5 years 2022–2026 and in total, and the final target hit at least as often as chance.
- Each family (Model 1 alone, Model 2 alone, CRT-paired) gets the **walk-forward** (spec v7 rule: pick on past years, trade the next year blind, 2023–2026).
- Anything that passes is **frozen and rerun on EUR/USD and silver** (never used) before it counts. About 90 rows are tested, so a few lucky "consistent" rows are expected by chance alone.

## Addendum (25 Nov 2026, after the main run, before the fresh-market run)
One row passed the consistency rule: **Model 1 (sniper), H4, entry at C3's extreme, management B, no filter** (+0.04R, 215 trades, 4 of 5 years). Frozen exactly as is and run on **EUR/USD (1.0 pip) and silver ($0.025)**. It passes only if, on the two markets pooled: average R > 0, positive in at least 3 of the 5 years 2022–2026, final target hit at least as often as chance, at least 30 trades.

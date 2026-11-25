# Spec v16: top-down bias + market structure shift + order block / FVG entry (pre-registered 25 Nov 2026, before any result)

Ore's request: find the bias on **D1 and H4**, drop to the entry timeframe, wait for a **market structure shift (MSS) in the bias direction**, enter from an **order block or fair value gap**. The standard smart-money (SMC/ICT) top-down model, with no CRT. (SMT *divergence* between correlated pairs was tested separately in v2.) Script: `backtest/smc_bias.py`. GBP/USD and gold, Nov 2021 – Nov 2026, Exness candles (GMT+0), 1-minute outcomes, stop first if both hit in a minute; every trade scored **after Ore's spreads**, and also **with no costs** for the bias rows.

## Rules (sell shown; buy is the mirror)
- **Bias:** market structure on each timeframe (the existing engine rule: direction = the last close beyond a confirmed swing high or low, swings 2 candles each side). Using only finished candles at the moment of the MSS. Versions: **D1 and H4 both bearish** (Ore's model), **D1 only** (for comparison), **no bias** (baseline: does the bias add anything?).
- **MSS on the entry timeframe:** a candle **closes below the latest confirmed swing low**, after price had made a higher point since that low (a pullback up, then a break down). Each swing low is used once. The **top** = the highest high between that swing low and the MSS candle.
- **Entries:** E1 market at the MSS close; E2/E3 limit at the latest unfilled bearish **FVG** in the move down (near edge / middle); E4/E5 limit at the **order block** (last up-close candle at or just before the top that took liquidity and left an FVG; its open / middle). These are the engine's existing definitions (`engine/structure.py`). Limits are valid for 12 entry candles and only if above the MSS close.
- **Stop:** above the top + 2 spreads. **Target:** 3R (Ore's 1:3 minimum), all out. Time limit 3 days.
- **Entry timeframes:** H1 and M15. (M5 left out for run time: about 4× as many setups. It can be added if anything here looks promising.)
- **Session filter** (Ore's v1.2 rule) as extra rows: MSS candle closes in London or New York.

## Judged (same standard as before)
A row is **consistent** with at least 30 trades, average R after spread positive in at least 4 of 5 years (2022–2026) and in total, and the target hit at least as often as chance (25% at 3R). Walk-forward per bias version. Any consistent row is frozen and rerun on EUR/USD + silver before it counts. 60 rows (2 timeframes × 5 entries × 3 bias versions × 2 session versions), so a couple of lucky passes are expected.

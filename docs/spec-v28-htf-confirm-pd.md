# Spec v28: Ore's rules from his loss reviews (pre-registered 27 Nov 2026, before any run)

From Ore's first loss reviews (2025–26 replay trades):
- **Rule 1, higher-timeframe confirmation:** "MSS should always close with the body ... confirm that on the H4 even
  if the lower timeframe has a valid MSS; HTF is always stronger than LTF."
- **Rule 2, premium / discount:** "we entered too early ... use the premium and discount logic and sell when the price
  is right": sell only in premium (above 50% of the dealing range), buy only in discount (below 50%).

## Definitions (fixed now)
- **Rule 1 (H4 confirm):** at the decision candle's close, the H4 external structure on **body closes**
  (`engine.smc_structure.external_structure`, mode "close", full history) points the trade's way: its last event is
  bullish for a buy, bearish for a sell.
- **Rule 2 (premium/discount):** at the decision candle's close, the H4 dealing range (`smc_structure.dealing_range`,
  close mode) gives high/low; 50% = (high + low) / 2. A sell passes if its entry price is above 50%; a buy passes if
  its entry is below 50%. Variant 2b: the same on the **D1** dealing range.
- Rules 1 + 2 combined is reported too.

## Trades (the live rules of each strategy, from existing backtest files, filled trades only)
| Strategy | Trades |
|---|---|
| CRT | Ore's rules (`ore_rules`), body close; one number per setup = average R of its filled options, entry = their average |
| Order block | v22 `smc_ob`, H1, 3R, D1+H4 trend (rule 1 is already part of it: reported, not decided) |
| IRL/ERL | v23 rows with H4 IRL/ERL + D1 trend; entry from the matching v22 order-block row |
| Toni Iyke | v22 `toni`, H1, swing-point target, D1 trend |
| Lingard | v22 `lingard`, H4, 5R, D1 trend, London/NY |
| Ore's model | v26 (exact live function), filled |

## Test sets
- **A:** GBP/USD + gold, **2021–2024** (Ore's examples came from 2025–26).
- **B:** EUR/USD + silver, all years.

## Pass rule (per strategy, per variant)
A filter is adopted for a strategy only if in **both** A and B the filtered trades (n >= 20) average **above 0R**
and at least **0.10R above** the same strategy's unfiltered trades. "All strategies pooled" uses the same rule with
n >= 30 and decides whether the filter applies to every strategy at once.

Results are appended below; nothing above is edited after the runs.

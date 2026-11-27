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

## Results (run 27 Nov 2026, `python -m backtest.htf_pd_v28`; CRT decision times fixed to ns before the counted run)

| Strategy | Rule | A: all → kept (n) | B: all → kept (n) | Pass |
|---|---|---|---|---|
| crt | 1: H4 confirm | +0.014 → +0.099 (220) | -0.131 → -0.076 (361) | fail |
| crt | 2: premium/discount H4 | +0.014 → +0.087 (253) | -0.131 → -0.131 (454) | fail |
| crt | 2b: premium/discount D1 | +0.014 → -0.087 (201) | -0.131 → -0.150 (386) | fail |
| crt | 1+2 | +0.014 → +0.282 (91) | -0.131 → -0.086 (162) | fail |
| smc_ob | 1: H4 confirm | -0.455 → -0.455 (21) | -0.313 → -0.313 (29) | fail |
| smc_ob | 2: premium/discount H4 | -0.455 → -0.239 (10) | -0.313 → -0.705 (13) | fail |
| smc_ob | 2b: premium/discount D1 | -0.455 → -1.000 (6) | -0.313 → -0.453 (7) | fail |
| smc_ob | 1+2 | -0.455 → -0.239 (10) | -0.313 → -0.705 (13) | fail |
| irl_erl | 1: H4 confirm | +0.203 → -1.000 (6) | -0.139 → -0.306 (16) | fail |
| irl_erl | 2: premium/discount H4 | +0.203 → +0.058 (22) | -0.139 → -0.132 (50) | fail |
| irl_erl | 2b: premium/discount D1 | +0.203 → -0.011 (12) | -0.139 → +0.028 (30) | fail |
| irl_erl | 1+2 | +0.203 → -1.000 (6) | -0.139 → -0.521 (8) | fail |
| toni | 1: H4 confirm | +0.025 → +0.060 (151) | -0.173 → -0.102 (227) | fail |
| toni | 2: premium/discount H4 | +0.025 → +0.222 (56) | -0.173 → -0.146 (108) | fail |
| toni | 2b: premium/discount D1 | +0.025 → +0.210 (35) | -0.173 → -0.324 (92) | fail |
| toni | 1+2 | +0.025 → +0.495 (27) | -0.173 → -0.140 (45) | fail |
| lingard | 1: H4 confirm | +0.068 → +0.314 (13) | +0.162 → +0.130 (33) | fail |
| lingard | 2: premium/discount H4 | +0.068 → +0.314 (13) | +0.162 → +0.479 (33) | fail |
| lingard | 2b: premium/discount D1 | +0.068 → +0.897 (3) | +0.162 → +0.367 (19) | fail |
| lingard | 1+2 | +0.068 → +0.553 (11) | +0.162 → +0.553 (24) | fail |
| ore_poi | 1: H4 confirm | +0.608 → +0.210 (15) | +0.497 → +0.297 (17) | fail |
| ore_poi | 2: premium/discount H4 | +0.608 → +0.561 (9) | +0.497 → +0.772 (15) | fail |
| ore_poi | 2b: premium/discount D1 | +0.608 → +1.813 (4) | +0.497 → +0.573 (7) | fail |
| ore_poi | 1+2 | +0.608 → -0.457 (6) | +0.497 → +0.262 (6) | fail |
| ALL | 1: H4 confirm | +0.027 → +0.053 (426) | -0.122 → -0.081 (683) | fail |
| ALL | 2: premium/discount H4 | +0.027 → +0.117 (363) | -0.122 → -0.094 (673) | fail |
| ALL | 2b: premium/discount D1 | +0.027 → -0.024 (261) | -0.122 → -0.146 (541) | fail |
| ALL | 1+2 | +0.027 → +0.225 (151) | -0.122 → -0.072 (258) | fail |

**No rule passes; no live change.** Direction is consistent, though: H4 confirmation and premium/discount (H4)
raise the average in both sets for CRT and for all strategies pooled (1+2 pooled: A +0.027 → +0.225R on 151 trades,
B −0.122 → −0.072R on 258), but set B stays below zero. D1 premium/discount does not help. Kept as a lead for the
live record; Ore's loss reviews may sharpen it (e.g. which dealing range he means).

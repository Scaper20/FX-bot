# Backtest report: spec v1.2 (Ore's chart feedback + spread-aware stops)

Rules and selection method: `docs/spec-v1.2.md`, committed **before** any v1.2 result (commit 26c87d4).
Design = Nov 2021 – Dec 2023. Check = 2024, run once for v1.2 (also once at 2x cost for the cost estimate). Final 2025–2026: untouched.
Costs: GBPUSD 1.0 pip, XAUUSD $0.35 (assumed; Ore's real Exness Standard spreads still needed).

## Result: nothing passed the 2024 Check convincingly
| Step | Result |
|---|---|
| Stage A, best filter (Design) | GBPUSD: London session + 20-day-average direction + sweep depth ≥ 0.1 ATR, +0.27 R over 144 setups. All 8 London combinations were +0.22 to +0.27 R. XAUUSD: 0 of 32 combinations positive (best −0.22 R) |
| Stage B, finalists (Design) | 1,453 variants tried; 33 GBPUSD and 1 XAUUSD qualified; top 10 + 1 sent to Check. Best Design t-score 2.07 |
| Stage C, Check 2024 | **1 of 11 passed** (the XAUUSD finalist: +0.17 R on 38 trades, but only +0.09 R in Design, consistent with luck). The 10 GBPUSD finalists: 2024 average between −1.00 and +0.18 R, none passed |
| Stage A filter in 2024 | GBPUSD London filter: **−0.31 R** over 66 setups (vs +0.27 in Design) |

## What did hold up in both periods (information only, not used for selection)
| Average R per trade | Design GBPUSD | 2024 GBPUSD | Design XAUUSD | 2024 XAUUSD |
|---|---|---|---|---|
| v1, all setups | −0.22 | −0.47 | −0.46 | −0.26 |
| London/NY sessions only (no Friday late) | −0.03 | −0.32 | −0.26 | −0.09 |
| + Ore's direction rule (with trend, or against only with HTF OB/FVG) | +0.04 | −0.39 | −0.26 | −0.05 |

- **Sessions help in every column.** Trading only London/New York is a real improvement over v1, but not enough to turn a profit.
- **The direction rule** helps in 2 of 4 columns: not clearly better than no rule.
- **Costs are a large share of the result.** One spread costs about 0.25 R per trade on average (sweep-extreme stops). Estimated zero-cost results swing from period to period (GBPUSD +0.45 → −0.01; XAUUSD +0.07 → +0.39), so there is no stable edge even before costs.

## Honest reading
Two rounds of rules, about 34,000 combinations, and two independent periods have not produced a version that holds up. The 2024 Check has now been used for v1.2; any further rule change tested on 2024 is weaker evidence, and this report says so.

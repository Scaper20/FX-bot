# Spec v13 result: limit orders with and without expiry / the cancel-at-50% rule

Spec: `docs/spec-v13-expiry-cancel.md` (committed before the run). v1.4 engine (C2 closes inside C1's body), Nov 2021 – Nov 2026, GBP/USD + gold, Ore's spreads, limit entries E2–E5, stop = sweep + 2 spreads, one trade per setup per entry type.

## Ore's rules · half at 50%, stop to entry, rest at far side

| Version | Orders | Filled | Avg R (filled) | 2022 | 2023 | 2024 | 2025 | 2026 | Extra trades vs A | Extra trades avg R | Extra: years + |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A. Current (expires, cancels at 50%) | 2281 | 627 (27%) | **+0.044** | +0.07 | -0.10 | +0.01 | +0.36 | -0.21 | — | — | — |
| B. No expiry | 2281 | 684 (30%) | **+0.028** | +0.04 | -0.05 | -0.06 | +0.27 | -0.12 | 62 | +0.037 | 2 of 5 |
| C. No 50% cancel | 2281 | 1234 (54%) | **-0.193** | -0.12 | -0.24 | -0.22 | -0.11 | -0.31 | 611 | -0.425 | 0 of 5 |
| D. Neither | 2281 | 1998 (88%) | **-0.130** | -0.07 | -0.15 | -0.15 | -0.21 | -0.07 | 1373 | -0.199 | 1 of 5 |

## Ore's rules · all out at far side

| Version | Orders | Filled | Avg R (filled) | 2022 | 2023 | 2024 | 2025 | 2026 | Extra trades vs A | Extra trades avg R | Extra: years + |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A. Current (expires, cancels at 50%) | 2281 | 627 (27%) | **+0.028** | +0.18 | -0.10 | -0.15 | +0.52 | -0.44 | — | — | — |
| B. No expiry | 2281 | 684 (30%) | **+0.012** | +0.17 | -0.03 | -0.23 | +0.36 | -0.29 | 62 | +0.078 | 2 of 5 |
| C. No 50% cancel | 2281 | 1234 (54%) | **-0.230** | -0.12 | -0.28 | -0.31 | -0.10 | -0.43 | 611 | -0.484 | 0 of 5 |
| D. Neither | 2281 | 1998 (88%) | **-0.142** | -0.09 | -0.14 | -0.16 | -0.20 | -0.14 | 1373 | -0.208 | 1 of 5 |

## All setups · half at 50%, stop to entry, rest at far side

| Version | Orders | Filled | Avg R (filled) | 2022 | 2023 | 2024 | 2025 | 2026 | Extra trades vs A | Extra trades avg R | Extra: years + |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A. Current (expires, cancels at 50%) | 5147 | 1808 (35%) | **-0.059** | -0.09 | -0.03 | -0.07 | -0.01 | -0.14 | — | — | — |
| B. No expiry | 5147 | 1902 (37%) | **-0.040** | -0.04 | -0.02 | -0.04 | -0.05 | -0.10 | 101 | +0.400 | 4 of 5 |
| C. No 50% cancel | 5147 | 3071 (60%) | **-0.166** | -0.14 | -0.17 | -0.19 | -0.08 | -0.25 | 1270 | -0.320 | 0 of 5 |
| D. Neither | 5147 | 4560 (89%) | **-0.129** | -0.14 | -0.08 | -0.13 | -0.13 | -0.15 | 2754 | -0.170 | 0 of 5 |

## All setups · all out at far side

| Version | Orders | Filled | Avg R (filled) | 2022 | 2023 | 2024 | 2025 | 2026 | Extra trades vs A | Extra trades avg R | Extra: years + |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A. Current (expires, cancels at 50%) | 5147 | 1808 (35%) | **-0.093** | -0.07 | -0.02 | -0.17 | -0.01 | -0.28 | — | — | — |
| B. No expiry | 5147 | 1902 (37%) | **-0.065** | -0.01 | +0.01 | -0.12 | -0.07 | -0.20 | 101 | +0.556 | 4 of 5 |
| C. No 50% cancel | 5147 | 3071 (60%) | **-0.184** | -0.13 | -0.17 | -0.25 | -0.09 | -0.29 | 1270 | -0.316 | 0 of 5 |
| D. Neither | 5147 | 4560 (89%) | **-0.126** | -0.15 | -0.02 | -0.11 | -0.17 | -0.16 | 2754 | -0.142 | 1 of 5 |

## By entry, Ore's rules · half at 50% (average R per filled trade; filled count)

| Entry | A. Current (expires, cancels at 50%) | B. No expiry | C. No 50% cancel | D. Neither |
|---|---|---|---|---|
| FVG edge | +0.265 (86) | +0.221 (89) | +0.168 (108) | -0.007 (137) |
| FVG middle | +0.160 (114) | +0.134 (120) | +0.046 (143) | -0.066 (188) |
| OB open | -0.059 (209) | -0.043 (231) | -0.262 (464) | -0.139 (780) |
| OB middle | -0.006 (218) | -0.028 (244) | -0.272 (519) | -0.155 (893) |

## Verdict (spec rule: Ore's rules, half management)

- B. No expiry: avg +0.028 vs current +0.044; extra trades +0.037, positive in 2 of 5 years -> **not better**
- C. No 50% cancel: avg -0.193 vs current +0.044; extra trades -0.425, positive in 0 of 5 years -> **not better**
- D. Neither: avg -0.130 vs current +0.044; extra trades -0.199, positive in 1 of 5 years -> **not better**

## Reading (written after the run)
- **The cancel-at-50% rule protects you.** Without it, about twice as many orders fill, and the extra fills (orders that fill *after* price already reached 50%) lose **−0.43R each with Ore's rules**, negative in every year 2022–2026 (all setups: −0.32R, 0 of 5 years). These are late entries on a pullback after Target 1 was reached: price came back to your level because the move was reversing, so many go on to the stop. Keep the rule.
- **Expiry barely matters.** Keeping orders open for up to 20 range candles adds only ~60 fills (Ore's rules), averaging +0.04R, positive in 2 of 5 years: no real difference. Across all setups the ~100 extra fills did better (+0.40R, 4 of 5 years), but that's a small group and not with Ore's rules. Not enough to change the rule.
- **Both removed** = 88% of orders fill, −0.13R a trade: the worst-but-one version.
- A first version of this script forgot the 1:3 minimum to the far side (it let in trades below Ore's minimum); fixed before these numbers. Verdict was the same in both runs.

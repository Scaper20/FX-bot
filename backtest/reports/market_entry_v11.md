# Spec v11 result: instant market entry vs limit orders, same setups

Spec: `docs/spec-v11-market-entry.md` (committed before the run). v1.2 engine trade logs, Nov 2021 – Nov 2026, GBP/USD + gold, stop = sweep extreme + 2 spreads, spread included. E1 = market at the trigger candle's close.

## All setups · all out at the opposite side

**Market entry (E1):** 1421 trades, average +0.045R, total +63.6R, positive in 3 of 5 years (2022: -0.07, 2023: +0.10, 2024: -0.09, 2025: +0.21, 2026: +0.07). Target hit 14.6% vs chance 19.2%. -> **does not work** by the spec rule.

| Limit entry | Limit filled: trades / avg R | E1 on those same setups | **Limit cancelled or expired: setups** | **E1 on those setups (avg R)** | E1 on them, years + |
|---|---|---|---|---|---|
| limit at FVG edge | 437 / +0.213 | -0.087 | 82 | **+1.262** | 5 of 5 |
| limit at FVG middle | 462 / +0.179 | -0.153 | 112 | **+1.295** | 5 of 5 |
| limit at OB open | 652 / +0.248 | -0.300 | 209 | **+1.138** | 5 of 5 |
| limit at OB middle | 686 / +0.177 | -0.432 | 293 | **+1.214** | 5 of 5 |

## All setups · half at 50%, stop to entry, rest at the opposite side

**Market entry (E1):** 1421 trades, average +0.037R, total +53.0R, positive in 4 of 5 years (2022: -0.14, 2023: +0.01, 2024: +0.01, 2025: +0.18, 2026: +0.13). -> **WORKS** by the spec rule.

| Limit entry | Limit filled: trades / avg R | E1 on those same setups | **Limit cancelled or expired: setups** | **E1 on those setups (avg R)** | E1 on them, years + |
|---|---|---|---|---|---|
| limit at FVG edge | 437 / +0.179 | -0.120 | 82 | **+1.284** | 5 of 5 |
| limit at FVG middle | 462 / +0.136 | -0.175 | 112 | **+1.318** | 5 of 5 |
| limit at OB open | 652 / +0.180 | -0.319 | 209 | **+1.146** | 5 of 5 |
| limit at OB middle | 686 / +0.102 | -0.453 | 293 | **+1.282** | 5 of 5 |

## Ore's rules only · all out at the opposite side

**Market entry (E1):** 418 trades, average -0.071R, total -29.6R, positive in 2 of 5 years (2022: -0.26, 2023: -0.15, 2024: +0.14, 2025: +0.24, 2026: -0.23). Target hit 10.5% vs chance 18.8%. -> **does not work** by the spec rule.

| Limit entry | Limit filled: trades / avg R | E1 on those same setups | **Limit cancelled or expired: setups** | **E1 on those setups (avg R)** | E1 on them, years + |
|---|---|---|---|---|---|
| limit at FVG edge | 124 / +0.896 | +0.283 | 28 | **+0.634** | 4 of 5 |
| limit at FVG middle | 126 / +0.704 | +0.095 | 38 | **+1.002** | 5 of 5 |
| limit at OB open | 180 / +0.424 | -0.175 | 70 | **+0.783** | 4 of 5 |
| limit at OB middle | 199 / +0.207 | -0.357 | 96 | **+1.068** | 5 of 5 |

## Ore's rules only · half at 50%, stop to entry, rest at the opposite side

**Market entry (E1):** 418 trades, average +0.013R, total +5.3R, positive in 2 of 5 years (2022: -0.27, 2023: -0.12, 2024: +0.18, 2025: +0.32, 2026: -0.01). -> **does not work** by the spec rule.

| Limit entry | Limit filled: trades / avg R | E1 on those same setups | **Limit cancelled or expired: setups** | **E1 on those setups (avg R)** | E1 on them, years + |
|---|---|---|---|---|---|
| limit at FVG edge | 124 / +0.702 | +0.178 | 28 | **+0.787** | 4 of 5 |
| limit at FVG middle | 126 / +0.468 | -0.029 | 38 | **+1.170** | 5 of 5 |
| limit at OB open | 180 / +0.251 | -0.255 | 70 | **+0.972** | 5 of 5 |
| limit at OB middle | 199 / +0.122 | -0.366 | 96 | **+1.200** | 5 of 5 |

## Verdict

| Scope | Management | E1 trades | E1 avg R | Years + | Works? |
|---|---|---|---|---|---|
| All setups | all out at the opposite side | 1421 | +0.045 | 3 of 5 | no |
| All setups | half at 50%, stop to entry, rest at the opposite side | 1421 | +0.037 | 4 of 5 | YES |
| Ore's rules only | all out at the opposite side | 418 | -0.071 | 2 of 5 | no |
| Ore's rules only | half at 50%, stop to entry, rest at the opposite side | 418 | +0.013 | 2 of 5 | no |

## Reading (written after the run)
- **"Market entry on the cancelled setups: +1.1 to +1.3R" is hindsight, not a strategy.** A limit is cancelled *because* price ran away without coming back, so those are the winners by definition, and you can't know in advance which setups they'll be. The mirror image proves it: on setups where the limit did fill, market entry lost (−0.09 to −0.45R). Limits miss winners and market entries catch the losers that limits avoid. They balance out.
- **The honest number is market entry on every setup:** +0.037R a trade (half at 50%). It technically meets the spec rule (4 of 5 years), but the checks below show it's noise:
  - t-stat 0.88 (about 2+ is needed to tell it from luck);
  - the same setup was counted up to 4 times (H1 and M15 entries, CISD and MSS triggers). **One trade per setup: 638 setups, +0.027R, t 0.42, positive in 3 of 5 years** (2022 −0.19, 2023 +0.09, 2024 −0.05, 2025 +0.24, 2026 +0.06);
  - target hit **below** chance (14.6% vs 19.2%); the profit comes from trades closed at the time limit while ahead (+194R), not from targets;
  - gold loses (−0.03R); only GBP/USD is positive (+0.12R), D1→H1 best (+0.22R, 110 trades: a small slice).
- With Ore's rules: −0.07R / +0.01R, 2 of 5 years. Doesn't work.

**Verdict: market entry doesn't create an edge. It trades the missed winners for extra losers, and nets out at about zero after spread.**

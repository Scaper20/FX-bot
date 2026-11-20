# SMT test: result (rules in `docs/spec-v2-smt.md`, committed before the run, commit 1bfc508)

GBP/USD vs EUR/USD, gold vs silver. New York clock, D1 and H4, Nov 2021 – Dec 2023. SMT = during the sweep candle our market takes C1's high (low) but the partner does not take its own. Found on 30% of CRTs.

| Entry | TF | Group | Trades | Target 1 hit vs chance | z | Avg R after spread |
|---|---|---|---|---|---|---|
| C2 close | D1 | SMT | 77 | 52% vs 55% | −0.5 | −0.05 |
| C2 close | D1 | no SMT | 188 | 64% vs 60% | +1.3 | +0.08 |
| C2 close | D1 | SMT + HTF bias | 30 | 50% vs 53% | −0.4 | +0.15 |
| C2 close | H4 | SMT | 441 | 58% vs 58% | 0.0 | −0.14 |
| C2 close | H4 | no SMT | 1,041 | 60% vs 61% | −0.7 | −0.10 |
| C2 close | H4 | SMT + HTF bias | 193 | 58% vs 59% | −0.4 | −0.15 |
| Candle 3 + Model #1 | D1 | SMT | 31 | 35% vs 26% | +1.2 | +0.09 |
| Candle 3 + Model #1 | D1 | no SMT | 102 | 26% vs 25% | +0.5 | −0.13 |
| Candle 3 + Model #1 | H4 | SMT | 149 | 25% vs 32% | −2.1 | −0.45 |
| Candle 3 + Model #1 | H4 | no SMT | 327 | 29% vs 31% | −1.1 | −0.21 |
| Candle 3 + Model #1 | H4 | SMT + HTF bias | 68 | 22% vs 33% | −2.1 | −0.45 |

**Nothing passed** (needed z ≥ 2.5, 40+ trades, and SMT beating no-SMT). The one positive cell (D1 Candle 3 with SMT, z +1.2) has only 31 trades, which is what luck looks like across 12 cells. On H4, SMT trades did slightly *worse* than chance. 2024 and 2025–2026 not used.

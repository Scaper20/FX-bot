# Spec v6 result: breaker blocks (run 20 Nov 2026)

Spec: `docs/spec-v6-breaker.md` (committed before the run). Script: `python -m backtest.breaker` (3 minutes). GBP/USD + gold, Nov 2021 – Nov 2026, 1-minute outcomes, spread included. Look-ahead check: scrambling all candles after a cut point leaves every earlier breaker unchanged (3 cuts, 92–358 signals each).

## Average R per trade after spread, by year

| Variant | Trades | 2022 | 2023 | 2024 | 2025 | 2026 | Avg R | Years + (of 5) | Target hit vs chance |
|---|---|---|---|---|---|---|---|---|---|
| A in CRT, D1 → M15, classic stop | 577 | +0.13 | −0.07 | +0.05 | −0.24 | −0.20 | −0.06 | 2 | 25.3% vs 27.3% |
| A in CRT, D1 → M15, tight stop | 577 | −0.09 | −0.29 | −0.13 | −0.24 | −0.30 | −0.21 | 0 | 10.6% vs 11.9% |
| A in CRT, H4 → M5, classic stop | 2,449 | −0.13 | −0.11 | −0.20 | −0.08 | −0.08 | −0.13 | 0 | 37.2% vs 38.5% |
| A in CRT, H4 → M5, tight stop | 2,449 | −0.31 | −0.33 | −0.33 | −0.24 | −0.28 | −0.30 | 0 | 19.6% vs 19.7% |
| B standalone H1, classic, 3R | 2,058 | −0.14 | −0.02 | +0.01 | +0.02 | +0.02 | −0.03 | 3 | 18.8% vs 25% |
| ↳ London/NY hours only | 1,237 | −0.17 | −0.06 | +0.17 | +0.00 | +0.17 | +0.01 | 3 | 20.6% vs 25% |
| B standalone H1, tight, 3R | 2,058 | −0.18 | −0.19 | −0.15 | −0.08 | −0.14 | −0.14 | 0 | 22.6% vs 25% |
| B standalone M15, classic, 3R | 8,027 | −0.04 | −0.11 | −0.06 | −0.08 | −0.06 | −0.07 | 0 | 20.6% vs 25% |
| B standalone M15, tight, 3R | 8,028 | −0.20 | −0.25 | −0.15 | −0.20 | −0.20 | −0.20 | 0 | 23.6% vs 25% |

Rule: consistent = positive in at least 4 of 5 years (2022–2026) and in total. **0 of 8 pass** (also 0 per pair; full table incl. per-pair rows in `backtest/out/breaker_yearly.csv`).

## What it means
1. **Inside a CRT, breakers hit targets at the chance rate or a little below**, like every other entry model tested. The tight stop gives bigger reward per trade but wins less often by the same amount, then spread makes it worse.
2. **Standalone, the 3R target is hit less often than chance (19–21% vs 25%, z −3 to −8).** Price tends to come back after the shift rather than run on.
3. **The one near-zero row (H1 classic, London/NY, +0.01R, 3 of 5 years)** is one slice out of 28, positive mainly in 2024 and 2026 and below chance on target hits. It isn't an edge. At most, it's something to watch on the live log.

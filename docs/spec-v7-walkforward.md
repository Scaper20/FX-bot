# Spec v7: walk-forward for every strategy (pre-registered 20 Nov 2026, before any result)

Ore asked that every strategy gets a walk-forward. A walk-forward copies what a trader would really have done: **choose using only the past, then trade the next year blind**, and repeat. Only the "next year" results count. Script: `backtest/walkforward.py`.

## Families (every strategy tested so far)
| Family | Unit that can be chosen | Data |
|---|---|---|
| v1.2 CRT variants | pair × range TF × entry TF × trigger × entry type × stop type × management | `backtest.run` design + check + final (final period now run, Ore's all-years decision) |
| Romeo v2 | pair × TF × entry kind × filter (none, F1, F2, F3, all three) | `backtest.romeo.run`, all years |
| Combination search + SMT | pair × TF × entry × up to 2 conditions (25 conditions + SMT) | `backtest.search.scan` with partner, all years |
| Edge hunt v3 | family × variant × market (4 markets) | existing log |
| v4 advanced models | model × TF × pair (incl. mixing) | existing log |
| v6 breakers | variant × pair | existing log |
| v5 trend (daily, long history) | signal (portfolio, GBP/USD, gold separately) | `data/long/` |

## Rule (anchored, yearly)
- **Test years 2023, 2024, 2025, 2026** (to 18 Nov). Each year, train on everything from Nov 2021 to the end of the year before.
- Only units with **at least 30 trades** in training can be picked. Score = **t-statistic** of the average R after spread (average ÷ standard error), so a big average on few trades doesn't win by luck.
- **Pick A, "the best one":** the single unit with the highest training score, traded for the whole next year.
- **Pick B, "everything that looked good":** every unit with training score ≥ 2.0, all traded next year with equal weight. No unit, no trades.
- **Trend:** test years 1981–2026, trained on all years before (from 1971); pick the signal with the best training Sharpe; report next-year Sharpe for 1981–2012, 2013–2026 and 2021–2026.

## Passes
A family passes if its **next-year results** (Pick A or Pick B) have average R after spread > 0 over 2023–2026 combined, are positive in **at least 3 of the 4** test years, with at least 30 trades. Trend passes if next-year Sharpe 2013–2026 > 0.3.

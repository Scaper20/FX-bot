# Spec v18: Asian-session trades (pre-registered 25 Nov 2026, before any run)

Ore asked: "Do test for Asian session trades." Both live strategies normally recommend London / New York only
(CRT by Ore's rule; the order block backtest pooled every hour). This test asks whether setups whose trigger forms
in the Asian session do better, worse or the same.

## Definitions
- **Asia** = decision time (CRT trigger candle close; order-block MSS candle close) from 00:00 to 07:00
  **London time** (Tokyo hours before London opens; summer time handled by the timezone database). Same as
  `engine.sessions.session_of() == "asia"`.
- **London/NY** = Ore's existing session rule (`session_flags` not empty).
- **Late** = everything else (17:00 New York to midnight London). Reported for information only, never a pass.
- Data: GBP/USD + spot gold, Dukascopy M1, Nov 2021 – Nov 2026, after Ore's spreads (GBP/USD 1.0 pip, gold $0.24).
  Existing trade logs, no new detection code:
  - CRT (body-close rule): `backtest/out/trades_{design,check,final}.csv`. Ore's other rules kept
    (with daily direction or HTF-backed, not Friday late, 1:3 minimum); only the session rule is swapped.
  - Order block: `backtest/out/smc_{PAIR}_{H1,M15}.csv`, D1+H4 bias rows. Fresh markets: `smcfresh_*_H1.csv`.

## Rows
- CRT: range TF (D1/H4) × entry type × management, pooled over pairs, triggers and stops; plus "all options".
- Order block: TF (H1/M15) × entry (E1–E5); headline H1 E4 (the live strategy).
- Each row reported for Asia, London/NY and Late side by side.

## Pass rule (same as every spec since v7)
A row is **consistent** if it has ≥ 30 trades, average R after spread > 0 in total and in ≥ 4 of the 5 years
(2022–2026), and its target hit rate ≥ chance (risk / (risk + reward)).
An Asia row only counts if it is consistent **and** then holds, unchanged, on markets it was not built on
(EUR/USD + silver). For the order block those trade logs exist; for CRT the fresh-market run would be a new step,
reported as "not run" if needed.
Many rows are tested, so roughly 1 in 20 can look good by luck; a lone passing row is a lead, not an edge.

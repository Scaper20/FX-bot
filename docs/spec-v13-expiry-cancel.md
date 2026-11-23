# Spec v13: what if limit orders don't expire, and aren't cancelled at 50%? (pre-registered 23 Nov 2026, before any result)

Ore asked to test the two order rules:
- **Expiry:** an unfilled limit is dropped when the 2nd range candle after the sweep candle closes (D1 ≈ 2 days, H4 ≈ 8 hours).
- **Cancel at 50%:** an unfilled limit is dropped if price reaches 50% of C1 (Target 1) first. Added by Claude while building (spec v1 "details fixed while building"), never tested.

**Four versions, same setups, same orders** (v1.4 engine, body-close rule, Ore's spreads, Nov 2021 – Nov 2026, limit entries E2–E5, stop = sweep + 2 spreads; both managements):
| Version | Expires after 2 range candles | Cancelled at 50% |
|---|---|---|
| A. Current | yes | yes |
| B. No expiry | no (kept up to 20 range candles: D1 20 days, H4 80 hours) | yes |
| C. No 50% cancel | yes | no |
| D. Neither | no (20-candle cap) | no |
Unchanged: no fill on the decision candle's past, stop first if both hit in a minute, only the stop checked on the fill minute, 5-range-candle time stop after the fill.

**Reported:** fill rate; average R after spread per filled trade, per year, for all setups and for Ore's rules; one trade per setup per entry type; and, separately, **the extra trades** each version adds (orders the current rules would have dropped): how those extra fills did on their own.

**Judged:** a version beats the current rules only if, with Ore's rules, its average R is higher **and** the extra trades are themselves positive on average **and** positive in at least 3 of 5 years (2022–2026). Otherwise the current rules stay.

# Spec v10: the v9 candidate on markets it has never seen (pre-registered 20 Nov 2026, before any result)

The rule is frozen exactly as found in v9 (no change of any setting): **Romeo loose 3 filters (F1L, F2L, F3L) + MSnR, H4 range → M5 breaker entry, classic stop**, entries edge / confirm / mid, targets half at 50% of C1 then C1's far side, all as in `backtest/breaker_filters.py`. Run on **EUR/USD and XAG/USD (silver)**, Nov 2021 – Nov 2026, Dukascopy M1 bid. Neither market was used to find or shape this rule.

**Costs:** EUR/USD spread 1 pip (0.00010); silver 3 cents (0.03). Ore's Exness spreads for these are unknown.

**Passes if, on the two markets pooled:**
1. the **edge classic** row (fixed as the main row now) has average R after spread **> 0**, and
2. at least **2 of the 3** classic rows (edge, confirm, mid) have average R > 0, and
3. edge classic hits Target 2 **at least as often as chance**.
Also reported per market and per year, with trade counts. Expected trades: roughly 40–100 per row. If fewer than 30, the result is reported as too small to decide.

If it passes, the rule is a stronger candidate and goes to live logging. If it fails, v9's result is treated as luck.

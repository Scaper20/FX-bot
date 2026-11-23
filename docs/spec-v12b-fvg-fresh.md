# Spec v12b: the FVG-limit candidate on markets it has never seen (pre-registered 23 Nov 2026, before running)

Found while retesting with Ore's body-close rule (spec v12): under Ore's rules (London/NY session, not Friday late, with the daily direction or an HTF OB/FVG on the left), stop = sweep extreme + 2 spreads, half off at 50% then the rest at C1's far side, one trade per setup (first trigger):
- **E3, limit at the FVG middle:** +0.22R, 116 setups, positive in 5 of 5 years (2022–2026), t 1.44;
- **E2, limit at the FVG edge:** +0.31R, 86 setups, 4 of 5 years, t 1.74.
Found by looking at 5 entries, so it may be luck. The walk-forward over all 2,882 engine variants failed.

**Frozen rule, run unchanged** with the same engine (`backtest.run` logic, body-close rule) on **EUR/USD and silver (XAG/USD)**, Nov 2021 – Nov 2026. Neither market was used to find it. Spreads: EUR/USD 1.0 pip, silver $0.025 (Ore's Exness screenshot). Script: `backtest/fvg_fresh.py`.

**Passes only if, on the two new markets pooled, one trade per setup:**
1. E3 average R after spread **> 0**, **and**
2. E3 positive in **at least 3 of the 5 years** 2022–2026, **and**
3. E3 hits the far target at least as often as chance, **and**
4. at least 40 setups.
E2 is reported alongside but doesn't decide. If it passes, it becomes the one rule worth logging live and testing with demo trades. If it fails, it's treated as luck like v9.

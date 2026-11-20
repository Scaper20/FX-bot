# Spec v7 result: walk-forward for every strategy

Spec: `docs/spec-v7-walkforward.md` (committed before the run). Each year, the unit is chosen using only earlier years, then traded blind for the year. Only those blind years are shown. R after spread (edge hunt in ATR units).

## v1.2 CRT variants (2,986 units)

| Test year | Pick A (best past t) | past t | past avg | trades | **blind avg R** | Pick B units (t ≥ 2) | trades | **blind avg R** |
|---|---|---|---|---|---|---|---|---|
| 2023 | GBPUSD H4 M5 1 MSS E3 S1p M1_T2 | 1.63 | +0.751 | 25 | **+0.548** | 0 | 0 | **—** |
| 2024 | GBPUSD H4 M5 1 MSS E3 S1p M1_T2 | 1.93 | +0.665 | 23 | **+0.154** | 0 | 0 | **—** |
| 2025 | GBPUSD H4 M5 1 MSS E3 S1p M1_T2 | 1.81 | +0.521 | 32 | **-0.164** | 0 | 0 | **—** |
| 2026 | GBPUSD H4 M15 1 MSS E5 S1p M1_T3 | 1.53 | +0.701 | 24 | **-0.046** | 0 | 0 | **—** |

Pick A: blind average +0.105 over 104 trades, positive in 2 of 4 years -> **fail**. Pick B: no unit ever reached t ≥ 2 in training, so no trades -> **fail**.

## Romeo v2 (40 units)

| Test year | Pick A (best past t) | past t | past avg | trades | **blind avg R** | Pick B units (t ≥ 2) | trades | **blind avg R** |
|---|---|---|---|---|---|---|---|---|
| 2023 | XAUUSD D1 control none | 1.60 | +0.289 | 62 | **-0.151** | 0 | 0 | **—** |
| 2024 | GBPUSD D1 control F3 | 1.02 | +0.124 | 28 | **-0.153** | 0 | 0 | **—** |
| 2025 | XAUUSD D1 control F3 | 1.11 | +0.163 | 29 | **-0.383** | 0 | 0 | **—** |
| 2026 | GBPUSD D1 control F3 | 0.95 | +0.094 | 24 | **+0.046** | 0 | 0 | **—** |

Pick A: blind average -0.165 over 143 trades, positive in 1 of 4 years -> **fail**. Pick B: no unit ever reached t ≥ 2 in training, so no trades -> **fail**.

## Combination search + SMT (1,955 units)

| Test year | Pick A (best past t) | past t | past avg | trades | **blind avg R** | Pick B units (t ≥ 2) | trades | **blind avg R** |
|---|---|---|---|---|---|---|---|---|
| 2023 | GBPUSD H4 c2_close +sweep_big+ny_sweep | 1.84 | +0.203 | 40 | **-0.112** | 0 | 0 | **—** |
| 2024 | GBPUSD H4 c2_close +sweep_mon+htf_ob | 2.34 | +0.411 | 17 | **-0.155** | 1 | 17 | **-0.155** |
| 2025 | XAUUSD H4 c2_close +c1_big+london_sweep | 2.31 | +0.326 | 47 | **+0.258** | 3 | 74 | **+0.178** |
| 2026 | XAUUSD H4 c2_close +c1_big+london_sweep | 2.59 | +0.304 | 26 | **-0.387** | 6 | 90 | **-0.103** |

Pick A: blind average -0.039 over 130 trades, positive in 1 of 4 years -> **fail**. Pick B: +0.007 over 181 trades, 1 of 4 -> **fail**.

## Edge hunt v3 (ATR units) (724 units)

| Test year | Pick A (best past t) | past t | past avg | trades | **blind avg R** | Pick B units (t ≥ 2) | trades | **blind avg R** |
|---|---|---|---|---|---|---|---|---|
| 2023 | B short 11:00 UTC for 1h EURUSD | 3.57 | +0.028 | 259 | **+0.011** | 6 | 1034 | **+0.005** |
| 2024 | B long 21:00 UTC for 3h EURUSD | 4.35 | +0.016 | 207 | **+0.005** | 9 | 1901 | **-0.005** |
| 2025 | B long 21:00 UTC for 3h EURUSD | 4.11 | +0.012 | 206 | **+0.029** | 7 | 1282 | **+0.031** |
| 2026 | B long 21:00 UTC for 3h EURUSD | 4.91 | +0.016 | 183 | **+0.013** | 9 | 1502 | **+0.014** |

Pick A: blind average +0.014 over 855 trades, positive in 4 of 4 years -> **PASS**. Pick B: +0.010 over 5719 trades, 3 of 4 -> **PASS**.

## v4 advanced models (36 units)

| Test year | Pick A (best past t) | past t | past avg | trades | **blind avg R** | Pick B units (t ≥ 2) | trades | **blind avg R** |
|---|---|---|---|---|---|---|---|---|
| 2023 | RTM1 H4 GBPUSD | 1.45 | +0.226 | 116 | **-0.212** | 0 | 0 | **—** |
| 2024 | RTM1 D1 GBPUSD | 1.10 | +0.335 | 28 | **-0.312** | 0 | 0 | **—** |
| 2025 | RTM1 D1 GBPUSD | 0.56 | +0.133 | 21 | **-0.438** | 0 | 0 | **—** |
| 2026 | rejection block D1 GBPUSD | 0.46 | +0.025 | 28 | **-0.250** | 0 | 0 | **—** |

Pick A: blind average -0.257 over 193 trades, positive in 0 of 4 years -> **fail**. Pick B: no unit ever reached t ≥ 2 in training, so no trades -> **fail**.

## v6 breakers (48 units)

| Test year | Pick A (best past t) | past t | past avg | trades | **blind avg R** | Pick B units (t ≥ 2) | trades | **blind avg R** |
|---|---|---|---|---|---|---|---|---|
| 2023 | A in CRT D1 confirm classic XAUUSD | 0.94 | +0.272 | 45 | **-0.317** | 0 | 0 | **—** |
| 2024 | A in CRT D1 confirm classic GBPUSD | 0.67 | +0.081 | 47 | **+0.065** | 0 | 0 | **—** |
| 2025 | A in CRT D1 mid classic XAUUSD | 0.69 | +0.133 | 44 | **-0.314** | 0 | 0 | **—** |
| 2026 | B standalone H1 confirm classic XAUUSD | 0.95 | +0.050 | 120 | **-0.145** | 0 | 0 | **—** |

Pick A: blind average -0.166 over 256 trades, positive in 1 of 4 years -> **fail**. Pick B: no unit ever reached t ≥ 2 in training, so no trades -> **fail**.

## v5 trend following (daily, signal re-chosen every year from all earlier years)

| Market | blind Sharpe 1981–2012 | **2013–2026** | 2021–2026 | last picks | Pass |
|---|---|---|---|---|---|
| portfolio | 0.60 | **-0.17** | -0.11 | 2021:W13, 2022:W13, 2023:W13, 2024:W13, 2025:W4, 2026:W4 | fail |
| GBPUSD | 0.20 | **-0.10** | -0.41 | 2021:W13, 2022:W13, 2023:W13, 2024:W13, 2025:W13, 2026:W13 | fail |
| XAUUSD | 0.42 | **0.29** | 0.51 | 2021:M12, 2022:M12, 2023:M12, 2024:M12, 2025:M12, 2026:M12 | fail |

## Summary

| Family | Units | Pick A blind avg | trades | years + | Pick B blind avg | trades | years + |
|---|---|---|---|---|---|---|---|
| v1.2 CRT variants | 2,986 | +0.105 | 104 | 2 | none qualified | 0 | 0 |
| Romeo v2 | 40 | -0.165 | 143 | 1 | none qualified | 0 | 0 |
| Combination search + SMT | 1,955 | -0.039 | 130 | 1 | +0.007 | 181 | 1 |
| Edge hunt v3 (ATR units) | 724 | +0.014 PASS | 855 | 4 | +0.010 PASS | 5719 | 3 |
| v4 advanced models | 36 | -0.257 | 193 | 0 | none qualified | 0 | 0 |
| v6 breakers | 48 | -0.166 | 256 | 1 | none qualified | 0 | 0 |

## Reading (written after the run)
- **Luck rate.** With no edge anywhere, a family still passes this walk-forward about **1 time in 8** (measured: 5 of 40 pure-noise runs, `tests/test_walkforward.py`). With 6 families, about one lucky pass is expected.
- **v1.2 CRT:** the best past variant (GBP/USD H4→M5, MSS trigger) faded year by year: +0.55, +0.15, −0.16, −0.05. Positive overall (+0.10R on 104 trades) but only 2 of 4 years. No variant ever reached t ≥ 2 in training. Fail.
- **Romeo v2, combination search + SMT, v4 models, breakers:** the past winner lost the next year in 3 or 4 of 4 years. Fail.
- **Trend:** the yearly re-chosen signal worked before 2013 (blind Sharpe 0.60) and not after (−0.17). Gold 0.29, below simply holding gold (0.45). Fail.
- **Edge hunt passes**, with EUR/USD "buy at 21:00 UTC, hold 3 hours", but this is very likely a **data artifact**, not an edge:
  - Our data is bid prices only. At the New York close (17:00 NY) spreads widen, so the bid dips and then recovers. Measured on 2021–2026 EUR/USD, Mon–Thu: the bid falls 1.3 pips into 17:01 NY and is back by 17:40.
  - "21:00 UTC" is 17:00 NY in summer, exactly at the dip. Split by season, the trade made +0.020 ATR when entered at 17:00 NY against +0.007 at 16:00 NY.
  - Real costs at that hour are higher than modelled: the ask is inflated during the widening, and a EUR/USD buy held through 17:00 NY pays swap. The whole gain is about 1 pip per trade, smaller than these costs.
  - It's EUR/USD, not one of Ore's pairs, and confirming it needs ask-price data or a demo test.

**Bottom line: no strategy family passes the walk-forward in a way that survives a costs check.**

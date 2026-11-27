# Spec v32: do more pairs help the prop plan? (written 27 Nov 2026, before the prop simulation was run)

Ore's question: "Does adding more pairs to trade like the EURUSD and silver help to have more trades... also check if
we can handle it."

## What is already known (so this is not a blind test)
The live-scanner replay (`backtest/replay_live.py --pairs EURUSD,XAGUSD --only ore_poi,irl_erl`, 1 Jun 2022 to
18 Nov 2026) was run before this spec was written. Its trade totals:

| pair | Ore's model | IRL/ERL |
|---|---|---|
| EUR/USD | 19 trades, +1.0R | 13 trades, +3.0R |
| silver | 8 trades, +12.0R | 16 trades, -4.0R |

The prop simulation below has **not** been run yet. Its rule is fixed here first.

## Test
- **Trades:** the prop plan, Ore's model + IRL/ERL, from the live-scanner replays.
  - GBP/USD + gold: `replay_2022_24.csv` + `replay_2025_26.csv`.
  - New pairs: their own replay.
  - Common window: 1 Jun 2022 to 18 Nov 2026.
- **Simulator:** `backtest/prop_sim.py`, with Equity Edge Swift rules and each pair's leverage:
  - 1:30 for FX, 1:10 for metals.
  - USD/JPY pays in yen, converted at the price.
- **Baskets:**
  - A = GBP/USD + gold (today's plan).
  - A + EUR/USD.
  - A + silver.
  - A + EUR/USD + silver.
  - Later, the same with USD/JPY and AUD/USD once their data is in.
- **Risk:** 1%, 1.5% and 2%.
- **Measures:**
  - Pass rate over challenges started every Monday (6-month horizon).
  - Week-block bootstrap pass rate (2,000 paths, 26 weeks).
  - Median days to pass.
  - Funded-stage average payout (6 months, payouts every 14 days).

## Adoption rule (per pair, whole pair, both strategies; no picking one strategy on one pair)
A pair is added to the prop plan only if all three hold:
1. Its own plan trades are net positive after spread over the window.
2. At 1.5% risk, A + that pair has a pass rate at least 3 points above A, and the bootstrap pass rate is not lower.
3. The funded average payout is not lower than A's.

If a pair passes, the live feed must also carry it inside the free Twelve Data limits (two keys, 800 credits a day
each). This is checked separately and reported. Passing here does not by itself put the pair live.

## Results
(appended after the run)
Run 27 Nov 2026 with `python -m backtest.more_pairs_v32` → `backtest/out/v32_more_pairs_EURUSD_XAGUSD.csv`.

### Trades in the window (Ore's model + IRL/ERL, filled, after spread)

| pair | trades | net R |
|---|---|---|
| GBP/USD | 26 | +14 |
| gold | 23 | +5 |
| EUR/USD | 32 | +4 |
| silver | 24 | +8 |

### Prop results (204 challenges, one started every Monday)

| basket | risk | trades | pass | fail (trailing) | still open at 6 months | bootstrap pass | funded avg paid | funded breached |
|---|---|---|---|---|---|---|---|---|
| A: GBP/USD + gold | 1% | 49 | 13.7% | 16.7% | 69.6% | 12.2% | $133 | 46% |
| A: GBP/USD + gold | **1.5%** | 49 | **31.9%** | 29.9% | 38.2% | **19.1%** | **$170** | 50% |
| A: GBP/USD + gold | 2% | 49 | 32.8% | 30.9% | 36.3% | 22.2% | $202 | 51% |
| A + EUR/USD | 1% | 81 | 23.5% | 27.0% | 49.5% | 17.7% | $131 | 57% |
| A + EUR/USD | **1.5%** | 81 | **36.3%** | 35.3% | 27.9% | **20.2%** | **$166** | 76% |
| A + EUR/USD | 2% | 81 | 22.1% | 46.1% | 26.0% | 23.2% | $172 | 82% |
| A + silver | 1% | 73 | 22.1% | 29.4% | 48.5% | 18.8% | $151 | 62% |
| A + silver | **1.5%** | 73 | **21.1%** | 61.3% | 17.6% | **23.7%** | **$192** | 89% |
| A + silver | 2% | 73 | 32.4% | 50.0% | 17.6% | 25.2% | $207 | 89% |
| A + EUR/USD + silver | 1% | 105 | 31.9% | 31.9% | 36.3% | 21.7% | $143 | 64% |
| A + EUR/USD + silver | **1.5%** | 105 | **33.8%** | 45.6% | 13.7% | **21.7%** | **$165** | 84% |
| A + EUR/USD + silver | 2% | 105 | 26.5% | 51.0% | 17.6% | 23.1% | $161 | 82% |

### Verdict against the rule (1.5% risk)

- **EUR/USD: not added.**
  - Rule 1 holds: +4R.
  - Rule 2 holds: pass rate up 4.4 points, bootstrap up 1.1.
  - Rule 3 fails: funded payout $166 against $170.
- **Silver: not added.**
  - Rule 1 holds: +8R.
  - Rule 2 fails: pass rate down 10.8 points.
- **Both together: not added.** Rule 2 fails: pass rate up only 1.9 points.

**The prop plan stays on GBP/USD + gold.**

### What the numbers say
More pairs bring more trades, and challenges finish sooner: "still open" drops from 38% to 14–28%. They also fail on
the 5% trailing limit far more often: 30% of starts with two pairs, 35–61% with three or four. In the funded stage the
breach rate rises from 50% to 76–89%.

The extra pairs often trade at the same time as GBP/USD and gold, so their losses land on the same days. Because the
trailing limit is only 5%, more trades at once makes a breach more likely, not a pass. The bootstrap pass rate rises a
little with more pairs, but the week-by-week real history, which keeps those same-day clusters together, does not.

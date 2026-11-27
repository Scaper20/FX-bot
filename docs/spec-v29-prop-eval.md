# Spec v29: a plan for passing the prop challenge (27 Nov 2026)

Ore bought a challenge: **5K, 1-Step "Swift", $19.** Phase 1: no time limit, minimum 2 trading days, maximum daily
loss 3%, maximum loss 5% trailing, profit target 8%, MT5 / Match-Trader, leverage up to 1:30. Funded: daily 3%,
trailing 5%, minimum 1 day. Goal: pass consistently; later, maybe monetise.

## Method (`backtest/prop_sim.py`)
The live scanner's own trade record (replays of the live scanner, `backtest/replay_live.py`: fills, exits and R
after Ore's spreads, overlapping trades included) is played through the challenge rules:
- balance $5,000; pass = balance >= $5,400 with at least 2 trading days and no open trade;
- fail = the day's closed P&L reaches -3% ($150) of the starting balance, or balance falls 5% ($250) below its
  highest closed balance (trailing; variant: trailing stops at the starting balance);
- a challenge starts every Monday of the record; horizon 26 weeks (the firm has no time limit; longer is "still open");
- plus a week-block bootstrap: 600 random 26-week paths made from shuffled real weeks.
Compared: risk per trade 0.25% – 2%, strategy sets (all six, CRT only, the five smart-money strategies, Ore's model +
IRL/ERL + Lingard), with and without a "no new trades after -1.5% on the day" stop.

## Equity Edge rules (official help centre, "Trading Rules and Guidelines", read 27 Nov 2026)
- Daily loss 3% from the balance at the reset, **reset 22:00 London time**; closed P&L, swaps and commissions count.
- Maximum loss 5% **trailing the highest balance or equity** (section 1; section 12 says the high is from closed
  trades): simulated as the stricter equity version (each trade's best point lifts the high). No lock at the start.
- Target 8% of the starting balance; minimum 2 trading days; unlimited time; manual review within 3 working days.
- Leverage 1:30 FX, **1:10 metals** (caps gold size on $5K: ~0.14 lots); simulated with margin for open trades.
- **No hedging** (simulated: skip a trade opposite an open one on the same pair). No EAs, copiers, signal bots or trade
  management services: Ore places every trade by hand. No martingale.
- **News: no opening or closing within 2 minutes either side of high-impact news** (USD news: all pairs). Funded: profit
  from such trades is removed; news profit over 25% of the profit share voids the payout. Not simulated (no calendar).
- Weekend holding allowed; no consistency rule; no inactivity rule; funded payouts 80% every 14 days.

## Assumptions still open
Whether floating losses count toward the daily limit (simulated: closed P&L only); commissions (not included);
which of the two trailing definitions applies (simulated: the stricter one).

## How results are read
This is a plan, not a rule test: the trade record is the same 2022-2026 replay the strategies were judged on. The
pass rate is mostly set by risk size and luck when the average trade is near 0R, so the result is read together
with the fee per pass ($19 / pass rate) and the failure mix.

## Results (27 Nov 2026; `python -m backtest.prop_sim <replays> --candles <dir> --only N`; 659 live-scanner trades,
June 2022 – Nov 2026; Equity Edge rules as above; challenges started every Monday)

| Plan | Pass ≤ 6 months | Shuffled-history pass ≤ 12 m | Median days to pass | Funded payout (avg, 6 m) | Value of a $19 attempt |
|---|---|---|---|---|---|
| **Ore's model + IRL/ERL, 1.5% risk** | **31%** | 24% | 93 | $170 | **+$34** |
| Ore's model + IRL/ERL, 2% | 32% | 26% | 87 | $201 | +$46 |
| Ore's model + IRL/ERL, 1% | 13% | 21% | 98 | $133 | −$1 |
| Ore's model + IRL/ERL + Lingard, 1.5% | 28% | 22% | 72 | $130 | +$18 |
| Smart-money five, 2% | 16% | 14% | 15 | $46 | −$12 |
| CRT only, 2% (taper) | 12% | 11% | 11 | $51 | −$13 |
| All six, 1% | 10% | 10% | 10 | $47 | −$15 |

- Below ~1% risk the challenge rarely finishes: Ore's model + IRL/ERL give ~11 trades a year, and 8% at 0.5% risk
  needs ~16R of net profit (years).
- The risk rules (daily stop 1.5%, halve after −2.5%, taper near target) moved pass rates by 0–2 points.
- Gold at 1:10 leverage: at 1% risk 58% of gold CRT trades must be cut in size and one tight-stop gold trade can use
  nearly all the margin; one more reason not to run CRT on this account.

**Caveats.** Ore's model + IRL/ERL is ~49 trades in 4.5 years (+0.29R and +0.52R a trade) and both were chosen because
their backtests looked best, so this plan rests on a small, selected sample; its positive value is not proven.
News windows (no fills or exits within 2 minutes of high-impact news) and commissions are not simulated.

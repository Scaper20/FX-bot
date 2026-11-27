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

## Assumptions to confirm with the firm (unknown today)
Daily loss counted on balance or on equity (including open trades), and when the firm's day resets; whether the
trailing maximum loss follows balance or equity and whether it stops at the starting balance; consistency rules;
news and weekend holding; commissions; payout split and schedule. The simulation uses closed balance, a 00:00 UTC
day and a floor that keeps trailing. Equity-based rules are stricter than these numbers.

## How results are read
This is a plan, not a rule test: the trade record is the same 2022-2026 replay the strategies were judged on. The
pass rate is mostly set by risk size and luck when the average trade is near 0R, so the result is read together
with the fee per pass ($19 / pass rate) and the failure mix.

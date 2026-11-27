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

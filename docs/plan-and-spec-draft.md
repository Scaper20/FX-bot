# CRT + ICT + MSnR setup scanner — Step 1 to 3 report and build plan

## Context
Ore wants a personal site that shows the best current GBP/USD or XAU/USD setup matching his written CRT + ICT + MSnR rules, with the pattern's historical results. Nothing is built yet. This plan reports on the data, sets out the strategy spec (with open questions), picks the engine language and lays out the build order. **No code until Ore approves this and answers the spec questions.**

Confirmed by Ore today: GU = GBP/USD. Gold = **spot XAU/USD** (not futures).

---

## Step 1 — Data report

| | Gold file | GBP/USD file |
|---|---|---|
| File | `GOLD_GC-F_COMEX_futures_daily_...csv` | `GBPUSD_daily_...csv` |
| Format | CSV: Date, Open, High, Low, Close, Volume | CSV: Date, Open, High, Low, Close (no volume) |
| Timeframe | **Daily only** | **Daily only** |
| Range | 19 Nov 2021 to 18 Nov 2026, 1,257 rows | 19 Nov 2021 to 18 Nov 2026, 1,299 rows |
| Instrument | **COMEX gold futures (GC=F)**, not spot | GBP/USD (looks like the Yahoo "GBPUSD=X" feed) |
| Timezone | None stated. Dates follow the CME trading day | None stated. Probably the UTC/London calendar day |
| Gaps | 47 missing weekdays, all US exchange holidays. No other gaps | 5 missing weekdays (New Year, Good Friday/Easter Monday 2025, Christmas 2025) |
| Bad rows | 8 days with volume 0; same volume repeated on 4 pairs of days (incl. the last two rows, so the last row is likely incomplete). Big ranges in Jan–Mar 2026 (up to 14.7% in a day) look like real moves, not errors | **Close column is broken:** on 94% of days Close is within 5% of the day's range from Open (real data: about 5–10%). 23 rows have Close above High or below Low. 22–30 Sep 2022 gaps are real (mini-budget crash) |

**Verdict: neither file can be used for the backtest.**
1. The strategy needs H4, H1, M15 and M5. Both files are daily only.
2. GBP/USD closes are wrong. CRT ("close back inside") and MSnR (levels from closes) depend on closes.
3. Gold is futures. Ore trades spot; futures sit about $10–40 above spot and jump at each contract roll.
4. Neither file uses a broker-style daily candle (most brokers close the day at 17:00 New York).

**Replacement data:** Dukascopy free 1-minute history for GBPUSD and XAUUSD (spot), 2021 to 2026, turned into all timeframes. A download from this cloud server was refused by Dukascopy (HTTP 429 on the first request: they block this server). Next try: Ore runs one download command on his PC (I'll give the exact command after approval, e.g. the `dukascopy-node` tool, writes CSV to a folder he uploads). If that also fails, Ore supplies intraday files himself.

Other data notes:
- `TWELVEDATA_API_KEY` is **not set in this cloud session**. Needed only for the scanner step; Ore adds it as an environment secret then. XAU/USD on the free plan still unchecked.
- Dukascopy vs Twelve Data vs Ore's broker price gap: to be measured once both feeds are in hand, and shown on the site.

---

## Step 2 — Strategy spec (draft, one page)

Status: **Yes** = already decided in CLAUDE.md. **Ans** = needs Ore's answer. Nothing here is my own trading idea.

### A. General
| # | Rule | Status |
|---|---|---|
| A1 | Pairs GBP/USD, spot XAU/USD | Yes |
| A2 | Range TF D1 and H4; entry TF H1, M15, M5 | Yes |
| A3 | Minimum reward:risk 1:3, below it not shown | Yes |
| A4 | Daily candle close time | **Ans Q1** |
| A5 | Which entry TF pairs with which range TF | **Ans Q2** |

### B. CRT
| # | Rule | Status |
|---|---|---|
| B1 | Range = high, low, 50% of a completed range-TF candle | Yes |
| B2 | Sweep = later candle trades beyond one side and closes back inside | Yes (generic) |
| B3 | Which candle may sweep: only the very next one, or any within N candles? | **Ans Q3** |
| B4 | "Closes back inside": close inside the range, or past the 50%? Min sweep size? | **Ans Q4** |
| B5 | Range candle filters (min/max size, inside bars, etc.) | **Ans Q5** |
| B6 | Stop: beyond sweep extreme, plus what buffer? | **Ans Q6** |
| B7 | Targets: 50% then opposite side — which one counts for the 1:3 check? Partial closes? Move stop to breakeven? | **Ans Q7** |
| B8 | When does an unfilled idea expire? | **Ans Q8** |

### C. ICT (entry trigger)
| # | Rule | Status |
|---|---|---|
| C1 | Which of FVG, order block, market structure shift, killzone are **mandatory** vs **score only** | **Ans Q9** |
| C2 | Exact definitions you use (FVG = 3-candle gap? MSS = close beyond last swing — which swing size?) | **Ans Q10** |
| C3 | Entry price: FVG edge, FVG 50%, OB open, or market on trigger close? | **Ans Q11** |

### D. MSnR
| # | Rule | Status |
|---|---|---|
| D1 | A-level, V-level, gap level from candle closes | Yes (generic) |
| D2 | Fresh until wick touch; body close through makes it fresh again | Yes (generic) |
| D3 | Exact A/V definition (close of which candle, how many candles each side) and gap level definition | **Ans Q12** |
| D4 | Which TF the levels come from, and how far back | **Ans Q13** |
| D5 | Storyline (direction): how you decide it, which TF | **Ans Q14** |
| D6 | How near counts as "at a level" (pips / $) | **Ans Q15** |

### E. How they combine
| # | Rule | Status |
|---|---|---|
| E1 | CRT finds the idea, MSnR confluence, ICT entry trigger | Proposed — **Ans Q16** |
| E2 | Is MSnR level confluence mandatory or score only? Is MSnR target used instead of CRT target? | **Ans Q16** |
| E3 | Ranking when several setups qualify | Proposed: by historical after-cost average R of that exact pattern, sample size shown — **Ans Q17** |

### F. Costs and simulation
| # | Rule | Status |
|---|---|---|
| F1 | Limit entry; stop first if both hit in one candle; only stop checked on fill candle; cancel unfilled after N candles | Yes |
| F2 | Cost assumption per trade (spread + slippage) | **Ans Q18** (my default proposal: GBP/USD 1.0 pip, XAU/USD $0.40, stated on the site) |
| F3 | Sessions: all; any "best session" only from 2021–24 evidence, checked on 2025–26 | Yes |

### Plain questions for Ore
1. Which broker or chart platform do you use? (Sets the daily close time; most use 17:00 New York.)
2. D1 range → which entry TFs? H4 range → which entry TFs? (e.g. D1→H1/M15, H4→M15/M5)
3. Must the sweep happen on the very next candle after the range candle, or can it be any of the next few? How many?
4. After the sweep, where must the candle close: anywhere inside the range, or beyond the 50%? Is there a minimum sweep size?
5. Do you skip any range candles (too small, too big, inside bars, news days)?
6. How far beyond the sweep high/low do you put the stop?
7. Which target do you use for the 1:3 check — 50%, opposite side, or the next fresh MSnR level? Do you take partials or move to breakeven?
8. If the trigger hasn't come by when, do you drop the idea?
9. For ICT, which are must-haves and which just add confidence: FVG, order block, market structure shift, killzone time?
10. How do you define each of those exactly? (A screenshot of a real trade with notes is the fastest way.)
11. Where exactly do you enter?
12. How do you mark A-levels, V-levels and gap levels — which candle's close, and what makes it a peak/valley?
13. Which timeframe do your MSnR levels come from, and how far back do you look?
14. How do you read the storyline (direction)?
15. How close to a level counts as "at" it?
16. Is "sweep at a fresh MSnR level" required, or a bonus? Same for the MSnR target.
17. OK to rank setups by measured after-cost average R, sample size always shown?
18. What spread do you usually pay on GBP/USD and gold?

---

## Step 3 — Language and repo structure

**One language for the engine: Python.**
- You already run Python 3.13, the earlier prototype (replay, journal, Twelve Data client) is Python, and pandas makes the backtest fast to build and check.
- The same `engine/` package runs in the backtest and in the live scanner; the scanner just feeds it one new closed candle at a time.
- The website (Next.js) only reads results from the database; it never contains trading rules, so there is no second copy of the logic.

Scanner scheduler: **GitHub Actions scheduled job** (free; runs every 5 minutes at most and can start a few minutes late — fine for H1/M15, borderline for M5; I'll report the real delays). Vercel's free cron runs only once a day, so it is not used for scanning.

```
crt-scanner/
  engine/            # the rules — the ONLY place rules live
    candles.py       # load, clean, resample M1 -> M5..D1, daily close time, DST
    sessions.py      # sessions in UTC with London/NY DST
    crt.py  ict.py  msnr.py  combine.py
    simulate.py      # fill/stop/target conventions + costs
  backtest/
    run.py           # walks candles one at a time; writes trades + stats
    noise_check.py   # random-price check
    reports/         # generated, not hand-edited
  scanner/
    feed_twelvedata.py  # cache + daily credit budget, key from env only
    scan.py             # called by the schedule; arms setups, logs shown setups
  web/               # Next.js site (reads Supabase)
  db/migrations/     # Supabase tables: setups_shown, armed, outcomes, pattern_stats
  data/raw/ (git-ignored)  data/clean/ (git-ignored)
  tests/             # incl. look-ahead test and noise test
  .github/workflows/scan.yml
  CLAUDE.md
```
Data split enforced in code: `backtest/run.py` refuses 2025–2026 unless run with `--final-test`, and that run is logged; a second final run prints "test contaminated".

---

## Step 4 — Build order after approval (each step tested, results reported)
1. **Data:** get Dukascopy M1 (Ore's PC if needed), clean, build M5–D1 with the agreed daily close, report gaps. Tests: resample correctness, DST.
2. **Engine + backtester** on 2021–2024 only, with Ore's approved rules. Tests: no look-ahead (results unchanged when future candles are deleted), fill conventions, noise check. Report trades, win rate with count, avg R, total R, worst losing run, drawdown, after costs.
3. **Final test** on 2025–2026, run once, with Ore's go-ahead.
4. **Scanner:** Twelve Data feed (check XAU/USD on the free plan first), credit budget, armed setups, GitHub Actions schedule.
5. **Website:** "Find me a setup", setup card, armed list, history, Version B design, text version of every chart.
6. **Forward log:** every shown setup saved before its outcome, scored later.

## Verification
- Every step ends with tests run and a short "what ran on real data / what didn't" note.
- Backtest numbers are only quoted from an actual run, with sample size and date range.

## Update CLAUDE.md (after approval)
Decisions: GU = GBP/USD; Gold = spot XAU/USD; Python engine; GitHub Actions scanner; supplied daily files rejected (reasons above). Open items: intraday data source, daily close time, spec answers Q1–Q18, Twelve Data key in this environment.

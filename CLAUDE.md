# Project context: CRT + ICT + MSnR setup scanner (personal website)

Read this whole file before doing anything. Update the "Decisions" and "Open items" sections as things get settled.

## 1. Who and what
- Owner: Ore, entrepreneur in Lagos (UTC+1, no daylight saving). Works alone on this. Windows PC, PowerShell, Python 3.13 installed.
- Goal: a website where Ore clicks "Find me a setup" and it shows the best current trade setup that matches his written strategy rules, with levels, a chart and the historical results of that exact pattern.
- Use: **for Ore only for now.** It may become public if the results are good. Build so that going public later is possible, but do not build accounts, payments or marketing now.
- Not auto-trading. The site never places orders.

## 2. Scope (decided by Ore, 19 Nov 2026)
- Instruments: **GU** and **Gold**. I read GU as GBP/USD and Gold as XAU/USD. **Confirm both with Ore before coding.**
- Range timeframes (where the CRT range candle comes from): **D1 and H4**.
- Entry timeframes: **H1, M15, M5**.
- Sessions: any (Asia, London, New York and overlaps). Narrow to the best sessions only from backtest evidence, and only if the sample sizes are big enough to trust.
- Minimum reward to risk: **1 : 3**. Setups below it are not shown.
- Ore wants "the highest win rate". Nobody can promise that. The site ranks setups by measured historical performance of that pattern, always showing sample size and date range.

## 3. The strategy (RULES NOT YET SUPPLIED)
Three methods combined. Ore has not yet written down his exact rules. **Do not invent them and do not code final rules until Ore approves a written spec.**

- **CRT (Candle Range Theory, as taught by Romeo TPT):** a completed higher-timeframe candle sets the range (its high, low, 50% midpoint). A later candle trades beyond one side (the sweep) and closes back inside. Entry is timed on a lower timeframe. Stop goes beyond the sweep extreme. Targets are usually the 50% level, then the opposite side of the range.
- **ICT:** concepts used to time the entry, such as fair value gap, order block, market structure shift, killzones. Ore must say which are mandatory and which only add to the score.
- **MSnR (Malaysian Support and Resistance):** levels are single prices taken from candle closes: A-levels (peaks), V-levels (valleys) and gap levels. A level is fresh until a wick touches it; a body close through an unfresh level makes it fresh again. A higher-timeframe "storyline" gives direction; first revisits of fresh levels are the trade; the next fresh level is the target.
- **Proposed way to combine (Ore to confirm or change):** CRT finds the idea. MSnR supplies confluence (the sweep or entry sits at a fresh level; the target is the next fresh level). ICT supplies the lower-timeframe entry trigger.
- Sources used for the generic definitions above: LuxAlgo library pages on Candle Range Theory and Malaysian SnR, and an MQL5 blog post on CRT. They state that these methods are taught rather than published, that details vary by teacher, and that no independent test of results exists. Treat them as a draft only.
- Define sessions in UTC and handle daylight saving explicitly (London and New York shift). Never hardcode local hours.

## 4. Data
- Ore has **GU and Gold candle data for 2021 to 2026** as files. Format, timeframes, timezone and gaps are **unknown**. First job: inspect them and report.
- Ore has a **Twelve Data API key** (free plan, around 800 credits a day and a few calls a minute, check current limits). Used for the live feed. Verify that XAU/USD is available on the free plan before designing around it.
- The key lives in an environment variable and **never** goes in the code, the repo or a message.
- Prices differ between brokers and data providers, especially gold. The backtest data and the live feed may not match exactly. Check how far apart they are and say so on the site.
- Spread and slippage matter more on gold and on M5. Backtests must include a cost assumption, stated openly.
- Scanning must save credits: check H4 and D1 when they close, and poll the entry timeframes only while a range setup is "armed" (waiting for the entry trigger).

## 5. Backtesting rules (non-negotiable)
- No look-ahead. Step through candles one closed candle at a time; the engine only sees the past.
- Keep a test period the rules never see. Suggested: design and tune on 2021 to 2024, then run **once** on 2025 to 2026 untouched. If the rules are changed after seeing the final test, say that the test is now contaminated.
- Report win rate **with the number of trades**, average R, total R, worst losing run and drawdown. A win rate on 20 trades means almost nothing.
- Breakeven win rate at 1 : 3 is 25% before costs. Costs push it higher. Show the result after costs.
- Slicing by session, pair and timeframe gives many small groups. Treat any "best session" as a hypothesis until it holds on the untouched period.
- Simulation conventions from the earlier prototype (keep unless Ore changes them): limit entry; if stop and target are both inside one candle, assume the stop hit first; on the candle that fills the order only the stop is checked; orders not filled within a set number of candles are cancelled and counted separately.
- Random-noise check: run the rules on random price series. If they find "setups" at a high rate on noise, the rules are too loose.

## 6. Product
- Main action: **Find me a setup** shows the best current setup, or says "nothing qualifies right now" (an honest answer is a feature).
- A setup card shows: pair, direction, the range candle, the sweep, the entry-timeframe trigger, entry/stop/target, reward to risk (at least 1 : 3), a checklist of which CRT, ICT and MSnR conditions are met, the historical stats for this pattern (sample size and date range), and a chart.
- Also: a list of "armed" setups that are waiting for their trigger, a history log of every setup shown, and its later outcome.
- **Log every setup at the moment it is shown, before the outcome is known**, then score it later. This forward record is the real test, more than the backtest.
- Wording: "setup that matches these rules, with its historical results". Never "guaranteed", "sure", "high-probability" without the number beside it, and never buy/sell commands.
- Design: reuse the light "Version B" look from the earlier mock. Ink #0F1B2D on #F2F4F7, white cards, verdict colours green #0B7A5A, amber #D99A1E, coral #C8473B. Fonts Instrument Sans, Instrument Serif for large headings, JetBrains Mono for numbers. Mobile first. Provide a text equivalent for every chart.

## 7. Technical direction (proposal, confirm before building)
- Website: Next.js on Vercel. Database: Supabase Postgres. Both free tiers are enough for personal use.
- Scanner: a scheduled job that runs at candle closes. Vercel's free tier limits how often cron jobs can run; check current limits. Alternatives: GitHub Actions scheduled runs, or Supabase scheduled functions.
- The rule engine and backtester can be Python or TypeScript. Prefer one language for the engine so the backtest and the live scanner run **the same code**. Decide this explicitly.
- Free-tier and data licences to check before any public launch: Vercel's free tier may restrict commercial use; Twelve Data's terms for redistribution; any historical data source's terms.

## 8. Existing prototype (reusable ideas)
An earlier Python prototype, "Preflight bot v0.2" (Telegram bot for a different strategy, sweep + order block), was built and tested with 58 passing tests. Ore dropped Telegram. Ideas worth reusing, not necessarily the code:
- Candle feed with a Twelve Data client, a short cache and a daily call budget.
- `replay.py`: walks real candles one at a time, saves a chart for each setup, scores each with the simulation conventions above.
- A journal that logs every verdict when given and scores it later.
- Annotated chart rendering.
- Lesson: on random noise the old rules said VALID about 0.1% of the time; the test suite included a noise check.
- Known unresolved: the first Twelve Data download from Ore's PC failed with a vague error; the error handling was changed to show the provider's message. Cause never found.

## 9. Ways of working
- Strategy before execution: spec first, code second. Ore's habits: low cost first, progressive disclosure (simple first, detail on request), proof before personalisation.
- Plain English. Short explanations. Say what you did and what is untested.
- Small steps, each tested. Say clearly what has and has not been run on real data.
- Ask when a rule is ambiguous. Do not fill gaps with your own trading ideas.
- No secrets in files or logs.
- Do not claim a result you have not run.

## 10. Decisions
- 19 Nov 2026: personal site first, public only if results justify it. GU and Gold. D1/H4 range, H1/M15/M5 entry, minimum 1 : 3.
- Telegram bot dropped.
- 19 Nov 2026: GU = GBP/USD. Gold = **spot XAU/USD** (Ore trades spot, not futures).
- 19 Nov 2026: the supplied daily files are **not used** for backtesting. Both are daily only (strategy needs H4 to M5); the GBP/USD close column is broken (94% of days close almost at the open, 23 rows close outside high/low); the gold file is COMEX futures (GC=F), not spot. Full report: `docs/plan-and-spec-draft.md`.
- 19 Nov 2026: intraday source = Dukascopy 1-minute candles, all timeframes built from them. Dukascopy refuses downloads from the cloud server (HTTP 429), so Ore downloads on his PC (`docs/get-data.md`). If that fails, Ore supplies intraday files.
- 19 Nov 2026: engine language **Python** (backtest and scanner share `engine/`). Website Next.js reads the database only, no rules in it. Scanner scheduler: GitHub Actions (Vercel free cron is once a day).
- 19 Nov 2026: spec draft with 18 questions approved as the plan.
- 19 Nov 2026: Ore pushed Dukascopy M1 bid data (GBPUSD, XAUUSD, 1 Nov 2021 to 18 Nov 2026) into `data/`. Checked: no duplicates or bad rows, gaps are holidays and gold's daily break; my D1 build matches his 2023+ D1 pack exactly. Data stays in the repo (Ore's choice).
- 20 Nov 2026: Ore answered the questions. Broker Exness MT5. Wants many variants tested, several setups shown at once, entry options ranked, and Claude free to research and improve. Knows no MSnR: treat as experimental. Rules written up in `docs/spec-v1.md`.
- 20 Nov 2026: Ore approved spec v1, confirmed Exness server = GMT+0 (Sunday candle seen), account Exness Standard. Added HTF confluences (sweep into older HTF OB/FVG, HTF MSS) as spec v1.1.
- 20 Nov 2026: v1.1 engine built (`engine/setups.py`), 30 tests pass. Design-period backtest (Nov 2021 to Dec 2023): **no edge** — best of 3,644 eligible variants t = 1.61, no better than random direction, rules fire as often on shuffled noise. Report: `backtest/reports/design_v1.md`. Check period (2024) deliberately not run yet.
- 20 Nov 2026: Ore's chart feedback -> spec v1.2 (London/NY sessions, trade with daily direction or against only with HTF OB/FVG on the left, sweep-size limits, spread-aware stops, no Friday-late entries), pre-registered in `docs/spec-v1.2.md`. Design best: GBPUSD London +0.27 R (144 setups); gold 0/32 positive. **2024 Check run once: 1 of 11 finalists passed (likely luck); GBPUSD London filter -0.31 R in 2024.** Sessions filter helps consistently but results stay negative. **2024 has now been used once for v1.2.** Report: `backtest/reports/v12_report.md`.
- 20 Nov 2026: Ore chose assisted mode: the system recommends, Ore decides; forward journal + reviews. Diagnosis (`backtest/reports/diagnosis.md`): the CRT premise itself hits targets at the chance rate (risk/(risk+reward)) in every subset, including in-candle (turtle soup) entries; losses = spread + 1:3 rule selecting weak rejections + limit-order adverse selection. Spec v1.3 (`docs/spec-v1.3.md`): Ore's rules decide what is recommended; every option shows chance and break-even win rates and its 2021-2024 history (shrunk ranking); practice mode on 2021-2024 setups; Performance compares Ore's picks to chance.

## 11. Open items
- [ ] Ore's real Exness Standard spreads (costs are ~0.25 R per trade, decisive).
- [x] 20 Nov 2026: live at https://fxbot-ochre.vercel.app (Vercel, deployed by Ore). Database: Supabase project ltzcwwtnfmiembysuzie (Ore's new org), schema 001 + schedule 002 applied by Claude. Forced test scan through pg_cron route: OK, both pairs fetched, 6 credits. XAU/USD works on the Twelve Data free plan.
- 20 Nov 2026: Ore's idea: public practice for other traders at `/p` (username only, no password). Separate tables `community_users`/`community_reviews` (migration 003, applied), never mixed with Ore's data; per-trader shuffled order; one answer per trader per setup; 200/day limit; outcomes only after answering; Ore's Performance page shows each trader vs chance. Usernames are not authentication.
- [ ] Optional: revoke anon/authenticated EXECUTE on Supabase-created `public.rls_auto_enable()` (security advisor warning; not our code; awaiting Ore).
- [ ] Ore: real Exness Standard spreads into Settings; reviews (live + practice) to measure his judgment.
- [ ] Confirm XAU/USD works on the Twelve Data free plan, and the live-versus-historical price gap. Key is not yet set in the cloud session.
- [ ] Before going public: legal opinion (Nigeria SEC draft rules on online forex and CFD trading are not yet in force but could cover this), data and hosting licence checks, wording review.

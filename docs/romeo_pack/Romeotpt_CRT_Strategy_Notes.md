# Romeotpt CRT (Candle Range Theory) + Turtle Soup — Strategy Notes for a Trading Bot

Compiled 20 Nov 2026 from Romeotpt's own YouTube lectures (CRT Secrets ep. 1–10, CRTology Intro + ep. 1–4, "What is CRT?", "What is turtle soup?"). Source list at the bottom.

> **Read first.** These notes paraphrase his public teaching. Several parts he says he keeps for paid material (picking the correct key level, full time theory, market profiling, the "6 candle shapes"), so those sections are thin; Section 14 lists them. His accuracy figures (80–90%) and "$1M bounty" are his own claims and nobody has checked them. Backtest every rule before risking money. This is not financial advice.

---

## 0. The whole system in one paragraph

Every candle is a range. The next candle either **breaks out** of that range (closes beyond it, so continuation) or **turtle-soups** it (wicks beyond it and closes back inside, so reversal). Pick a higher-timeframe (HTF) candle, decide its bias from how it relates to the previous candle and to a **key level**, then go to a lower timeframe (LTF) and wait for the price to run an old high or low at the key level (turtle soup) and confirm it (**Model #1** or a **true market structure shift**). Enter, put the stop past the turtle-soup extreme, and target **50% of the CRT range** first and then the **opposite end of the range**. Time matters more than price: most weekly highs and lows form Mon–Wed, and the action window is NY midnight to 4pm NY.

Core mantra: **"Open → (key level / old high-low) → turtle soup → expansion."**
- Bearish: open, rally above the open into a key level or old high, turtle soup, then decline.
- Bullish: open, drop below the open into a key level or old low, turtle soup, then rally.

---

## 1. Definitions / terminology

| Term | Meaning |
|---|---|
| **CRT** | Candle Range Theory. Every candle (monthly, weekly, daily, 4H…) is a range with open, high, low and close. |
| **Candle 1 (C1)** | The range candle (accumulation). Its high and low are the CRT High and CRT Low. |
| **Candle 2 (C2)** | Manipulation. Wicks beyond one side of C1 (turtle soup) and closes back inside. |
| **Candle 3 (C3)** | Distribution/expansion. Moves toward the opposite side of C1. Usually the fastest, cleanest move. |
| **CRTH / CRTL** | CRT High / CRT Low. The high and low of the specific range you expect to be turtle-souped (not just any arbitrary high or low). |
| **+ / − target** | Bullish target (upside) / bearish target (downside). |
| **Turtle Soup (TS)** | A false breakout or breakdown: price stabs past an old high or low (taking the stops and luring breakout traders), then reverses. **+TS** = bullish (stab below an old low). **−TS** = bearish (stab above an old high). He treats CRT, turtle soup, liquidity sweep and stop hunt as the same thing. |
| **Kiss of Death Turtle Soup (KOD TS)** | The **last** turtle soup before the target is hit. Price is pushed above an engineered liquidity pool (bearish case) to stop out shorts and lure longs, then dumps fast into the target. Usually forms after the price has already hit 50% and bounced. Often coincides with the OTE. Prefers it in the lower 25% of the range (bearish case). |
| **Model #1 (M1)** | His core entry. **Bearish:** one thick **up-close** candle stabs above an old high, and a later candle **closes below that candle's low (body)**, which is the trigger. **Bullish:** one thick **down-close** candle stabs below an old low, and a later candle **closes above that candle's high**. It is one specific candle, not a zone. |
| **RTM1** | Retrade into Model #1. Price comes back into the M1 candle before continuing. −RTM1 = bullish retrade into a bearish M1. +RTM1 = bearish retrade into a bullish M1. |
| **True MSS** | True market structure shift. **Bullish:** low → high → lower low (the turtle soup at a key level) → **close above the high that broke the low**. **Bearish:** mirror image. It must come from a key level at the right time. |
| **FMSS** | Fake market structure shift. An MSS printed in the wrong place. A **bearish** MSS printed at a **discount** (after a big drop) is really a bullish turtle soup. A **bullish** MSS printed at a **premium** is really a bearish turtle soup. Market makers do not buy at a premium or sell at a discount. |
| **OTE** | Optimal trade entry, in his own definition. It is not a Fib level. It is the deep retracement after a true MSS that comes from a key level, designed to shake everyone out before **leg 2** of the expansion. Activated only after a **candle close** through the swing that formed the MSS (a wick does not count). He prefers a "wave" of breaks through that level, then a sharp retrace. |
| **Failure Swing (FS)** | Same idea as the OTE, named from the retrace side. **+FS** = deep bearish retrace after a bullish true MSS. **−FS** = deep bullish retrace (to 50% or beyond) after a bearish true MSS. "Every turtle soup has a failure swing." |
| **Key level** | A price where you expect a bounce: either a counter-trend reaction or the actual high or low of the candle. Usually an HTF level. Examples he shows: old highs and lows, the open of a down-close candle (support) or up-close candle (resistance), 50% of a weekly wick, FVGs. **Key levels produce LTF expansions** (monthly KL → weekly expansion, weekly KL → daily, daily KL → 4H, 4H KL → 1H/15m). |
| **Rejection block** | A turtle soup of the candle **bodies**. It usually causes a retracement before the high (or low) target is attacked. |
| **SMT** | Smart money technique (divergence). One correlated asset takes a high or low and the other does not, which shows weakness and is a "signal". |
| **WOP / DOP** | Weekly / daily opening **price**. |
| **WOT / WCT** | Weekly opening time = **Monday 00:00 New York**. Weekly closing time = **Friday 16:00 NY**. |
| **DOT / DCT** | Daily opening time = **00:00 NY**. Daily close ≈ **16:00 NY**. |
| **50%** | 50% of the CRT candle range. This is **Target 1** for every CRT. |

---

## 2. Timeframes: which candle you trade and how to pair them

- **First question before any trade: "Which candle am I trading?"** He calls himself a candle trader, not a zone or pattern trader.
- Allowed candles: **Weekly, Daily, 4H** (beginner: start with one of these). Advanced traders can use Monthly/3M/6M/12M. 1H is allowed only for "hyper-scalpers".
- His preference: mostly **daily and 4H ranges**, and a clean weekly range when one appears.
- **HTF candle → LTF entry pairings ("golden rule"):**
  - Monthly candle → Daily (or 4H) entry
  - Weekly candle → 4H (or 1H) entry
  - Daily candle → 1H (or 15m) entry
  - 4H candle → 15m / 5m entry
- Two-dimension analysis: **HTF candle shape = bias. LTF candle anatomy/slope = entry.**
- Price is fractal. A monthly candle is a 1H candle printing more slowly, so you can study the LTF to get practice faster. **Analyse** the LTF a lot, but don't **trade** it.
- There is no fixed timeframe alignment sequence; each timeframe prints at its own pace.

---

## 3. Bias rules (direction of the next candle)

Compare the **just-closed candle** with the **candle before it**:

| Relationship | Expectation for the NEXT candle |
|---|---|
| **Close above** previous candle's high | Higher prices |
| **Close below** previous candle's low | Lower prices |
| **Wick above** previous high, close back inside | Lower prices (bearish turtle soup) |
| **Wick below** previous low, close back inside | Higher prices (bullish turtle soup) |
| Closes inside the range | Inside bar. The range continues and the turtle soup may come later. |

**Filters (he stresses these, so a bot should not chase wicks and closes alone):**
- Always pair the bias with a **key level**.
- There is a **market structure / market profile requirement** (e.g. a bullish week should show a low → high → lower low → close above the high that broke the low).
- In a bullish market, wicks below tend to get filled. Expect **highs to be broken through and lows to be turtle-souped**. Bearish is the mirror image.
- **Trade with the HTF CRT.** Do not take bullish LTF CRTs inside an HTF bearish CRT, or the reverse. The only exception is counter-trend trading, which he calls lower quality.
- If confused about direction, ask **"who is getting trapped?"** (retail buys above highs and sells below lows).

---

## 4. The CRT 3-candle model (C1 → C2 → C3)

```
Bearish CRT:
C1 = range (accumulation). Mark CRTH, CRTL, 50%.
C2 = wicks ABOVE C1 high and closes back inside (turtle soup / manipulation).
C3 = distribution down → Target 1 = 50% of C1 → Target 2 = C1 low (CRTL).
Bullish CRT = mirror image.
```

- After a turtle soup of the range, price "with extremely high probability" trades back to **at least 50%** of the range.
- "Always take partials at 50%" (or at a high/low near 50%).
- A CRT that reaches 50% and then reverses is **not** a failure, because Target 1 was hit. A trader who only ever trades CRT high/low → 50% "can build an entire career on that".
- **Two-candle CRT:** if C2 already expands strongly (no C3 entry), treat it as a 2-candle CRT. Log it as a miss and move on.
- **"If the manipulation happened at the end of the previous candle, expect distribution in the next candle with minimal manipulation."**
- Phases are not fixed. The order can be accumulation → manipulation → distribution **or** manipulation → accumulation → distribution. Your job is to work out which phase is running now.

### Which candle to trade
- **Beginners: trade Candle 3 only.** Watch Candle 2 without trading it ("tape-read C2, trade C3").
- Candle 2 is slow, choppy and hard. Only very advanced students should trade it.
- Candle 3 is the **fastest trade**, because the manipulation is already done.

### How to trade Candle 3 (his summary)
1. Mark C1 (accumulation) and confirm C2 manipulated into a **key level**.
2. **Wait for C2 to CLOSE.** Never act mid-candle, because a candle that looks bearish mid-way can close bullish.
3. At **C3's open**:
   - **Bearish:** wait for the price to pop **above C3's open**, ideally above a small high (turtle soup), then sell. ("Sell above the open.")
   - **Bullish:** wait for the price to drop **below C3's open** and turtle-soup a low, then buy. ("Buy below the open.")
4. Entry = LTF Model #1 or true MSS / OTE (Section 6).
5. Targets: **50% of C1**, then the **opposite end of C1** (CRTH/CRTL), then look for further targets.
6. Daily CRT: the reference open is the daily open (00:00 NY). Weekly CRT: sell above or buy below the **Monday 00:00 NY open** while watching from Sunday 17:00 NY.
- Candle 1 usually contains a Model #1. **Candle 3 usually contains an OTE** (a continuation of the true MSS formed inside C2, or the true break and continuation).

### Ideal bullish CRT (Candle 3 focus)
Price dumps toward a key level → a **thick down-close candle right before the key level** (C1) → C2 manipulates below (turtle soup into the key level) → C3 expands up.

---

## 5. The "journey" inside a CRT (what you should see on the LTF)

From the turtle soup to the target, in a bullish CRT (mirror image for bearish), he calls these near-certainties:

1. **Turtle soup** at the CRT low / key level (almost always present)
2. **Model #1**
3. **True market structure shift** (every CRT has one)
4. **Breaker / OTE** (the second-leg entry)
5. **Kiss of Death turtle soup** just before the target is hit

Entry **time sequence**: Entry 1 = turtle soup. Entry 2 = order block / Model #1. Entry 3 = market structure shift, then a breaker or OTE for the second leg. "If the breaker or OTE has already hit, looking for the earlier entry is foolish."

He adds that every turtle soup has a **failure swing**: a second push back toward the extreme to scare people out before the real move.

---

## 6. Entry models (precise rules)

**"Every entry you ever take is either a Model #1 or a true market structure shift."**

### 6.1 Model #1 (M1)
**Bullish M1:**
1. Price trades down into an **old low** (ideally at an HTF key level, at the right time).
2. Identify the **one thick down-close candle** that stabbed below the old low. Prefer a **thick** body, which shows a strong dump that scares people. A flimsy candle is weaker.
3. **Wait for a candle to CLOSE above that candle's high (body).** A wick above does not count.
4. Entry: on the close / at the M1 candle high (a retrade into the M1 candle is RTM1).
5. Stop: below the M1 low (the turtle-soup low).
6. Targets: **highs one by one**, then 50% of the CRT, then the CRT high.

**Bearish M1:** mirror image. A thick **up-close** candle stabs above an old high, then a candle **closes below** it. Sell, stop above its high, target the lows one by one.

**Higher probability when:** M1 comes **with an FVG**, comes **at the right time** (Section 8), comes at an **HTF key level**, or an **FVG sits above the old high / below the old low**.

**Pairings:** Monthly → Daily M1. Weekly → 4H M1. Daily → 1H M1. (4H → 15m M1)

### 6.2 True MSS + OTE entry
**Bullish:**
1. Price comes from a **key level**: low → high → **lower low** (turtle soup) → **candle close above the high that broke the low** (true MSS).
2. Wait for the retrace into the area **between that high and the turtle-soup low** (the OTE / failure swing).
3. Buy in that area. **Stop = below the turtle-soup low** ("if your stop is the turtle soup, you're unlikely to get turtle-souped").
4. Target: previous highs and liquidity, the previous day's high, 50% of the CRT, the CRT high.

**OTE zone drawing (his method, bearish example):** Draw a Fib from the high that broke the low (the swing that started leg 1) to the end of expansion leg 1. Mark the zone from **0.5 to 0.79**, and draw a second Fib using **bodies**. The reaction usually happens in the **lower half** of the zone. Shallow reaction = "heavy" price = strong move. Deep reaction = more troublesome. In a strong trend, the price may not even reach 50%; adapt to the logic (has enough liquidity been lured in?) rather than insisting on a level.
**OTE Target 1:** the **body of the high that went down** into the zone (bearish case). After that, previous lows.

### 6.3 Kiss of Death entry
In a bearish CRT, after the price has reached 50% and bounced, look for a final push **above** a minor high (often with a bearish FVG above an old high), then a **LTF Model #1** to sell into the CRT low. Mirror image for bullish. The reaction to a big bullish candle into the KOD is exactly where you need to sell. "Get comfortable selling big up-close candles and buying big down-close candles, within rules."

### 6.4 Fake MSS warning (anti-pattern for a bot)
- Near a **bullish key level**, the market maker prints a **convincing bearish/bottoming pattern and even an MSS right before** the level. That is the trap (a KOD TS). Price then dumps into the key level and **then** forms the true MSS.
- On the way down to a bullish key level they print **several bullish CRTs that fail**. "CRT pattern traders die on the way down to the key level."
- "They give you a fake bottom always, before the actual low."
- An MSS at a **premium** in a bullish direction (or at a **discount** in a bearish direction) = **FMSS**. Fade it, don't follow it.

---

## 7. Stops, targets, exits

- **Stop:** beyond the turtle-soup extreme / M1 candle extreme. He hints at tighter stops for advanced students but doesn't teach them publicly.
- **Target 1 = 50% of the CRT candle** (always take partials there or at a high/low near it).
- **Target 2 = the opposite end of the CRT range** (CRTH/CRTL).
- Otherwise target **old highs/lows one by one**.
- Good targets after a reversal: the **high just before the dump into the old low** (bullish), or the **low just before the high was taken** (bearish).
- **"Every exit is an entry and every entry is an exit."** Targets are where new setups form.
- Exit by **price** (target hit) or by **time** (e.g. the session or candle closing). Both are valid.
- Lows that **fill an FVG** in a bullish market are good stop-loss anchors, because they usually aren't revisited before the target. Mirror image for bearish.
- Don't exit too early (fear before the target) or too late (greed past the target back to the stop). Both are reviewed weekly.

---

## 8. Time rules ("time is more important than price")

- **"If the time is right, the pattern works; if the time is wrong, the pattern fails."**
- All times are **New York time**. Lagos (WAT, UTC+1) is **6 hours ahead of NY in winter (EST)** and **5 hours ahead in summer (EDT)**. NY midnight = 06:00 Lagos (Nov–Mar) / 05:00 Lagos (Mar–Nov).
- **Weekly open = Monday 00:00 NY.** Watch from the Sunday 17:00 NY open, but treat Monday midnight as the "true" week open. **Weekly close = Friday 16:00 NY.** (One older video says 17:00.) Crypto: treat Mon–Fri as the week and weekends as noise.
- **Daily open = 00:00 NY. Main action window = 00:00 to 16:00 NY.** After that, don't chase.
- **Weekly high/low timing:**
  - One extreme of the week usually forms **Mon–Wed**. The opposite end comes **Thu–Fri**.
  - A typical bearish week: a **fake high on Monday** (often with an FVG to trap pattern traders), the **real high on Tuesday** (Model #1 forms), then a vicious dump into **Thursday/Friday**.
  - **"Thursday + Model #1 at the key level = time and price meet"**, which is his highest-conviction moment.
  - Typical bullish week: Monday chops to confuse, then a stab into the key level **Mon–Wed** (often **Tuesday**, his examples include the **London session on Tuesday**), then expansion **Wed–Fri**.
- Weekly cycle as candles: week 1 accumulation, week 2 manipulation, week 3 distribution (AMD inside a monthly range).
- Every high and low of every candle (weekly, daily, 4H) is **timed**. He keeps the detailed times for private material.

---

## 9. SMT (correlated-asset divergence)

**Definition:** one asset takes a high or low, its correlated pair does not. That signals smart money is unwilling to push further.

**SMT pairs he uses:**
- **EURUSD ↔ DXY** (inverse) and **EURUSD ↔ GBPUSD**
- **ES ↔ NQ** (and the Dow)
- **BTC ↔ ETH**
- **Gold ↔ Silver**

**Candle SMT:** compare the same candle on both assets. One turtle-soups the level and the other doesn't.

**Uses of SMT:**
1. **FVG fill SMT**: one asset fills its FVG, the other doesn't.
2. **Confirmation** (most important, below).
3. **Leaving equal highs/lows**: if EUR takes a low but DXY doesn't take the matching high, expect DXY to leave relatively equal highs and continue.
4. **CRTs**: CRT plus SMT.
5. **SMT stops targets from being hit** (the main reason a CRT "fails", Section 10).

**SMT = expansion.** Only take **bullish SMTs in an HTF bullish market** and **bearish SMTs in an HTF bearish market.**

**Two confirmations before acting on an SMT (don't buy or sell blindly on divergence):**
1. **Model #1** on the asset that swept the level: initial confirmation, which moves the price to a certain point.
2. **True MSS** (key level + time): for further expansion.

---

## 10. When CRT "fails" (bot invalidation logic)

1. **SMT:** after the turtle soup, on the way to the CRT target, an **opposite CRT forms with an SMT plus a Model #1 / MSS confirmation**. Stop forcing the original bias and follow the new direction.
2. **The 50% was already hit:** that is Target 1, not a failure. After 50%, monitor whether the price continues to the opposite end or reverses.
3. **Wrong CRT for the conditions:** taking bearish CRTs on the way up to a bullish HTF target (or bullish CRTs on the way down). Stick to CRTs **with the HTF trend**.

Other loss sources he names: no key level, no candle close (acting on wicks), forcing a turtle soup ("if it closes above, let it go, there'll be another"), trading C2 too early, wrong time, over-leveraging.

---

## 11. Key levels

- **Definition:** a price where you expect a bounce, either counter-trend or the actual high or low of the candle.
- Usually an **HTF level** that you watch from the LTF.
- **Pair the key level with an old low (bullish) or old high (bearish)** on the same timeframe, so you expect the price not to go much past that low.
- Support/resistance by candle type: when probing order flow, treat **down-close candles as true support** and **up-close candles as resistance** (e.g. the **opening price of a down-close candle**).
- **50% of an HTF wick** (e.g. a weekly candle's long wick) works as a key level.
- Lows/highs sitting **above or below FVGs**, and old liquidity pools near all-time highs, expect reactions.
- **Two trade opportunities per key level:** trade the journey **to** it (fast sells down into a bullish KL) and trade the reversal **from** it.
- Skill stages: (1) can't mark them correctly, (2) can mark them but can't trade them, (3) can mark and trade them because you know how the LTF behaves at HTF levels.
- What the LTF does at a bullish HTF key level: bearish patterns and failed bullish CRTs on the way down, then a convincing fake bottom / FMSS right before the level, then a KOD dump into the level, then a **true MSS** and expansion.

---

## 12. Weekly routine ("SS" = Saturday & Sunday)

**Saturday (early morning): review last week, for the asset you trade**
- What day and time did the **weekly high** form? The **weekly low**?
- What was the **shape** of the weekly candle (full bullish or bearish, up-then-down, down-then-up, pin/wick, inside)? Why?
- Which **weekly or daily key level** produced the high or low of the week (the "launch pad")?
- Execution review, answered yes/no with a reason:
  - Over-leveraged? Took more than the allowed number of trades?
  - Took a trade out of **boredom** (no model present)?
  - Exited **too early**? Exited **too late**?
  - Did you predict last week's candle correctly? If not, where did the read fail?

**Sunday: prepare for next week**
- Did last week **close above / below** or **wick above / below** the week before it? Combine that with the **key level** and the **market profile**, not wicks alone.
- Mark Monday (vertical line). Mark **last week's high and low** and other recent highs and lows (pre-open liquidity pools).
- **Anticipate next week's candle shape** (up, down, inside).
- During the week, watch how the price reacts to those pools (sweeps up then down? down then up? doesn't touch them = inside week?).

**"The Lens" (predicting the weekly candle):**
1. Mark the weekly open (Mon 00:00 NY) and close (Fri 16:00 NY).
2. Decide the bias (close/wick rules) and draw this week's high and low.
3. Mark the HTF key level (weekly/daily, e.g. 50% of last week's wick) and **pair it with an old low** (bullish).
4. Expect Monday chop, then a stab through consolidation into the key level (turtle soup) around Tue/Wed, then expansion Wed–Fri.
5. Target nearby highs one by one. Watch for **rejection blocks**, which cause a retracement before the high is taken.
6. Goal: **capture a portion of the planned expansion** more often than not, with controlled risk.

**Journaling law:** *Win → journal → repeat. Lose → journal → avoid. Miss → journal → catch next time.* Reverse-engineer every loss through the "open → turtle soup → expansion" lens.

---

## 13. Risk & behaviour rules (for the bot's guardrails)

- **Fewer, higher-quality trades.** Only execute when the model blatantly presents itself. "The best trades come to you."
- Never trade because the market is open, out of boredom, or to "force" a turtle soup.
- **Always wait for the candle close** (M1 trigger, OTE activation, C2 before C3).
- One bad setup must never blow the account, so use fixed risk per trade and a max number of trades.
- Don't let a win cause overconfidence or a loss cause fear.
- Beginner ladder: weekly/daily/4H only → Candle 3 only → master that before Candle 2 or lower timeframes. He suggests about 1 year to reach consistency.
- Partial profit at 50% of the CRT.

---

## 14. Gaps and ambiguities to resolve before coding

He leaves these discretionary or keeps them for paid material, so the bot needs explicit choices and backtests for each:

1. **"Thick" candle:** no numeric definition. Suggested proxy: body ≥ X% of range and body ≥ Y × ATR or the median body of the last N candles.
2. **Key level selection:** his "crown jewel", not fully taught. Start with prior-period highs/lows (PWH/PWL, PDH/PDL), the opening price of the last down-close (support) or up-close (resistance) candle, 50% of the HTF wick, and unfilled HTF FVGs.
3. **"Old high/low":** which swing counts. Define it as a fractal swing (e.g. 3- or 5-bar pivot) on the entry timeframe and require it to be "visible".
4. **Market profile:** only partly explained (range → turtle soup → trend, MSS structure). Treat it as "a true MSS exists in the bias direction".
5. **Exact high/low times:** only the general weekday pattern is public (Section 8).
6. **Six candle shapes / candle classification** (very bullish → very bearish): mentioned but not taught.
7. **Inside-candle handling:** "topic for later".
8. **Weekly open conflict:** Sunday 17:00 vs Monday 00:00 NY. He favours Monday 00:00 as the true open, but test both.
9. **Weekly/daily close:** 16:00 NY (newer video) vs 17:00 NY (older video).
10. **The OTE needs judgement** (has enough liquidity been taken?). A bot needs a fixed zone (0.5–0.79) plus a confirmation trigger.

---

## 15. Bot logic skeleton (suggested encoding)

```
for each trading candle TF in [Weekly, Daily, 4H]:
    entryTF = pair(TF)   # W→4H/1H, D→1H/15m, 4H→15m/5m

    # 1. HTF context
    prev, last = last two CLOSED candles on TF
    bias = close/wick rule (Section 3)
    require: HTF key level near the expected turtle-soup side
    require: bias agrees with the next-higher TF CRT (no counter-trend)

    # 2. CRT setup
    C1 = range candle  -> CRTH, CRTL, MID = (CRTH+CRTL)/2
    C2 must have CLOSED and turtle-souped C1 on the bias-opposite side, at/into key level
    C3 = current candle; reference = C3 open

    # 3. Time filter
    within 00:00–16:00 NY
    weekly setups: prefer TS Mon–Wed; highest conviction Thu + M1 at key level (reversal)

    # 4. Entry trigger on entryTF (bearish shown; invert for bullish)
    price must trade ABOVE C3 open and sweep a local high (turtle soup)
    trigger = Model #1 (close below thick up-close sweep candle)
           OR true MSS + retrace into 0.5–0.79 OTE zone
    optional boosters: FVG with M1, SMT with correlated pair (+ M1 confirm on swept asset)

    # 5. Orders
    stop  = above sweep high (M1 candle high / TS high)
    TP1   = MID (50% of C1)  -> take partial
    TP2   = CRTL
    trail / next targets = prior lows one by one

    # 6. Invalidation
    cancel if: C2 not closed; no close confirmation (wick only);
               opposite CRT + SMT + M1/MSS forms before TP; FMSS context;
               outside time window; max trades/risk exceeded
```

---

## Sources (Romeotpt YouTube channel)

- [What is CRT? Why do all other trading strategies suck?](https://www.youtube.com/watch?v=UUq_wKQ61Wo)
- [What is turtle soup?](https://www.youtube.com/watch?v=U-gNCwbGtTI)
- [CRT secrets ep.1: One CRT model for life](https://www.youtube.com/watch?v=T7udbrWlARI)
- [CRT secrets ep.2: The kiss of death](https://www.youtube.com/watch?v=FYr6J5pIDB4)
- [CRT secrets ep.3: The journey](https://www.youtube.com/watch?v=_oiwm8_id8c)
- [CRT secrets ep.4: Candle anatomy](https://www.youtube.com/watch?v=n2GF8kCpgVg)
- [CRT secrets ep.5: Key level](https://www.youtube.com/watch?v=p8UYOgVn1-g)
- [CRT secrets ep.6: SMT](https://www.youtube.com/watch?v=3IWgc52Dqsg)
- [CRT secrets ep.7: Candle 3](https://www.youtube.com/watch?v=h7NCST2wPw8)
- [CRT secrets ep.8: When does CRT fail?](https://www.youtube.com/watch?v=-mWYppebugo)
- [CRT secrets ep.9: Connecting the dots](https://www.youtube.com/watch?v=2sxdsgcIeYA)
- [CRT secrets ep.10: A clean close](https://www.youtube.com/watch?v=af7ECe4HBjc) (no technical content)
- [CRTology: Introduction](https://www.youtube.com/watch?v=8LblVvGZaGY)
- [CRTology episode 1: SS](https://www.youtube.com/watch?v=4DZWbCzEvhM)
- [CRTology episode 2: The Lens](https://www.youtube.com/watch?v=wkSiy27a8ps)
- [CRTology episode 3: OTE](https://www.youtube.com/watch?v=f4gdAohTi40)
- [CRTology episode 4: Terminology (i)](https://www.youtube.com/watch?v=L87Iy51_ATM)

Not covered: the two "CRT live tape-reading" sessions (live chart commentary) and the third-party playlists that re-upload his paid courses.

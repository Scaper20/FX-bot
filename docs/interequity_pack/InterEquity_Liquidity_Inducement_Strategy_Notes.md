# Inter Equity Trading: Liquidity Inducement Strategy Notes (for a trading bot)

Compiled 25 Nov 2026 from the Inter Equity Trading YouTube channel ([@InterEquity](https://www.youtube.com/@InterEquity), 64 videos). The trader (Marco) trades mostly NQ futures and gold, and shows EURUSD and AUDUSD examples. The whole channel teaches one system: **liquidity + inducement**. I read the transcripts of the 10 core videos (listed at the bottom) and captured frames for the visual pack.

> These notes paraphrase his public teaching. The P&L and funding results he shows are his own claims and haven't been checked by anyone else. He keeps the system mostly discretionary ("train the eyes"), so Section 10 lists what a bot needs you to define. Backtest every rule before risking money. This is not financial advice.

---

## 0. The whole system in one paragraph

Price moves to take liquidity: the stops and orders resting above highs and below lows. A break of structure (BOS) doesn't tell you to follow it. It **induces** retail traders to enter in that direction, and their stops build new liquidity. The market then comes back, takes out those traders (**traps** them), and only then makes the real move. So the rule is: **wait for one side to be induced, wait for that side to be trapped, then trade the opposite way.** Put the stop beyond the **Liquidity Block** (LB) and target the liquidity the market has left untouched. It works the same on every timeframe from weekly down to 1-minute.

> "Whenever buyers are induced, we do not want to be buying that market. Wait for them to get trapped, then we look to buy." (Masterclass Ep.1, paraphrased)

---

## 1. Definitions

| Term | Meaning |
|---|---|
| **Liquidity** | A high or low where orders/stops are resting. He only marks it when price **communicates** it: a high or low that was **respected** (price reacted off it, often more than once) and then moved away. "We're not predicting, the market told us." Equal highs/lows and areas tapped many times count as strong liquidity. |
| **Internal liquidity** | Smaller highs and lows inside a move. He uses them as partial-profit points and expects pullbacks after each is taken. |
| **Structural level** | A major swing high/low that retail treats as structure. A good place to pay yourself. |
| **BOS (retail term)** | A break of a prior high/low. He uses it only to describe what **retail** sees. |
| **Inducement** | The move that tempts traders to enter. **High taken → buyers induced**: retail now wants to buy pullbacks above the low that made the new high. **Low taken → sellers induced**: retail wants to sell rallies below the high. |
| **Trap / trapped** | Price takes out the level that induced traders are using for stops. **Buyers trapped** = the low below their buys is taken. **Sellers trapped** = the high above their sells is taken. Once one side is trapped, look for the trade the other way. |
| **"Trap" zone (red box)** | The zone retail expects to hold (e.g. the old high retested as support after a BOS). Expect a **false reaction** there, then a break through it. |
| **Engineered liquidity** | Bullish (or bearish) reactions that happen **before** the real liquidity below (above) has been taken. These are fake bounces that build more stops on the other side. Don't trade them. Treat them as fuel for the move you want. |
| **Liquidity Block (LB)** | The swing high or low that **took** a prior level of liquidity. Once it has swept the liquidity there is nothing left beyond it, so price has "no reason" to run it. Uses: (a) a future entry area, and (b) **the stop level: "no LB, no stop-loss, no trade"**. Refine an HTF LB on a lower timeframe for a tighter stop. |
| **Refinement** | Dropping from the HTF LB to a lower timeframe (e.g. 1H → 15m → 1m) to find a smaller LB inside it, giving a better risk:reward. |
| **Lows/highs left intact** | During a trend, swing lows that are never revisited become future targets and signal a later reversal. He doesn't buy a rally that keeps leaving lows intact, because there was no liquidity grab to buy from. |

**Priority (he repeats this):** 1) liquidity, the story and direction; 2) liquidity block, the entry and stop. An LB without a liquidity story is just a random high or low and leads to "a lot of unnecessary losses".

---

## 2. The core cycle (bot logic)

### Bearish (mirror image for bullish)
1. **Identify liquidity on the other side.** Find lows that price has respected and left intact. These are the targets.
2. **Sellers induced.** Price takes out a low (a BOS to the downside). Retail now expects to sell pullbacks below the most recent high, and their stops sit just above that high.
3. **Expect a false reaction.** Price may react at the retail sell zone, and you should not sell there.
4. **Sellers trapped = trigger.** Price takes out the high that induced sellers were hiding stops above. Now look to SELL.
5. **Entry:** as soon as that liquidity (the high) is taken. Don't wait for the extreme ("I don't need to get greedy... I just want to enter as soon as that liquidity is taken"). In his diagrams, anywhere above the taken high is valid.
6. **Stop:** above the **liquidity block**, i.e. the high that just swept the liquidity, or the HTF LB to the left. "Our stop loss always goes above this high from the left. Always."
7. **Targets:** internal lows first (partials), then the structural low, then the HTF low/liquidity from the left. "Every bullish reaction after sellers are trapped and buyers are induced is false."
8. **Management:** after the first internal liquidity is taken, move to break-even or tuck the stop behind the reaction high. Move the stop **only after liquidity is taken**. Don't roll it out of fear when price first goes into profit, because a second induce-higher-then-dump move is very common.

### The full two-way sequence (Masterclass Ep.2, image 03)
Every swing gets a label:
- Low taken → **sellers induced**
- Then a low taken after buyers entered → **sellers induced + buyers trapped**
- High taken → **buyers induced + sellers trapped**
- Then a quick drop below the low that buyers bought → **buyers trapped + sellers induced** → the signal to **BUY**, targeting the highs.

Bot rule: keep a running state of `{side_induced, side_trapped}` for each swing. Only take a trade **against the most recently induced side, after that side is trapped**.

---

## 3. Entry models

### 3.1 Liquidity → LB entry (main method)
- Story first: which side is induced, where the liquidity is, where the target is.
- Wait for the liquidity (old high/low, equal highs/lows, a range edge tapped several times) to be **taken**.
- Enter on the sweep, or on the retrace into the **LB** created by the sweep.
- Stop beyond the LB low/high. Target the opposite liquidity.
- If the HTF LB is too large, use a lower timeframe LB inside it to tighten the stop (his NQ 1H/4H example: 1:6, 1:7, 1:19, 1:14, 1:3.6 using only 1H/4H, plus one 15m refinement).

### 3.2 "The ONLY entry model" (sniper, 4-candle, fractal)
Bullish (mirror image for bearish):
- **C1** prints a low.
- **C2** spikes below the C1 low (a sweep) and closes back up above it, leaving a long lower wick. This creates a lower-timeframe **LB**.
- **C3** prints a low and closes bullish.
- **C4: when price trades below the C3 low → BUY.** Anything between the C3 low and the C2 low (the LB) is valid. Price can wick deep in C4, so the whole zone is valid.
- **Stop:** below the C2 low (the LB). **Target:** liquidity above.
- Works on daily, 4H, 15m and 1-5m. He says the pitch-perfect fills are not typical.
- His bearish 5m NQ example: C2 sweeps a high and leaves an LB, C3 leaves a high, then C4 spikes above the C3 high → sell with the stop above the LB.

### 3.3 Continuation model ("highest strike rate", image 11/12)
For a bearish continuation:
1. A clear **liquidity low** exists (price came back to an old low, respected it and rallied away).
2. The trend turns down. Price makes the induce/trap sequences at the highs.
3. Price trades back **into the liquidity-low area and bounces**. That bounce is **engineered liquidity**, a red flag that the low will be taken later. "We don't respect liquidity and just continue back up."
4. Don't sell the first high taken during the bounce (that's pattern trading). Wait for the price to **take the last engineered high / the liquidity just above**.
5. **Sell** anywhere above that taken high. **Stop above the LB/high from the left.** Target the liquidity lows.
6. Expect a fast move into profit, then one more induce-higher spike, then the dump. Keep the stop above the LB.

### 3.4 Stacking entries
Re-enter in the HTF direction each time a **new** level of liquidity is built and taken, with the stop below each new LB. His NQ example has 5 stacked longs from a weekly LB to the weekly equal highs. Each new entry needs:
- a fresh buildup of liquidity (buyers induced → their low swept),
- a new LB for the stop,
- the original HTF target to remain valid.

---

## 4. Daily bias (Finding the Daily Bias ONLY Using Liquidity)
1. Every morning, mark the **previous day's high and low**.
2. Ask what yesterday's main move was for:
   - Yesterday sold off **into lows where buyers had been entering** (buyers trapped) → today's bias is **bullish**, target yesterday's high and the liquidity high to the left that started the sell-off.
   - Mirror image for bearish.
   - Check that the move **respected** a liquidity level, which means it was a trap move.
3. Intraday (he trades only the **New York session**; futures mostly after 08:00 / 09:30 NY stock open):
   - Wait for a range or low where buyers keep getting induced (the price taps a low again and again).
   - **Buy only below that low** (strict rule, no exceptions), with the stop below a nearby LB (a low that already trapped buyers).
   - Target the previous day high and the liquidity high from the left.
4. "Lower timeframe for entry, higher timeframe for bias." All of it is fractal, 1m → weekly.

---

## 5. Higher-timeframe narrative (10,000 Hours / Liquidity Mastery Vol.1)
- Start on the weekly/daily. Mark respected equal highs/lows and long-built ranges (areas tapped for weeks). These are the big targets.
- A multi-week sell-off **into a cluster of old lows plus an HTF LB** is a trap move. The bottom forms at the LB, and you then buy the pullbacks on 4H/1H toward the HTF equal highs.
- "As price trades up and leaves lows intact, there are no high-probability longs on the way up, and those intact lows are future targets."
- When liquidity has just been taken, **wait**. Let the price build new liquidity (induce one side again) before the next entry.
- **News warning:** wicks caused by news are unrealistic to trade live. Don't count them as clean entries in backtests.

---

## 6. Sessions & time
- He trades **only the New York session** for futures, usually after **08:00 or 09:30 ET (stock open)**. London (03:00 ET) moves are context: they often build or induce the liquidity that New York then takes.
- Times are in **EST/ET** (New York). Lagos is 6 hours ahead of New York in winter and 5 hours ahead in summer (e.g. 09:30 ET = 15:30 Lagos in winter).
- A 9:30 stock-open sell-off that sweeps lows induces sellers. A run above the pre-marked high just after is his classic short.

---

## 7. Targets & risk
- Targets, in order: internal liquidity (partials) → structural level → HTF liquidity from the left.
- Usual minimum R:R is about 1:3–1:4 if a target lines up. He holds further when the HTF story supports it.
- Stop placement is fixed by the LB. Never place stops "randomly" or tighter than the LB out of greed.
- Move to break-even/trail only after a level of liquidity in your direction is taken.

---

## 8. What NOT to trade (invalidation filters)
- Buying after a high is taken ("buyers induced"), or selling after a low is taken. That is the retail pattern trade.
- Trading the first reaction in a trap/red box. It is expected to be false.
- Buying a bounce when the liquidity lows below are still intact (engineered liquidity). Same for selling a dip with highs intact above.
- Any entry with no LB to put the stop behind.
- Entering before the liquidity is actually taken (anticipating the sweep).
- Wicks caused by news.
- Counter-HTF-story trades. The HTF liquidity story decides direction.

---

## 9. Bot logic skeleton
```
for each instrument (he uses NQ/ES, XAUUSD, EURUSD, AUDUSD; fractal on any)
  HTF = 4H/Daily/Weekly ; LTF = 15m/5m/1m

  # 1. Liquidity map (HTF and LTF)
  swings = fractal pivots
  liquidity_levels = swings that were RESPECTED (>=1 later retest that held, or equal highs/lows)
                     and are still intact
  LBs = swings that took (wicked through) a liquidity level and then reversed

  # 2. Story / bias
  draw = nearest intact liquidity on HTF in the direction implied by the last trap
  daily bias: if yesterday swept liquidity lows that buyers used (buyers trapped) -> bullish,
              target PDH + liquidity high to the left (mirror for bearish)

  # 3. State machine per swing (LTF)
  on low taken:  sellers_induced = True ; if buyers had entered above that low -> buyers_trapped = True
  on high taken: buyers_induced = True  ; if sellers had entered below that high -> sellers_trapped = True
  mark any bounce while opposite liquidity is still intact as ENGINEERED (ignore)

  # 4. Entry
  SELL when: bias bearish AND sellers_induced AND the high above their entries is taken (sellers_trapped)
             AND an LB exists above -> enter on the sweep (or retrace into the LB)
  BUY  = mirror
  alt trigger (sniper 4-candle): C2 sweeps C1 extreme + closes back, C4 trades beyond C3 extreme
  session filter: NY session (>= 08:00 ET; futures prefer after 09:30)

  # 5. Orders
  stop  = beyond LB extreme (+ small buffer)
  TP1   = nearest internal liquidity (partial) ; TP2 = structural level ; TP3 = HTF liquidity
  move stop to BE / behind reaction swing only after TP1 liquidity is taken
  skip if R:R to TP2 < threshold (e.g. 2–3)

  # 6. Filters / invalidation
  no LB -> no trade ; liquidity not yet taken -> no trade ; news spike -> ignore
  first reaction inside a trap zone -> ignore
```

---

## 10. Things he leaves discretionary (define these before coding)
1. **Swing definition:** which pivot size counts as a "high/low". Suggested: 3- or 5-bar fractal on each timeframe.
2. **"Respected" liquidity:** how many retests and how close counts as a tap. Suggested: a later swing within X ticks/ATR fraction that holds, or equal highs/lows within a tolerance.
3. **Who entered where** (to decide "trapped"). Approximate it as the last opposite swing after a BOS. Retail sells below the high formed after the low was broken.
4. **Which LB to use** when several stack up. He takes the closest valid one that keeps R:R acceptable, and refines on a lower timeframe.
5. **Stop buffer** and minimum R:R.
6. **Engineered-liquidity detection:** a bounce that starts before the nearest opposite liquidity level is taken.
7. **News filter:** an economic calendar blackout around high-impact releases.

---

## 11. How it overlaps with the Romeo CRT notes
- Romeo's **turtle soup** ≈ Inter Equity's **liquidity taken / trapped**. Romeo's **Model #1 candle** ≈ the **Liquidity Block** that set the stop. Romeo's **fake MSS** ≈ **inducement**. Both say: don't trade the visible pattern, trade the trap.
- Differences: Inter Equity has no candle-range or 50% targets. Targets are the liquidity pools. Session timing is simpler (New York session only).
- A combined bot could use **CRT for the HTF range/bias and timing**, and **Inter Equity's induce → trap → LB** as the lower-timeframe entry and stop.

---

## Sources (Inter Equity Trading)
- [Liquidity Inducement Masterclass Ep. 1](https://www.youtube.com/watch?v=htyknOTK-xs)
- [Liquidity Inducement Masterclass Ep. 2](https://www.youtube.com/watch?v=0whEBw9aHKM)
- [Liquidity Inducement Masterclass Ep. 3](https://www.youtube.com/watch?v=x4ZUCA0GO48) (NQ live trade)
- [The ONLY Entry Model You Need (SNIPER ENTRIES)](https://www.youtube.com/watch?v=yIYY_jYy3sE)
- [Liquidity Inducement Entries (LIQUIDITY BLOCKS)](https://www.youtube.com/watch?v=GIYrW7FC06M)
- [How To Master Market Continuations](https://www.youtube.com/watch?v=QTGP2NQUcBE)
- [Finding the Daily Bias ONLY Using Liquidity](https://www.youtube.com/watch?v=-mX823uc5-s)
- [10,000 Hours of Liquidity Trading in a 16 Minute Video](https://www.youtube.com/watch?v=aKoGbAe-xTE)
- [Liquidity Mastery Volume 1](https://www.youtube.com/watch?v=SkKjZeY6EN4)
- Channel video list reviewed: [@InterEquity/videos](https://www.youtube.com/@InterEquity/videos)

Not transcribed: the "Training The Eyes" episodes 1–13 (chart-reading practice), Liquidity Mastery Vol. 2–3, live-trade recaps, and the full webinar. They apply the same rules and could serve as backtest/labeling examples.

---

## Visual index (visuals/ = his frames, schematics/ = my diagrams)

| File | Shows |
|---|---|
| visuals/01 | Bullish BOS induces buyers. The retest zone (red) is a trap, so expect a false reaction, then a dump. |
| visuals/02 | His bullish vs bearish inducement diagrams side by side (Ep.1 final). |
| visuals/03 | The full Ep.2 sequence with every swing labelled (induced/trapped), ending in the buy signal and the long position box. |
| visuals/04 | Close-up of the "Buyers Induced / Sellers Trapped / Buyers Trapped / Sellers Induced" labels. |
| visuals/05 | His 4-candle sniper entry sketch with the position (entry at the C3 low, stop under the C2 wick). |
| visuals/06 | Daily NQ example: the blue buy zone below the C3 low, down to the LB low (circle). |
| visuals/07 | 5m NQ bearish sniper example (C4 spikes above the C3 high). |
| visuals/08, 09 | Bearish and bullish liquidity block diagrams (LB circled after the BOS + sweep). |
| visuals/10 | Gold 15m with LBs marked (red = bearish, blue = bullish). |
| visuals/11 | Continuation model diagram: liquidity lows, two "Eng. LQ" bounces, then the sell position. |
| visuals/12 | AUDUSD 1H continuation: "ENG LIQUIDITY" bounce off the liquidity lows, sell zone above (blue). |
| visuals/13 | Daily bias on gold: Wednesday high/low marked, projected path to the Wednesday high. |
| visuals/14 | Gold 5m: buy below the range low that induced buyers, run to the Wednesday high. |
| visuals/15 | NQ weekly: multi-week sell-off into liquidity lows + HTF LB (red) → bottom. |
| visuals/16 | NQ 4H: stacked long entries after each new liquidity grab. |
| schematics/01 | Core cycle (bearish): sellers induced → sellers trapped → sell, stop above the LB, target the intact lows. |
| schematics/02 | Liquidity block and the stop rule. |
| schematics/03 | The 4-candle sniper entry with exact entry/stop lines. |
| schematics/04 | Continuation model with the engineered-liquidity trap zone. |

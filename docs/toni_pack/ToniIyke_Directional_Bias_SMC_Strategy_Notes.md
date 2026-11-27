# Toni Iyke: Directional Bias + SMC (Structure → Inducement → POI) Strategy Notes (for a trading bot)

Compiled 27 Nov 2026. Sources:
- All 8 videos on his own channel, [@toni_iyke](https://www.youtube.com/@toni_iyke) (transcripts read in full)
- The free 3-minute explainer by PipslayerFX
- A trade-recap upload by "Toni Iyke Insights" (no transcript, frames only)

He trades GBPJPY, XAUUSD (gold), BTCUSD and USDJPY.

> **What I skipped:** the three results on your search page from "Premium Forex Courses", "PAID FOREX COURSES" and "FOREX LEAKED COURSES" (the 1h12–1h35 "February 2026 directional bias" uploads). They are re-uploads of his paid class, so they're pirated, and I left them out, the same as with Romeo's leaked course. He also says in his BTC video that he won't teach the full concepts publicly "because some people paid me for it". So these notes are thinner than the Romeo or Inter Equity packs, and Section 9 lists the gaps.
>
> His P&L claims (e.g. "$38,000 in 5 days") haven't been checked by anyone else. **Don't copy the money management from that video:** he risked 25% and then 100% of the account on single trades. Backtest every rule before risking money. This is not financial advice.

---

## 0. The whole system in one paragraph

1. Get the **directional bias on the 4H** (sometimes Daily) from plain market structure: higher highs/higher lows = bullish, lower highs/lower lows = bearish, otherwise ranging.
2. Mark the **HTF zones** where price should react: order blocks, breaker blocks, support/resistance and trendlines.
3. When price reaches a zone, **don't enter on the touch**. Drop to a lower timeframe (15m/30m/1H) and wait for his three-step **"strategy": Market Structure Shift (MSS/BOS) → Inducement (liquidity) → POI** (the order block or breaker nearest the inducement).
4. Enter at the POI in the bias direction. Target the **nearest draw on liquidity**: the last high/low, trendline liquidity, or the "fake" OB other traders expect to hold.
5. **Keep taking continuation trades in the same direction** (several a week) until the HTF target is hit, e.g. the last 4H high in an uptrend.
6. Only flip bias when price reaches an opposite HTF zone **and** prints the same reversal model there.

> "I focus more on directional bias than just taking every single move I see in the market." (A Brief on Directional Bias)

---

## 1. Definitions (his words, made precise)

| Term | Meaning |
|---|---|
| **Directional bias** | The overall direction on the higher timeframe (mainly 4H; Daily for longer views). He trades **continuations** in that direction, not reversals. "If the higher timeframe is bullish we join the bullish move; if bearish, the bearish move; if ranging, we stay inside the range." |
| **Three market states** | **Uptrend** = HH/HL (a trendline connects the lows). **Downtrend** = LH/LL. **Range** = support ↔ resistance. Image: visuals/05. |
| **Zone / POI (HTF)** | 4H (or 3H/Daily) **order block**, **breaker block**, support/resistance, or a trendline touch. Best when a zone **lines up with the trendline** (GBPJPY and BTC examples). |
| **Market Structure Shift (MSS)** | On the LTF, price **takes out the last high** (bullish) or **last low** (bearish) against the prior LTF move. That signals the reversal at the HTF zone. He also uses "break of structure" (BOS) and "structure shift" interchangeably. |
| **Double / multiple break of structure** | When the shift takes out **several** highs/lows at once. He treats this as a stronger confirmation (XAUUSD and BTC). |
| **Inducement** | The **first pullback swing after the MSS**: the liquidity that early traders use. Price must **take out the inducement** before tapping the POI. "I can mark any high as my inducement" (the nearest one after the shift). |
| **POI (entry)** | The **nearest point of interest to the inducement**, beyond it. Either an **order block** (last opposite candle before the impulsive move) or a **breaker block** (the zone price broke while making the MSS/double BOS). He says there are further "criteria" for picking the POI that he doesn't share publicly. |
| **Breaker vs OB rule** (free explainer) | If the **breaker is not yet mitigated**, it is the nearest POI. If it **has been mitigated** (already tapped), use the **order block**. See schematics/03. |
| **Confirmation entry** | If he missed the POI touch, he waits for price to trigger the POI, form another small LTF shift, and **retest** the nearest POI, then enters there (GBPJPY and gold "pre-NFP" trades). |
| **Draw on liquidity / targets** | The nearest liquidity pool: the **last high/low before the POI got triggered**, **trendline liquidity** (the stops under an uptrend line or above a downtrend line), external highs/lows, and **"fake" order blocks** that others expect to reverse from. |
| **Trendline liquidity** | Any clean trend accumulates stops on the other side of its trendline. Eventually price **reverses to clear it**. He uses that both as a **target** and as a reason to expect a reversal. |
| **First-time reversal** | Getting the reversal concept (MSS → inducement → POI) **at the same level where you expected the reversal**. That is the confirmation that the zone holds. |

---

## 2. Step-by-step workflow (bot logic)

### Step 1: Bias on 4H
- Label the swings. HH+HL = **bullish**, LH+LL = **bearish**, otherwise **range** (trade only between the range edges).
- Find the **last opposite swing** that must be taken for the trend cycle to complete. Uptrend: the **last HH** is the target. Downtrend: the **last LL** is the target.
- The bias stays fixed **until that swing is taken**. "Every single day that I wake up and price has not yet taken out this high, I'm only focused on taking buys."

### Step 2: Mark HTF zones
- **With-trend pullback zones**: 4H/3H/Daily OBs and breakers, especially those **on the trendline**. Continuation entries come from these.
- **Opposite zones** (e.g. 4H resistance above in an uptrend): where a **reversal** might start. Bias does **not** flip just because price touches one.
- **Zone failure rule:** if price **ranges just under** a 4H resistance and then **breaks through** on its first touch, the zone won't hold. Keep the bias and look for another continuation entry (GBPJPY example, visuals/03).

### Step 3: LTF confirmation at the zone (15m, 30m, 1H; sometimes 3H/4H for POIs)
While price pulls into the HTF zone, the LTF will be trending **against** the bias (e.g. LTF LH/LL inside a bullish 4H pullback). Wait for:
1. An **MSS**: price takes out the last LTF high (bullish case).
2. An **inducement**: the first pullback low after the MSS.
3. Price **takes the inducement** and **taps the nearest POI** (breaker if unmitigated, otherwise OB). If no clean POI exists on the LTF, use the POI from the HTF (his GBPJPY 1H MSS used the 4H OB).
→ **Enter** at the POI in the bias direction.

### Step 4: Stops & targets
- **Stop:** beyond the POI (below the OB/breaker for buys), just under the POI's candle extreme in his position boxes.
- **TP1:** the **last high before the POI was triggered**, or the nearest draw on liquidity.
- **Further targets:** trendline liquidity → the HTF external high/low (the bias target).
- He usually **closes at the nearest liquidity pool** within a day or two, because he's a day trader. Then he **re-enters on the next continuation setup** toward the same HTF target.
- R:R examples he shows: 1:5.6, 1:8, 1:11, 1:13, 1:14, 1:16, 1:17, 1:32. All are from tight LTF POI stops toward HTF targets.

### Step 5: Repeat (continuation stacking)
- After each win, look for a **new MSS → inducement → POI** in the **same** direction on the LTF. He'll take "the same type of bias maybe in a week".
- Treat any counter-trend LTF move as an opportunity for the next with-trend entry: "Any sells I got, I used to look for more buy entries".

### Step 6: Bias flip (reversal)
Bias flips only when **both** of these happen:
- (a) price reaches an **opposite HTF zone**, or the HTF target is taken, **and**
- (b) the **same MSS → inducement → POI** model prints there, on the 30m in his GBPJPY example.

The first reversal trade is the confirmation. From then on, only take trades in the new direction ("any buy you take is going to be probably temporary").

---

## 3. Worked examples (from his videos)

| Video | Setup | Image |
|---|---|---|
| A Brief on Directional Bias | GBPJPY: price reaches a 4H OB → 15m BOS + inducement + OB → buy, then 4 more 15m buys. Price ranged under the 1st 4H resistance and broke it (zone failed) → another buy. At the 2nd 4H resistance, a 30m MSS + inducement + breaker → bias flips to sells. | visuals/01, 02, 03 |
| A Brief on Directional Bias | BTC: 4H bearish with trendline liquidity below → sells all week from breakers/OBs until the trendline liquidity is cleared. A counter-bias buy the same week lost. | visuals/04 |
| How to Find Directional Bias for an Uptrend | GBPJPY 4H HH/HL + trendline + OB zones. The LTF downtrend inside the 4H pullback, then 1H MSS + inducement + 4H OB as the POI → buy. Three 15m continuation buys (1:16, 1:8, 1:5.6) until the last 4H high is taken. | visuals/05–08 |
| How I Analyzed Bitcoin's Directional Bias | Daily: multiple BOS up but the nearest daily POI was never mitigated, so liquidity built above it. The uptrend breaks into a downtrend → the daily OB on the bearish trendline is the area of interest → LTF MSS + inducement + breaker → sell. Target 1 = last external low before the POI triggered, Target 2 = trendline liquidity, final = the untouched daily POI below. Posted a "BTC to 74,500" call. | visuals/09–12 |
| How I Analyzed XAUUSD Hitting a New ATH | 4H BOS + inducement + breaker → bullish bias held ~3 months to the target high. Many LTF buys (30m, 3H OB, 1H) closed at nearby liquidity (trendline liquidity, last high), with R:R up to 1:32. After a new ATH, gold "tends to go higher", so he kept buying. Also USDJPY: 4H downtrend, rally into a 4H OB → MSS + inducement + breaker → sell to the low. | visuals/13–16 |
| How I Analyzed and Traded GBPJPY & XAUUSD (pre-NFP) | GBPJPY: uptrend into a tested resistance → MSS + inducement + OB → confirmation entry → TP at the nearest low/"fake OB" (1:14), with trendline liquidity below as the bigger target. Gold: daily breaker = bullish bias, 3H MSS after the downtrend + inducement + 3H OB → buy to clear the bearish trendline liquidity. He says he ignores the news. | visuals/17–20 |
| PipslayerFX explainer | The breaker-vs-OB rule, drawn for bullish and bearish cases. Work with candle **bodies**. Target the nearest swing. | visuals/21–23 |
| Toni Iyke Insights recap | XAUUSD 45m/15m continuation buys from breakers after a low sweep and MSS. | visuals/24–25 |

---

## 4. Risk & position sizing (his lot-size video, which is sound)
`lot size = risk_in_USD ÷ pip_value_per_lot ÷ stop_in_pips`
- **USD-quote pairs** (EURUSD, GBPUSD, AUDUSD): pip value ≈ **$10** per lot.
- **JPY pairs** (GBPJPY, USDJPY, EURJPY, AUDJPY): he uses ≈ **$6.62** per lot. It floats with the USDJPY rate, so the bot should compute it live.
- **Gold/silver/oil**: pip value **$10** per lot, but **multiply the displayed price distance by 10** to get pips (a 3.58 move = 35.8 pips).
- Check the result: `lot × pip value × TP pips` should equal `risk × R:R`.
- **For the bot:** use a fixed fraction (e.g. 0.5–1%) per trade. His own plan of "split the deposit into 4 × 25% tries" and going all-in on the last try is gambling-level risk.

---

## 5. Habits/rules he states
- Only trade **with** the 4H bias. Counter-bias trades are the losses he highlights (the BTC buy).
- **Never enter on the first touch of a zone.** Always wait for the LTF model at that zone. "Sometimes price can go under the trendline and push back up again."
- The **higher the timeframe** of the zone, the longer the move. A 1-minute bounce is short-lived, while 4H moves can carry a whole week.
- He trades around **2–3 trades per day** maximum and withdraws after every third trade (from the $38k video).
- He's a day trader: he holds 1–2 days at most and re-enters on continuations rather than swinging.
- He ignores news (NFP) and goes by technicals only. **For a bot, add a news filter anyway.**

---

## 6. Bot logic skeleton
```
HTF = 4H (bias), with Daily as context ; LTF = 15m/30m/1H (entries)

# 1. Bias
swings_4h = fractal pivots on 4H
bias = BULL if last two swing highs and lows are HH and HL
       BEAR if LH and LL ; else RANGE
bias_target = last 4H swing high (BULL) / low (BEAR) that is not yet taken
bias persists until bias_target is taken OR a bias-flip event (Step 6)

# 2. Zones
htf_zones = 4H/3H/Daily order blocks + breakers + S/R + trendline touches
with_trend_zones = zones on the pullback side ; opposite_zones = zones in the target direction
zone_failed if price ranges just under a zone and closes through it on first contact

# 3. Entry state machine on LTF (bullish shown)
when price is inside a with_trend_zone (or retracing in bias direction):
   wait MSS: close above the last LTF lower high (multi-swing break = stronger)
   inducement = first pullback low after MSS
   POI = nearest unmitigated breaker beyond the inducement ; if mitigated -> nearest OB
         if none on LTF -> use the HTF OB/breaker
   ENTRY when price takes the inducement and taps the POI
   (missed it? -> confirmation entry: wait for retest of the nearest POI after a new small MSS)

# 4. Orders
stop = beyond POI extreme (+ buffer)
TP1  = last high before POI was triggered / nearest liquidity pool
TP2  = trendline liquidity ; TP3 = bias_target
lot  = risk_usd / pip_value / stop_pips  (risk fixed fraction, NOT his 25%)
max 2–3 trades/day ; close by end of next day if TP not hit (day-trader style; optional)

# 5. Bias flip
if price reaches an opposite_zone OR bias_target is taken:
   run the same MSS -> inducement -> POI model in the opposite direction
   if it triggers -> bias = opposite ; ignore old-direction setups from now on

# 6. Filters
no trades against bias ; no entry on raw zone touch ; skip if no inducement taken ;
news blackout (his choice is to ignore news, the bot shouldn't)
```

---

## 7. How it fits with the other two packs
- Toni = classic **SMC**: bias → zone → MSS → inducement → OB/breaker. It's the closest of the three to standard ICT/SMC wording.
- **Inter Equity** uses the same "inducement" idea but sharpens it: wait for the induced side to be **trapped**. That maps onto Toni's "price must take the inducement before the POI".
- **Romeo CRT** adds candle-range bias and timing (Candle 3, 50% target), which Toni's notes lack.
- One combined bot could use CRT/4H structure for bias, Toni's HTF zones + MSS → inducement → POI for setups, and Inter Equity's liquidity-block stop placement.

---

## 8. Training-data idea
His GBPJPY, BTC and gold examples have clear labels (zone, MSS, inducement, POI, entry, stop, TP). The visuals folder works as a seed set. Tag each image with: timeframe, bias, zone type, MSS point, inducement point, POI type (OB/breaker, mitigated or not), entry, stop, TP and outcome.

---

## 9. Gaps (he keeps these for his paid class; define them before coding)
1. **His POI "criteria"**: which OB/breaker qualifies. Default to the breaker-vs-OB mitigation rule plus "nearest to the inducement".
2. The exact **order-block definition** ("specific shapes") and **breaker definition**. Suggested: OB = the last opposite-colour candle before the displacement that caused the MSS. Breaker = the swing zone broken during the MSS.
3. **Swing size** for MSS and inducement on each timeframe (e.g. a 3-bar fractal).
4. **How to draw a trendline** objectively (connect the last 2–3 swing lows/highs).
5. The **"first-time reversal" concept** in depth (he mentions it but doesn't explain it).
6. **Session/time rules**: none given. He trades whenever a setup forms, including on Sunday.

---

## Sources
- [A Brief on Directional Bias (Toni Iyke)](https://www.youtube.com/watch?v=sI25I60QcJ4)
- [How To Find Directional Bias For An Uptrend](https://www.youtube.com/watch?v=hrUak8PxnxU)
- [How I Analyzed Bitcoin's Directional Bias](https://www.youtube.com/watch?v=6m5grLNlQoA)
- [How I Analyzed XAUUSD Hitting A New ATH (plus NFP, XAUUSD, USDJPY)](https://www.youtube.com/watch?v=MeFspWSXdJs)
- [How I Analyzed And Traded GBPJPY & XAUUSD (Pre NFP)](https://www.youtube.com/watch?v=zf18d6I-XMo)
- [How I Made $38,000 Trading in 5 Days](https://www.youtube.com/watch?v=0UQzHudBono)
- [How To Calculate Lot Sizes And Risk (USD, JPY pairs, XAUUSD)](https://www.youtube.com/watch?v=bvpQXbhVjuQ)
- How To Calculate Lot Sizes (Crypto pairs on forex brokers) (V_vtWzY5l9o): not transcribed, it's crypto lot-size arithmetic only
- [TONY IYKE STRATEGY EXPLAINED, PipslayerFX](https://www.youtube.com/watch?v=Jh7B0QRyYGc) (third party)
- [Breakdown on the XAUUSD trades I took this week, Toni Iyke Insights](https://www.youtube.com/watch?v=35s-ppWDSUU) (third-party channel, frames only)

## Visual index
| File | Shows |
|---|---|
| visuals/01 | GBPJPY 4H: directional bias, the 4H OB below, two 4H resistances above |
| visuals/02 | GBPJPY 15m: repeated buys (position boxes) after the 4H OB tap |
| visuals/03 | GBPJPY: price reaches the 4H resistance → sells begin (bias flip) |
| visuals/04 | BTC: sells from breakers targeting trendline liquidity |
| visuals/05 | His sketch of the 3 market states (uptrend, downtrend, range) |
| visuals/06 | GBPJPY 4H uptrend: HH/HL, trendline, OB zones |
| visuals/07 | Sketch: LTF downtrend inside the 4H pullback zone, then the reversal up |
| visuals/08 | GBPJPY LTF buy from the 4H OB on the trendline |
| visuals/09 | BTC daily: untouched POI, liquidity built above it |
| visuals/10 | BTC daily downtrend: trendline + OB area of interest, sell |
| visuals/11 | BTC LTF sell entry after MSS + inducement + breaker |
| visuals/12 | BTC targets: last external low, trendline liquidity, HTF POI |
| visuals/13 | XAUUSD 4H: bullish bias held ~3 months to the target high |
| visuals/14 | XAUUSD: BOS + inducement + POI sketch with buys |
| visuals/15 | XAUUSD: multiple continuation buys |
| visuals/16 | USDJPY 4H: rally into a bearish OB, then sell continuation |
| visuals/17 | GBPJPY: resistance → MSS + inducement + OB sell |
| visuals/18 | GBPJPY sell TP at the nearest low/fake OB; trendline liquidity below |
| visuals/19 | XAUUSD: daily breaker bias, buy |
| visuals/20 | XAUUSD 3H: MSS after the downtrend, buy targeting bearish trendline liquidity |
| visuals/21–23 | PipslayerFX: bullish and bearish MSS → inducement → breaker/OB diagrams, gold 30m example |
| visuals/24–25 | Toni Iyke Insights: XAUUSD 45m/15m continuation buys |
| schematics/01 | Entry model: HTF zone → LTF MSS → inducement → POI, with stop and TP |
| schematics/02 | Directional bias: keep buying continuations until the last 4H high is taken |
| schematics/03 | POI selection: unmitigated breaker vs order block |

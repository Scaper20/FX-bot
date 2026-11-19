# Strategy spec v1.1 (CRT + ICT, MSnR experimental) — approved by Ore 20 Nov 2026

Status column: **Ore** = Ore's answer (20 Nov 2026). **Claude** = my proposal where Ore said "test it" or "you decide". **Test** = several options will be measured, not chosen in advance.
Nothing here is promised to work. Every number shown on the site comes from a run, with sample size and date range.

## 1. Basics
| Rule | Choice | Status |
|---|---|---|
| Broker / platform | Exness, MT5 | Ore |
| Candle day | Exness MT5 server = GMT+0 (Ore saw the Sunday candle). D1 = 00:00–24:00 UTC, H4 opens 00, 04, 08, 12, 16, 20 UTC, Sunday-evening candle included and labelled | Ore confirmed |
| Pairs | GBP/USD, XAU/USD (spot) | Ore |
| Range → entry | D1 → H1 or M15; H4 → M15 or M5 | Ore |
| Minimum reward:risk | 1:3 to at least one target, after costs | Ore |
| Costs | Ore doesn't factor spread in, but the backtest must. Assumed per trade, spread + slippage: GBP/USD 1.0 pip, XAU/USD $0.35. Every result is also shown at double cost. Ore's account: Exness Standard (no commission). Replace with his real spreads when he sends them. | Claude |

## 2. CRT: range and sweep
| Rule | Choice | Status |
|---|---|---|
| Range | High, low and 50% of a completed D1 or H4 candle (candle 1) | Ore |
| Sweep | Candle 2 trades beyond one side and closes back inside the range | Ore |
| Which candle may sweep | The next candle; the second candle allowed as a separate, labelled variant | Ore + Test |
| Close position | Anywhere inside. Recorded as a number (0 = at the swept edge, 1 = at the far edge) so we can see whether deeper closes do better | Ore + Test |
| Both sides swept by candle 2 | Skipped (no clear direction) | Claude |
| Range filters | None | Ore |
| Expiry | The idea stays armed during candle 3 (the next range candle). Cancelled if no entry by its close, or if price reaches the target first | Claude (Ore didn't know). Test 1 vs 2 candles |

## 3. ICT: entry-timeframe confluences
All are optional and all add confidence (Ore). The backtest records which ones were present on each trade, then measures every combination, so nothing is assumed mandatory. Definitions follow Ore's reference pictures; a short bearish example for each (bullish is the mirror):

| Confluence | Definition (bearish example) | Status |
|---|---|---|
| CISD | Take the run of consecutive up-close candles that made the sweep high. CISD = the first later candle that **closes below the open of the first candle in that run** | Ore's picture |
| MSS | A candle closes below the most recent entry-timeframe swing low (swing = a low with 2 higher lows on each side) formed before the sweep high | Claude |
| FVG | 3 candles where candle 3's high is below candle 1's low, formed in the move down from the sweep high. Gap = candle 1 low to candle 3 high | Ore's picture |
| Order block | The last up-close candle before the move down that caused the CISD or MSS. Valid only if it took liquidity (its high ran above the previous candle's high) **and** the move away left an FVG | Ore's picture |
| Killzone | Trigger happens in London 07:00–10:00 London time, or New York 08:30–11:00 New York time (daylight saving handled) | Claude, ICT common use |
| Breaker block | Planned for v2, not in the first run | Claude |

## 3b. Higher-timeframe confluences (added by Ore on approval)
Recorded on every setup and measured like the others. Bearish example; bullish is the mirror.
| Confluence | Definition | Status |
|---|---|---|
| HTF FVG overlap | The sweep (from the range high up to the sweep high) overlaps a bearish FVG on the range timeframe (and on D1 when the range is H4) that formed before the range candle, within 60 candles, and that price has not traded fully through | Ore, definition Claude |
| HTF order block overlap | Same, with a bearish order block: an up-close candle followed by a bearish FVG, zone from its open to its high, not closed above since | Ore, definition Claude |
| HTF MSS | The sweep candle closes below the latest confirmed swing low on the range timeframe | Ore, definition Claude |
| Mid-timeframe MSS | After the sweep high, a candle one timeframe down (D1 range: H4; H4 range: H1) closes below the latest swing low before the high, by the time of entry | Claude, to match "in the same process" |

## 4. Entry, stop, targets (tested; site shows the options ranked)
| Item | Options | Status |
|---|---|---|
| Entry | E1 market at the trigger candle close · E2 limit at FVG near edge · E3 limit at FVG middle · E4 limit at order-block open · E5 limit at order-block middle | Ore: "rank them" → Test |
| Stop | S1 beyond sweep extreme + cost buffer · S2 beyond the order block / FVG far edge + buffer (tightest) | Ore: "tight" → Test |
| Targets | T1 range 50% · T2 opposite side of range · T3 next untaken range-timeframe swing beyond T2 | Ore + Test |
| Management | M1 full position to one target · M2 half off at 50%, stop to breakeven, rest to T2 or T3 | Ore (partials) → Test |
| Fill rules | Unchanged from CLAUDE.md: stop first if both are hit in one candle; on the fill candle only the stop is checked; unfilled orders cancelled at expiry and counted | Agreed |

## 5. MSnR (experimental, Ore: "pick the best and see if it helps")
Levels from **closes** on the range timeframe. A-level = close of an up candle followed by a down candle. V-level = close of a down candle followed by an up candle. Fresh until a wick touches it; a body close through it makes it fresh again. Recorded as a confluence: **the sweep extreme sits within 0.1 × D1 ATR of a fresh level**. It is used only if it improves results on the check period (section 6). Gap levels and storyline are left out of v1.

## 6. How "many iterations" is done without fooling ourselves
Testing many combinations finds lucky ones by chance. Protections, fixed **before** looking at results:
1. **Three periods.** Design: Nov 2021 – Dec 2023. Check: 2024. Final: 2025 – Nov 2026, run **once** at the end.
2. A variant counts only if it has **≥ 60 trades in Design with average R > 0 after costs, then average R > 0 on ≥ 25 trades in Check**. The number of variants tried is always reported.
3. **Baseline:** the same setups with a coin-flip direction. A variant must beat it clearly.
4. **Noise check:** run on random price series; the setup rate there is reported.
5. **Double-cost check:** a variant that only works at the assumed cost is flagged.
6. After the Final run, the rules don't change. Any later change makes the Final result "contaminated", and the site will say so.

## 7. On the site
"Find me a setup" lists **all** current setups that meet the 1:3 rule, ranked by measured after-cost average R of that exact variant. Each one shows its sample size and dates, a confluence checklist, and the entry options ranked. If nothing qualifies, it says so.

## Details fixed while building (Claude)
- If price goes above the sweep high before the trigger, the setup is cancelled (the stop would have been hit).
- A pending limit order is cancelled if price reaches the 50% level before it fills.
- An open trade is closed at market after 5 range candles (D1: 5 days, H4: 20 hours) if neither stop nor target has been hit. Counted separately.
- Trades are simulated on 1-minute candles. Data is bid prices: buys fill and shorts exit at bid + spread.
- A limit entry is skipped if price is already past it when the trigger fires (no chasing).

## Still open
- Ore's real Exness Standard spreads (Market Watch → Columns → Spread).

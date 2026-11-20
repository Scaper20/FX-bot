# My test: does Ore's judgment add an edge? (rules fixed 20 Nov 2026, before any result)

Ore chose options 1 and 2: measure his own judgment, and trade only demo or tiny size while the evidence builds. The site checks these rules on the **My test** page (`/plan`, `web/plan.py`). The rules don't change after results come in.

## What counts
- **Live test (the real one):** live setups Ore marked **Take**, that filled and finished, scored with the option he picked, after spread. Only setups logged by the site count (logged at first show, before the outcome is known).
- **Practice (supporting only):** the same numbers on the 400 historical practice charts. They're faster to collect, but Ore may half-remember those markets, so they never decide on their own.
- **Chance:** what a coin flip would make on the same trades after spread (each option's `chance_avg_R`).
- **Selection:** the average result (top option) of setups he Took minus those he Skipped.

## Checkpoints
| Finished live Takes | What happens |
|---|---|
| under 30 | Too early. Keep reviewing. |
| 30 | First read. If edge vs chance has z ≤ −2 (clearly worse), stop real money and go back to demo. Otherwise carry on. |
| 100 | **Decision.** PASS if edge vs chance > 0 with z ≥ 2 **and** selection > 0. Otherwise FAIL. |

PASS means his judgment very likely adds something. FAIL means no evidence it does: stay on demo, or stop trading this method.

## Money rules
- Before PASS: demo account, or real money at **0.25% of the balance per trade at most**.
- After PASS: up to **0.5%** for the next 100 trades, then check again. **Never above 1%.**
- **Pause** (back to demo, and read the journal before going on) if his recorded trades are **10R below their best point**, or after **8 losses in a row**.
- Every trade he actually places gets its result recorded on the setup page (entry, exit, R). Trades not recorded there don't count.
- **Execution gap:** the R of his recorded trades minus the system's R on the same setups. If it's worse than −0.2R per trade on average, his execution or spread is eating the edge.
- Spreads in Settings must be his real Exness Standard spreads, or every number is off.

"""Spec v13 (docs/spec-v13-expiry-cancel.md): limit orders with/without expiry and with/without the
cancel-at-50% rule, on exactly the same orders. v1.4 engine (body-close rule), all years.

    python -m backtest.expiry_test
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.pattern_stats import ore_rules  # noqa: E402
from engine import config as K  # noqa: E402
from engine.candles import clean, load_m1_csv  # noqa: E402
from engine.setups import Market, find_orders  # noqa: E402
from engine.simulate import simulate  # noqa: E402

OUT = ROOT / "backtest" / "out"
REPORT = ROOT / "backtest" / "reports" / "expiry_cancel_v13.md"
NO_EXPIRY_CANDLES = 20
VARIANTS = {"A": (True, True), "B": (False, True), "C": (True, False), "D": (False, False)}   # (expires, cancel50)
LABEL = {"A": "A. Current (expires, cancels at 50%)", "B": "B. No expiry", "C": "C. No 50% cancel",
         "D": "D. Neither"}
YEARS = range(2022, 2027)


def run_pair(pair: str) -> list[dict]:
    spread = K.PAIRS[pair]["spread"]
    m1, _ = clean(load_m1_csv(ROOT / K.PAIRS[pair]["file"]))
    rows = []
    for period, (a, b) in K.PERIODS.items():
        start, end = pd.Timestamp(a, tz="UTC"), pd.Timestamp(b, tz="UTC")
        mkt = Market(m1, data_end=end + pd.Timedelta("60D"))     # room for 20-candle no-expiry orders
        for range_tf, entry_tfs in K.RANGE_TO_ENTRY.items():
            R0 = mkt.view[(range_tf, False)]
            idx = [i for i in range(len(R0.o)) if start.value <= R0.t_open[i] < end.value]
            for entry_tf in entry_tfs:
                for mir in (False, True):
                    M = mkt.view[("M1", mir)]
                    R = mkt.view[(range_tf, mir)]
                    for i in idx:
                        for k in (1, 2):
                            orders, _ = find_orders(mkt, range_tf, entry_tf, i, k, mir, spread)
                            for o in orders:
                                rr2 = o["rr"].get("T2")
                                if o["market"] or o["stop_type"] != "S1p" or rr2 is None or rr2 < K.MIN_RR:
                                    continue                     # Ore's 1:3 minimum to the far side, as in backtest.run
                                st = int(np.searchsorted(M.t_open, o["t_dec"], side="left"))
                                j = int(np.searchsorted(R.t_close, o["t_dec"], side="left")) + NO_EXPIRY_CANDLES
                                far = int(R.t_close[min(j, len(R.t_close) - 1)])
                                ends = {True: int(np.searchsorted(M.t_open, o["t_end"][2], side="left")),
                                        False: int(np.searchsorted(M.t_open, far, side="left"))}

                                def hold_end(fill_idx, o=o):
                                    t0 = M.t_close[fill_idx] if fill_idx >= 0 else o["t_dec"]
                                    jj = int(np.searchsorted(R.t_close, t0, side="left")) + K.HOLD_RANGE_CANDLES - 1
                                    t_stop = R.t_close[jj] if jj < len(R.t_close) else M.t_close[-1]
                                    return int(np.searchsorted(M.t_open, t_stop, side="left"))

                                fs, xs = (spread, 0.0) if mir else (0.0, spread)
                                base = {"pair": pair, "range_tf": range_tf, "entry_tf": entry_tf, "k": k,
                                        "direction": "long" if mir else "short", "trigger": o["trigger"],
                                        "entry_type": o["entry_type"], "range_open": o["range_open"],
                                        "decision_time": o["decision_time"], "session": o["session"],
                                        "friday_late": o["friday_late"], "trend_struct": o["trend_struct"],
                                        "htf_ob": o["htf_ob"], "htf_fvg": o["htf_fvg"]}
                                for v, (expires, cancel50) in VARIANTS.items():
                                    sim = simulate(M.h, M.l, M.c, st, ends[expires], hold_end, entry=o["entry"],
                                                   market=False, stop=o["stop"], targets=o["targets"],
                                                   t1=o["targets"]["T1"], fill_shift=fs, exit_shift=xs,
                                                   cancel_at_t1=cancel50)
                                    res = sim.get("results", {})
                                    rows.append({**base, "variant": v, "status": sim["status"],
                                                 "R_all_out": (res.get("M1_T2") or {}).get("R"),
                                                 "R_half": (res.get("M2_T2") or {}).get("R")})
        print(pair, period, len(rows), flush=True)
    return rows


def fmt(x, p="+.3f"):
    return "—" if x is None or x != x else format(x, p)


def main() -> int:
    rows = []
    for pair in K.PAIRS:
        rows += run_pair(pair)
    d = pd.DataFrame(rows)
    d["year"] = pd.to_datetime(d["decision_time"], utc=True).dt.year
    d["ore"] = ore_rules(d)
    key = ["pair", "range_tf", "range_open", "direction", "entry_type"]
    d = d.sort_values("decision_time")
    d.to_csv(OUT / "expiry_test.csv", index=False)
    lines = ["# Spec v13 result: limit orders with and without expiry / the cancel-at-50% rule", "",
             "Spec: `docs/spec-v13-expiry-cancel.md` (committed before the run). v1.4 engine (C2 closes inside C1's body), "
             "Nov 2021 – Nov 2026, GBP/USD + gold, Ore's spreads, limit entries E2–E5, stop = sweep + 2 spreads, "
             "one trade per setup per entry type.", ""]
    verdict = {}
    for scope, sub in (("Ore's rules", d[d["ore"]]), ("All setups", d)):
        for mg, mlabel in (("R_half", "half at 50%, stop to entry, rest at far side"), ("R_all_out", "all out at far side")):
            lines += [f"## {scope} · {mlabel}", "",
                      "| Version | Orders | Filled | Avg R (filled) | " + " | ".join(str(y) for y in YEARS)
                      + " | Extra trades vs A | Extra trades avg R | Extra: years + |",
                      "|---|---|---|---|" + "---|" * len(YEARS) + "---|---|---|"]
            per = {}
            for v in VARIANTS:
                x = sub[sub["variant"] == v].drop_duplicates(key)
                per[v] = x.set_index(key)
            for v in VARIANTS:
                x = per[v]
                f = x[x["status"] == "filled"]
                yr = f.groupby("year")[mg].mean()
                extra_txt = ("—", "—", "—")
                ex = None
                if v != "A":
                    a = per["A"]
                    joined = x.join(a[["status"]], rsuffix="_A")
                    ex = joined[(joined["status"] == "filled") & (joined["status_A"] != "filled")]
                    eyr = ex.groupby("year")[mg].mean()
                    extra_txt = (str(len(ex)), fmt(ex[mg].mean()), f"{int(sum(1 for y in YEARS if eyr.get(y, -1) > 0))} of 5")
                lines.append(f"| {LABEL[v]} | {len(x)} | {len(f)} ({len(f) / max(len(x), 1):.0%}) | **{fmt(f[mg].mean())}** | "
                             + " | ".join(fmt(yr.get(y, np.nan), "+.2f") for y in YEARS)
                             + f" | {extra_txt[0]} | {extra_txt[1]} | {extra_txt[2]} |")
                if scope == "Ore's rules" and mg == "R_half":
                    verdict[v] = (f[mg].mean(), None if ex is None else ex[mg].mean(),
                                  None if ex is None else int(sum(1 for y in YEARS
                                                                  if ex.groupby("year")[mg].mean().get(y, -1) > 0)))
            lines.append("")
    # per entry type, Ore's rules, half management
    lines += ["## By entry, Ore's rules · half at 50% (average R per filled trade; filled count)", "",
              "| Entry | " + " | ".join(LABEL[v] for v in VARIANTS) + " |", "|---|" + "---|" * len(VARIANTS)]
    o = d[d["ore"]]
    for e, lab in (("E2", "FVG edge"), ("E3", "FVG middle"), ("E4", "OB open"), ("E5", "OB middle")):
        cells = []
        for v in VARIANTS:
            x = o[(o["variant"] == v) & (o["entry_type"] == e)].drop_duplicates(key)
            f = x[x["status"] == "filled"]
            cells.append(f"{fmt(f['R_half'].mean())} ({len(f)})")
        lines.append(f"| {lab} | " + " | ".join(cells) + " |")
    a_avg = verdict["A"][0]
    lines += ["", "## Verdict (spec rule: Ore's rules, half management)", ""]
    for v in ("B", "C", "D"):
        avg, ex_avg, ex_years = verdict[v]
        ok = avg > a_avg and (ex_avg or -1) > 0 and (ex_years or 0) >= 3
        lines.append(f"- {LABEL[v]}: avg {fmt(avg)} vs current {fmt(a_avg)}; extra trades {fmt(ex_avg)}, "
                     f"positive in {ex_years} of 5 years -> **{'BETTER than current' if ok else 'not better'}**")
    REPORT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

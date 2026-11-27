"""Spec v23 (docs/spec-v23-irl-erl.md): IRL -> ERL bias for the order-block strategy.

    python -m backtest.irl_erl_v23 PAIR     (one market -> backtest/out/v23_PAIR.csv)
    python -m backtest.irl_erl_v23          (report -> backtest/reports/irl_erl_v23.md)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.advanced import START, Outcome  # noqa: E402
from backtest.ob_v21 import ohlc, trend_lookup  # noqa: E402
from backtest.patterns import FRESH, MAIN, MARKETS  # noqa: E402
from engine.candles import clean, load_m1_csv, resample  # noqa: E402
from engine.smc_models import orderblock_setups  # noqa: E402
from engine.smc_structure import external_structure, irl_erl_bias  # noqa: E402

OUT = ROOT / "backtest" / "out"
REPORT = ROOT / "backtest" / "reports" / "irl_erl_v23.md"
YEARS = range(2022, 2027)
BIASES = {"ie_h4": "IRL/ERL H4", "ie_d1": "IRL/ERL D1", "ie_both": "IRL/ERL H4 + D1 agree",
          "trend": "D1 + H4 trend (live rule)", "ie_h4_d1trend": "IRL/ERL H4 + D1 trend", "none": "none"}


def bias_lookup(F):
    b, _ = irl_erl_bias(*ohlc(F))
    cl = pd.DatetimeIndex(F["close_time_utc"]).as_unit("ns").asi8

    def at(t):
        i = int(np.searchsorted(cl, t, side="right")) - 1
        return int(b[i]) if i >= 0 else 0
    return at


def run_pair(pair: str) -> pd.DataFrame:
    mk = MARKETS[pair]
    sp = mk["spread"]
    m1, _ = clean(load_m1_csv(ROOT / mk["file"]))
    m1 = m1[m1.index >= START - pd.Timedelta("400D")]
    D, H4 = resample(m1, "D1", "utc0"), resample(m1, "H4", "utc0")
    td1, th4 = trend_lookup(D), trend_lookup(H4)
    ie_d1, ie_h4 = bias_lookup(D), bias_lookup(H4)
    E = resample(m1, "H1", "utc0")
    o, h, l, c = ohlc(E)
    n = len(c)
    Eo, Ec = E.index.as_unit("ns").asi8, pd.DatetimeIndex(E["close_time_utc"]).as_unit("ns").asi8
    oc, free = Outcome(m1, sp, "H1"), Outcome(m1, 0.0, "H1")
    oc.hold = free.hold = pd.Timedelta("5D").value
    ev = external_structure(o, h, l, c, "close")
    orders = [("OB", s) for s in orderblock_setups(o, h, l, c, ev)]
    for e in ev:                                   # market entry at the MSS close, stop beyond the move's extreme
        if e["kind"] == "MSS":
            p, d = e["protected"], e["dir"]
            orders.append(("E1", {"dir": d, "decision": e["j"], "entry": c[e["j"]],
                                  "far": h[p] if d == -1 else l[p], "valid": 12}))
    rows = []
    for kind, s in orders:
        j, d = s["decision"], s["dir"]
        t = int(Ec[j])
        if t < START.value or j + 1 >= n:
            continue
        e = s["entry"]
        stop = s["far"] + 2 * sp * (-1 if d == 1 else 1)
        if (d == 1 and not stop < e) or (d == -1 and not stop > e):
            continue
        risk = abs(e - stop)
        tgt = e + d * 3 * risk
        side = "long" if d == 1 else "short"
        if kind == "OB":
            win = (int(Eo[j + 1]), int(Ec[min(j + s["valid"], n - 1)]))
            res, r0 = oc(side, e, stop, None, tgt, None, win), free(side, e, stop, None, tgt, None, win)
        else:
            res, r0 = oc(side, e, stop, None, tgt, t, None), free(side, e, stop, None, tgt, t, None)
        if not res or res["R"] is None:
            continue
        bh4, bd1, t1, t4 = ie_h4(t), ie_d1(t), td1(t), th4(t)
        rows.append({"pair": pair, "entry": kind, "side": side, "t_dec": t, "time": res["time"], "R": res["R"],
                     "R_free": r0["R"] if r0 else np.nan, "hit": res["hit_T2"], "chance": res["p_T2"],
                     "ie_h4": bh4 == d, "ie_d1": bd1 == d, "ie_both": bh4 == d and bd1 == d,
                     "trend": t1 == d and t4 == d, "ie_h4_d1trend": bh4 == d and t1 == d, "none": True})
    print(pair, len(rows), flush=True)
    return pd.DataFrame(rows)


def stats(g):
    yr = g.groupby("year")["R"].mean()
    pos = int(sum(1 for y in YEARS if yr.get(y, -1) > 0))
    n = len(g)
    avg = g["R"].mean() if n else np.nan
    hit, ch = (g["hit"].mean() * 100, g["chance"].mean() * 100) if n else (np.nan, np.nan)
    return {"n": n, "avg": avg, "free": g["R_free"].mean() if n else np.nan, "pos": pos, "hit": hit, "ch": ch,
            "yr": yr, "ok": bool(n >= 30 and avg > 0 and pos >= 4 and hit >= ch),
            "t": avg / (g["R"].std() / np.sqrt(n)) if n > 1 and g["R"].std() > 0 else np.nan}


def f(v, p="+.3f"):
    return "—" if v is None or v != v else format(v, p)


def report() -> int:
    from backtest.walkforward import verdict, walk
    d = pd.concat([pd.read_csv(OUT / f"v23_{p}.csv") for p in MARKETS], ignore_index=True)
    d["year"] = pd.to_datetime(d["t_dec"], unit="ns", utc=True).dt.year
    L = ["# Spec v23 result: IRL → ERL bias for the order-block strategy", "",
         "Spec: `docs/spec-v23-irl-erl.md` (committed before the run). H1 MSS, Ore's 2/3-candle order block, 3R "
         "(OB rows) or market entry at the MSS close (E1 rows, for information). Main GBP/USD + gold, fresh EUR/USD + "
         "silver, Nov 2021 – Nov 2026, Ore's spreads.", ""]
    for kind, title in (("OB", "Order-block entry (the live strategy)"), ("E1", "Market entry at the MSS close (does the bias point the right way?)")):
        L += [f"## {title}", "", "| Bias | Trades | No costs | **After spread** | t | Hit vs 25% | "
              + " | ".join(map(str, YEARS)) + " | Yrs + | Consistent | Fresh (trades · avg · yrs+ · hit) | Verdict |",
              "|---|---|---|---|---|---|" + "---|" * len(YEARS) + "---|---|---|---|"]
        x = d[d["entry"] == kind]
        for key, name in BIASES.items():
            g = x[x[key].astype(bool)]
            gm, gf = g[g["pair"].isin(MAIN)], g[g["pair"].isin(FRESH)]
            s, fs = stats(gm), stats(gf)
            fok = fs["n"] >= 30 and fs["avg"] > 0 and fs["pos"] >= 3 and fs["hit"] >= fs["ch"]
            L.append(f"| {name} | {s['n']} | {f(s['free'])} | **{f(s['avg'])}** | {f(s['t'], '+.1f')} | "
                     f"{f(s['hit'], '.0f')}% | " + " | ".join(f(s["yr"].get(y, np.nan), "+.2f") for y in YEARS)
                     + f" | {s['pos']} | {'YES' if s['ok'] else 'no'} | {fs['n']} · {f(fs['avg'])} · {fs['pos']} · "
                     f"{f(fs['hit'], '.0f')}% | " + (("fresh PASS" if fok else "fresh FAIL") if s["ok"] else "") + " |")
        L.append("")
    xm = d[(d["entry"] == "OB") & d["pair"].isin(MAIN)]
    parts = []
    for key in ("ie_h4", "ie_d1", "ie_both", "ie_h4_d1trend"):
        g = xm[xm[key].astype(bool)]
        parts.append(pd.DataFrame({"unit": key + " " + g["pair"], "time": pd.to_datetime(g["time"], unit="ns", utc=True).astype(str),
                                   "R": g["R"]}))
    wf, _ = walk(pd.concat(parts, ignore_index=True))
    v = verdict(wf, "A")
    L += [f"IRL/ERL family walk-forward (order-block entry; choose the variant on past years, trade next year blind, "
          f"2023–26): {f(v['avg'])}R over {v['trades']} trades, positive in {v['years_pos']} of 4 years → "
          f"**{'PASS' if v['pass'] else 'fail'}**.", ""]
    REPORT.write_text("\n".join(L) + "\n")
    # live card history for the IRL/ERL strategy (order-block entry, H4 IRL/ERL + D1 trend), merged into the SMC stats
    import json
    from backtest.smc_v22 import STATS
    allst = json.loads(STATS.read_text()) if STATS.exists() else {}
    g = d[(d["entry"] == "OB") & d["ie_h4_d1trend"].astype(bool)]
    fr = stats(g[g["pair"].isin(FRESH)])
    allst["irl_erl"] = {}
    for pair, gp in g[g["pair"].isin(MAIN)].groupby("pair"):
        sp = stats(gp)
        allst["irl_erl"][pair] = {"n": int(sp["n"]), "avg_R": round(float(sp["avg"]), 3),
                                  "win_rate": round(float((gp["R"] > 0).mean()), 3),
                                  "first": pd.Timestamp(int(gp["t_dec"].min()), tz="UTC").isoformat(),
                                  "last": pd.Timestamp(int(gp["t_dec"].max()), tz="UTC").isoformat(),
                                  "enough": bool(sp["n"] >= 30), "score": round(float(sp["avg"]), 3),
                                  "fresh_avg_R": round(float(fr["avg"]), 3), "fresh_n": int(fr["n"])}
    STATS.write_text(json.dumps(allst, indent=1))
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        df = run_pair(sys.argv[1])
        df.to_csv(OUT / f"v23_{sys.argv[1]}.csv", index=False)
    else:
        raise SystemExit(report())

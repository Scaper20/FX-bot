"""Spec v22 (docs/spec-v22-smc-live.md): order block, Toni Iyke and Lingard on real market structure, using the
same rules module as the live scanner (engine/smc_models.py).

    python -m backtest.smc_v22 PAIR      (one market -> backtest/out/v22_PAIR.csv)
    python -m backtest.smc_v22           (report -> backtest/reports/smc_v22.md, live stats -> engine/data/smc_v22_stats.json)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.advanced import START, Outcome  # noqa: E402
from backtest.ob_v21 import ohlc, trend_lookup  # noqa: E402
from backtest.patterns import FRESH, MAIN, MARKETS, atr  # noqa: E402
from engine.candles import clean, load_m1_csv, resample  # noqa: E402
from engine.sessions import session_flags  # noqa: E402
from engine.smc_models import lingard_setups, orderblock_setups, toni_setups  # noqa: E402
from engine.smc_structure import external_structure  # noqa: E402

OUT = ROOT / "backtest" / "out"
REPORT = ROOT / "backtest" / "reports" / "smc_v22.md"
STATS = ROOT / "engine" / "data" / "smc_v22_stats.json"
HOLD = {"H4": "10D", "H1": "5D", "M15": "2D"}
TFS = {"smc_ob": ("H1",), "toni": ("H1", "M15"), "lingard": ("H4", "H1")}
YEARS = range(2022, 2027)
LIVE = {"smc_ob": ("H1", "3R", "d1h4"), "toni": ("H1", "liq", "d1"), "lingard": ("H4", "5R", "d1")}


def run_pair(pair: str) -> pd.DataFrame:
    mk = MARKETS[pair]
    sp = mk["spread"]
    m1, _ = clean(load_m1_csv(ROOT / mk["file"]))
    m1 = m1[m1.index >= START - pd.Timedelta("400D")]
    d1, h4 = trend_lookup(resample(m1, "D1", "utc0")), trend_lookup(resample(m1, "H4", "utc0"))
    rows = []
    for tf in ("H4", "H1", "M15"):
        E = resample(m1, tf, "utc0")
        o, h, l, c = ohlc(E)
        n = len(c)
        Eo, Ec = E.index.as_unit("ns").asi8, pd.DatetimeIndex(E["close_time_utc"]).as_unit("ns").asi8
        oc, free = Outcome(m1, sp, tf), Outcome(m1, 0.0, tf)
        oc.hold = free.hold = pd.Timedelta(HOLD[tf]).value
        setups = []
        if tf in TFS["smc_ob"]:
            setups += orderblock_setups(o, h, l, c, external_structure(o, h, l, c, "close"))
        if tf in TFS["toni"]:
            setups += toni_setups(o, h, l, c, external_structure(o, h, l, c, "close"))
        if tf in TFS["lingard"]:
            setups += lingard_setups(o, h, l, c, external_structure(o, h, l, c, "wick"), atr(h, l, c))
        for s in setups:
            j, d = s["decision"], s["dir"]
            t = int(Ec[j])
            if t < START.value or j + 1 >= n:
                continue
            side = "long" if d == 1 else "short"
            e = s["entry"]
            stop = s["far"] + 2 * sp * (-1 if d == 1 else 1)
            risk = abs(e - stop)
            win = (int(Eo[j + 1]), int(Ec[min(j + s["valid"], n - 1)]))
            tg = {"3R": e + d * 3 * risk} if s["model"] == "smc_ob" else {"5R": e + d * 5 * risk}
            if s["liq"] is not None and s["model"] != "smc_ob":
                tg["liq"] = s["liq"]
            for name, tgt in tg.items():
                if (d == 1 and not tgt > e) or (d == -1 and not tgt < e):
                    continue
                res = oc(side, e, stop, None, tgt, None, win)
                if not res or res["R"] is None:
                    continue
                r0 = free(side, e, stop, None, tgt, None, win)
                rows.append({"pair": pair, "tf": tf, "model": s["model"], "struct": s.get("struct", s["variant"]),
                             "variant": s["variant"], "target": name, "side": side, "t_dec": t,
                             "d1": d1(t) == d, "d1h4": d1(t) == d and h4(t) == d,
                             "session": session_flags(pd.Timestamp(t, tz="UTC")) != "",
                             "rr": abs(tgt - e) / risk, "time": res["time"], "R": res["R"],
                             "R_free": r0["R"] if r0 else np.nan, "hit": res["hit_T2"], "chance": res["p_T2"],
                             "e": e, "stop": stop, "tgt": tgt,
                             "zone": f"{Eo[s['zone'][0]]};{Eo[s['zone'][1]]};{s['zone'][2]};{s['zone'][3]}",
                             "line": f"{Eo[s['line'][0]]};{Eo[s['line'][1]]};{s['line'][2]};{s['line'][3]}",
                             "dec_open": int(Eo[j])})
        print(pair, tf, "done", sum(r["tf"] == tf for r in rows), flush=True)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ report


def stats(g):
    yr = g.groupby("year")["R"].mean()
    pos = int(sum(1 for y in YEARS if yr.get(y, -1) > 0))
    n = len(g)
    avg = g["R"].mean() if n else np.nan
    hit, ch = (g["hit"].mean() * 100, g["chance"].mean() * 100) if n else (np.nan, np.nan)
    return {"n": n, "avg": avg, "free": g["R_free"].mean() if n else np.nan, "pos": pos, "hit": hit, "ch": ch,
            "yr": yr, "ok": bool(n >= 30 and avg > 0 and pos >= 4 and hit >= ch),
            "t": avg / (g["R"].std() / np.sqrt(n)) if n > 1 and g["R"].std() > 0 else np.nan,
            "win": float((g["R"] > 0).mean()) if n else np.nan}


def f(v, p="+.3f"):
    return "—" if v is None or v != v else format(v, p)


def rows_for(d, model):
    x = d[d["model"] == model]
    if model == "lingard":
        x = x[x["session"] & ((x["target"] == "5R") | (x["rr"] >= 5))]
    keys = ["struct", "tf", "target"] if model == "toni" else ["tf", "target"]
    bias = "d1h4" if model == "smc_ob" else "d1"
    for vals, g in x.groupby(keys):
        vals = vals if isinstance(vals, tuple) else (vals,)
        for b in (True, False):
            yield vals, b, (g[g[bias]] if b else g)


def report() -> int:
    from backtest.walkforward import verdict, walk
    d = pd.concat([pd.read_csv(OUT / f"v22_{p}.csv") for p in MARKETS], ignore_index=True)
    d["year"] = pd.to_datetime(d["t_dec"], unit="ns", utc=True).dt.year
    L = ["# Spec v22 result: order block, Toni Iyke and Lingard on real market structure", "",
         "Spec: `docs/spec-v22-smc-live.md` (committed before the run). Rules: `engine/smc_models.py` (same code as the "
         "live scanner). Main test GBP/USD + gold, fresh check EUR/USD + silver, Nov 2021 – Nov 2026, Ore's spreads.", ""]
    live_stats = {}
    names = {"smc_ob": "Order block (H1 MSS, Ore's 2/3-candle block, D1+H4 trend)", "toni": "Toni Iyke",
             "lingard": "Lingard"}
    for model in ("smc_ob", "toni", "lingard"):
        hdr = {"toni": "| Structure | TF | Target |", "lingard": "| TF | Target |", "smc_ob": "| TF | Target |"}[model]
        L += [f"## {names[model]}", "", hdr + " Bias | Trades | No costs | **After spread** | t | Hit vs chance | "
              + " | ".join(map(str, YEARS)) + " | Yrs + | Consistent | Fresh (trades · avg · yrs+) | Verdict |",
              "|" + "---|" * (hdr.count("|") - 1) + "---|---|---|---|---|---|" + "---|" * len(YEARS) + "---|---|---|---|"]
        for vals, b, g in rows_for(d, model):
            gm, gf = g[g["pair"].isin(MAIN)], g[g["pair"].isin(FRESH)]
            s, fs = stats(gm), stats(gf)
            fok = fs["n"] >= 30 and fs["avg"] > 0 and fs["pos"] >= 3 and fs["hit"] >= fs["ch"]
            L.append("| " + " | ".join(map(str, vals)) + f" | {'on' if b else 'off'} | {s['n']} | {f(s['free'])} | "
                     f"**{f(s['avg'])}** | {f(s['t'], '+.1f')} | {f(s['hit'], '.0f')}% vs {f(s['ch'], '.0f')}% | "
                     + " | ".join(f(s["yr"].get(y, np.nan), "+.2f") for y in YEARS)
                     + f" | {s['pos']} | {'YES' if s['ok'] else 'no'} | {fs['n']} · {f(fs['avg'])} · {fs['pos']} | "
                     + (("fresh PASS" if fok else "fresh FAIL") if s["ok"] else "") + " |")
            tf, tg, bias = LIVE[model]
            if b and vals[-2:] == (tf, tg) and (model != "toni" or True):
                key = model if model != "toni" else f"toni_{vals[0]}"
                for pair, gp in gm.groupby("pair"):
                    sp_ = stats(gp)
                    live_stats.setdefault(key, {})[pair] = {
                        "n": int(sp_["n"]), "avg_R": round(float(sp_["avg"]), 3), "win_rate": round(sp_["win"], 3),
                        "first": pd.Timestamp(int(gp["t_dec"].min()), tz="UTC").isoformat(),
                        "last": pd.Timestamp(int(gp["t_dec"].max()), tz="UTC").isoformat(),
                        "enough": bool(sp_["n"] >= 30), "score": round(float(sp_["avg"]), 3),
                        "fresh_avg_R": round(float(fs["avg"]), 3) if fs["n"] else None, "fresh_n": int(fs["n"])}
        x = d[(d["model"] == model) & d["pair"].isin(MAIN)]
        if model == "lingard":
            x = x[x["session"] & ((x["target"] == "5R") | (x["rr"] >= 5))]
        unit = x["struct"].astype(str) + " " + x["tf"] + " " + x["target"] + " " + x["pair"]
        wf, _ = walk(pd.DataFrame({"unit": unit, "time": pd.to_datetime(x["time"], unit="ns", utc=True).astype(str),
                                   "R": x["R"]}))
        v = verdict(wf, "A")
        L += ["", f"Walk-forward (choose on past years, trade next year blind, 2023–26): {f(v['avg'])}R over "
              f"{v['trades']} trades, positive in {v['years_pos']} of 4 years → **{'PASS' if v['pass'] else 'fail'}**.", ""]
    REPORT.write_text("\n".join(L) + "\n")
    STATS.write_text(json.dumps(live_stats, indent=1))
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        df = run_pair(sys.argv[1])
        df.to_csv(OUT / f"v22_{sys.argv[1]}.csv", index=False)
        print(sys.argv[1], len(df), "trades")
    else:
        raise SystemExit(report())

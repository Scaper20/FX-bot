"""Spec v24 (docs/spec-v24-ore-model.md): Ore's liquidity model, reversal (OB / BB) and continuation (BB).

    python -m backtest.ore_v24 PAIR      (one market -> backtest/out/v24_PAIR.csv)
    python -m backtest.ore_v24           (report -> backtest/reports/ore_model_v24.md)
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
from engine.smc_models import ore_continuation_setups, ore_reversal_setups  # noqa: E402
from engine.smc_structure import external_structure, ore_order_block  # noqa: E402

OUT = ROOT / "backtest" / "out"
REPORT = ROOT / "backtest" / "reports" / "ore_model_v24.md"
TFS = ("H1", "M15", "M5")
HOLD = {"H1": "10D", "M15": "5D", "M5": "3D"}
YEARS = range(2022, 2027)


def htf_zones(F) -> list[tuple]:
    """H4 POIs: (known_at_ns, low, high, dir): FVGs (dir = the side they would sell/buy from) and Ore's order blocks
    at H4 structure origins."""
    o, h, l, c = ohlc(F)
    cl = pd.DatetimeIndex(F["close_time_utc"]).as_unit("ns").asi8
    zs = []
    for x in range(len(c) - 2):
        if h[x + 2] < l[x]:
            zs.append((int(cl[x + 2]), h[x + 2], l[x], -1))          # bearish FVG: sell zone
        if l[x + 2] > h[x]:
            zs.append((int(cl[x + 2]), h[x], l[x + 2], 1))
    for e in external_structure(o, h, l, c, "close"):
        p = e["protected"]
        ob = ore_order_block(o, h, l, c, p, e["dir"], ahead=max(0, min(2, e["j"] - p)))
        if ob:
            zs.append((int(cl[e["j"]]), min(ob["near"], ob["far"]), max(ob["near"], ob["far"]), e["dir"]))
    return zs


def run_pair(pair: str) -> pd.DataFrame:
    mk = MARKETS[pair]
    sp = mk["spread"]
    m1, _ = clean(load_m1_csv(ROOT / mk["file"]))
    m1 = m1[m1.index >= START - pd.Timedelta("400D")]
    d1 = trend_lookup(resample(m1, "D1", "utc0"))
    zones = htf_zones(resample(m1, "H4", "utc0"))
    zt = np.array([z[0] for z in zones], dtype=np.int64)
    rows = []
    for tf in TFS:
        E = resample(m1, tf, "utc0")
        o, h, l, c = ohlc(E)
        n = len(c)
        Eo, Ec = E.index.as_unit("ns").asi8, pd.DatetimeIndex(E["close_time_utc"]).as_unit("ns").asi8
        oc, free = Outcome(m1, sp, tf), Outcome(m1, 0.0, tf)
        oc.hold = free.hold = pd.Timedelta(HOLD[tf]).value
        ev = external_structure(o, h, l, c, "close")
        setups = ore_reversal_setups(o, h, l, c, ev) + ore_continuation_setups(o, h, l, c, ev)
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
            htf_poi = False
            if s["model"] == "ore_rev":
                top = s["top"]
                px = h[top] if d == -1 else l[top]
                k = int(np.searchsorted(zt, int(Eo[top]), side="right"))
                htf_poi = any(z[3] == d and z[1] <= px <= z[2] for z in zones[:k][-400:])
            for name, mult in (("3R", 3), ("5R", 5)):
                tgt = e + d * mult * risk
                res = oc(side, e, stop, None, tgt, None, win)
                if not res or res["R"] is None:
                    continue
                r0 = free(side, e, stop, None, tgt, None, win)
                rows.append({"pair": pair, "tf": tf, "model": s["model"], "variant": s["variant"], "shape": s["shape"],
                             "target": name, "side": side, "t_dec": t, "d1": d1(t) == d, "htf_poi": htf_poi,
                             "time": res["time"], "R": res["R"], "R_free": r0["R"] if r0 else np.nan,
                             "hit": res["hit_T2"], "chance": res["p_T2"], "e": e, "stop": stop, "tgt": tgt,
                             "dec_open": int(Eo[j]),
                             "zone": f"{Eo[s['zone'][0]]};{Eo[s['zone'][1]]};{s['zone'][2]};{s['zone'][3]}",
                             "line": f"{Eo[s['line'][0]]};{Eo[s['line'][1]]};{s['line'][2]};{s['line'][3]}",
                             "liq": f"{Eo[s['liq_idx']]};{s['liq_px']}"})
        print(pair, tf, sum(r["tf"] == tf for r in rows), flush=True)
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


def nearest(x: pd.DataFrame) -> pd.DataFrame:
    """Reversal 'nearest' variant: per setup (pair, tf, side, decision, target) the BB if present, else the OB."""
    r = x[x["model"] == "ore_rev"].copy()
    r["pri"] = (r["variant"] != "BB").astype(int)
    return r.sort_values("pri").drop_duplicates(["pair", "tf", "side", "t_dec", "target"]).drop(columns="pri")


def report() -> int:
    from backtest.walkforward import verdict, walk
    d = pd.concat([pd.read_csv(OUT / f"v24_{p}.csv") for p in MARKETS], ignore_index=True)
    d["year"] = pd.to_datetime(d["t_dec"], unit="ns", utc=True).dt.year
    groups = {"Reversal · OB": d[(d["model"] == "ore_rev") & (d["variant"] == "OB")],
              "Reversal · BB": d[(d["model"] == "ore_rev") & (d["variant"] == "BB")],
              "Reversal · nearest (BB, else OB)": nearest(d),
              "Continuation · BB": d[d["model"] == "ore_cont"]}
    L = ["# Spec v24 result: Ore's liquidity model", "",
         "Spec: `docs/spec-v24-ore-model.md` (committed before the run). Main test GBP/USD + gold, fresh check EUR/USD + "
         "silver, Nov 2021 – Nov 2026, Ore's spreads, 1-minute scoring.", "",
         "| Model | TF | Target | Bias | Trades | No costs | **After spread** | t | Hit vs chance | "
         + " | ".join(map(str, YEARS)) + " | Yrs + | Consistent | Fresh (trades · avg · yrs+ · hit) | Verdict |",
         "|---|---|---|---|---|---|---|---|---|" + "---|" * len(YEARS) + "---|---|---|---|"]
    fam = {}
    for gname, g0 in groups.items():
        for tf in TFS:
            for tg in ("3R", "5R"):
                for b in (True, False):
                    g = g0[(g0["tf"] == tf) & (g0["target"] == tg)]
                    g = g[g["d1"]] if b else g
                    gm, gf = g[g["pair"].isin(MAIN)], g[g["pair"].isin(FRESH)]
                    s, fs = stats(gm), stats(gf)
                    fok = fs["n"] >= 30 and fs["avg"] > 0 and fs["pos"] >= 3 and fs["hit"] >= fs["ch"]
                    L.append(f"| {gname} | {tf} | {tg} | {'D1 trend' if b else 'none'} | {s['n']} | {f(s['free'])} | "
                             f"**{f(s['avg'])}** | {f(s['t'], '+.1f')} | {f(s['hit'], '.0f')}% vs {f(s['ch'], '.0f')}% | "
                             + " | ".join(f(s["yr"].get(y, np.nan), "+.2f") for y in YEARS)
                             + f" | {s['pos']} | {'YES' if s['ok'] else 'no'} | {fs['n']} · {f(fs['avg'])} · {fs['pos']} · "
                             f"{f(fs['hit'], '.0f')}% | " + (("fresh PASS" if fok else "fresh FAIL") if s["ok"] else "") + " |")
                    if b:
                        fam.setdefault(gname.split(" · ")[0], []).append(gm.assign(unit=gname + " " + tf + " " + tg + " " + gm["pair"]))
    L.append("")
    for name, parts in fam.items():
        x = pd.concat(parts, ignore_index=True)
        wf, _ = walk(pd.DataFrame({"unit": x["unit"], "time": pd.to_datetime(x["time"], unit="ns", utc=True).astype(str),
                                   "R": x["R"]}))
        v = verdict(wf, "A")
        L.append(f"**{name} family walk-forward** (D1-trend rows; choose on past years, trade next year blind, 2023–26): "
                 f"{f(v['avg'])}R over {v['trades']} trades, positive in {v['years_pos']} of 4 years → "
                 f"**{'PASS' if v['pass'] else 'fail'}**.")
    L += ["", "## Reversal model: did the top start at an H4 POI? (information, D1 trend, all TFs and variants, 3R)", "",
          "| Top at an H4 POI | Trades | After spread | Hit vs chance | Fresh trades · avg |", "|---|---|---|---|---|"]
    r = d[(d["model"] == "ore_rev") & d["d1"] & (d["target"] == "3R")]
    for v_ in (True, False):
        g = r[r["htf_poi"] == v_]
        s, fs = stats(g[g["pair"].isin(MAIN)]), stats(g[g["pair"].isin(FRESH)])
        L.append(f"| {'yes' if v_ else 'no'} | {s['n']} | {f(s['avg'])} | {f(s['hit'], '.0f')}% vs {f(s['ch'], '.0f')}% | "
                 f"{fs['n']} · {f(fs['avg'])} |")
    REPORT.write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        df = run_pair(sys.argv[1])
        df.to_csv(OUT / f"v24_{sys.argv[1]}.csv", index=False)
    else:
        raise SystemExit(report())

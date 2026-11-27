"""Spec v21 (docs/spec-v21-orderblock-rebuild.md): order-block strategy on external structure.
Test A = draft order block; test B = Ore's 2/3-candle order block.

    python -m backtest.ob_v21 PAIR      (one market -> backtest/out/ob21_PAIR.csv)
    python -m backtest.ob_v21           (report -> backtest/reports/orderblock_v21.md)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.advanced import START, Outcome  # noqa: E402
from backtest.patterns import FRESH, MAIN, MARKETS  # noqa: E402
from engine.candles import clean, load_m1_csv, resample  # noqa: E402
from engine.smc_structure import external_structure, ore_order_block, order_block  # noqa: E402

OUT = ROOT / "backtest" / "out"
REPORT = ROOT / "backtest" / "reports" / "orderblock_v21.md"
TFS = ("H1", "M15")
VALID = 12
RR = 3.0
YEARS = range(2022, 2027)


def ohlc(F):
    return tuple(F[k].to_numpy(float) for k in ("open", "high", "low", "close"))


def trend_lookup(F):
    """Function t_ns -> external trend (+1/-1/0) known at t on frame F."""
    ev = external_structure(*ohlc(F), "close")
    cl = pd.DatetimeIndex(F["close_time_utc"]).as_unit("ns").asi8
    ts = np.array([cl[e["j"]] for e in ev], dtype=np.int64)
    dirs = np.array([e["dir"] for e in ev])

    def at(t):
        i = int(np.searchsorted(ts, t, side="right")) - 1
        return int(dirs[i]) if i >= 0 else 0
    return at


def run_pair(pair: str) -> pd.DataFrame:
    mk = MARKETS[pair]
    sp = mk["spread"]
    m1, _ = clean(load_m1_csv(ROOT / mk["file"]))
    m1 = m1[m1.index >= START - pd.Timedelta("400D")]
    d1, h4 = trend_lookup(resample(m1, "D1", "utc0")), trend_lookup(resample(m1, "H4", "utc0"))
    rows = []
    for tf in TFS:
        E = resample(m1, tf, "utc0")
        o, h, l, c = ohlc(E)
        n = len(c)
        Eo, Ec = E.index.as_unit("ns").asi8, pd.DatetimeIndex(E["close_time_utc"]).as_unit("ns").asi8
        after, free = Outcome(m1, sp, tf), Outcome(m1, 0.0, tf)
        after.hold = free.hold = pd.Timedelta("3D").value
        for ev in external_structure(o, h, l, c, "close"):
            if ev["kind"] != "MSS":
                continue
            j, d, p = ev["j"], ev["dir"], ev["protected"]
            t = int(Ec[j])
            if t < START.value or j + 1 >= n:
                continue
            side = "long" if d == 1 else "short"
            bias = d1(t) == d and h4(t) == d
            ext = h[p] if d == -1 else l[p]
            win = (int(Eo[j + 1]), int(Ec[min(j + VALID, n - 1)]))
            orders = [("A", "E1", float(c[j]), ext, t, None, None)]
            ob = order_block(o, h, l, c, p, d)
            if ob:
                far = max(ext, ob["high"]) if d == -1 else min(ext, ob["low"])
                orders.append(("A", "OB", ob["body_edge"], far, None, win, (ob["first"], ob["last"], ob["low"], ob["high"])))
            ob2 = ore_order_block(o, h, l, c, p, d, ahead=min(2, j - p))   # formation complete by the MSS candle
            if ob2:
                far = max(ext, ob2["far"]) if d == -1 else min(ext, ob2["far"])
                box = (ob2["first"], ob2["last"], min(ob2["near"], ob2["far"]), max(ob2["near"], ob2["far"]))
                orders.append(("B", "edge", ob2["near"], far, None, win, box + (ob2["kind"],)))
                orders.append(("B", "body", ob2["body_edge"], far, None, win, box + (ob2["kind"],)))
            for test, entry, e, far, t_ns, w, box in orders:
                stop = far + 2 * sp if d == -1 else far - 2 * sp
                if w is not None and ((d == -1 and e <= c[j]) or (d == 1 and e >= c[j])):
                    continue                                   # limit must be ahead of price
                if (d == -1 and not stop > e) or (d == 1 and not stop < e):
                    continue
                tgt = e - RR * (stop - e)
                res = after(side, e, stop, None, tgt, t_ns, w)
                if not res or res["R"] is None:
                    continue
                r0 = free(side, e, stop, None, tgt, t_ns, w)
                rows.append({"pair": pair, "tf": tf, "test": test, "entry": entry, "side": side, "bias": bias,
                             "t_dec": t, "time": res["time"], "R": res["R"], "R_free": r0["R"] if r0 else np.nan,
                             "hit": res["hit_T2"], "chance": res["p_T2"], "e": e, "stop": stop, "tgt": tgt,
                             "j": int(Eo[j]), "origin": int(Eo[p]), "broken": int(Eo[ev["broken"]]),
                             "level": ev["level"],
                             "box": "" if box is None else f"{Eo[box[0]]};{Eo[box[1]]};{box[2]};{box[3]}"
                                    + (f";{box[4]}" if len(box) > 4 else "")})
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
            "t": avg / (g["R"].std() / np.sqrt(n)) if n > 1 and g["R"].std() > 0 else np.nan}


def f(v, p="+.3f"):
    return "—" if v is None or v != v else format(v, p)


def report() -> int:
    from backtest.walkforward import verdict, walk
    d = pd.concat([pd.read_csv(OUT / f"ob21_{p}.csv") for p in MARKETS], ignore_index=True)
    d["year"] = pd.to_datetime(d["t_dec"], unit="ns", utc=True).dt.year
    L = ["# Spec v21 result: order-block strategy rebuilt on real market structure", "",
         "Spec: `docs/spec-v21-orderblock-rebuild.md` (committed before the run). MSS on the entry timeframe in the "
         "direction of the D1 + H4 external trend; stop beyond the top/bottom of the move + 2 spreads; 3R. Main test "
         "GBP/USD + gold, fresh check EUR/USD + silver, Nov 2021 – Nov 2026, Ore's spreads, 1-minute scoring.", "",
         "For comparison, the **old** live strategy (v16, tiny-swing MSS): H1 OB open with D1+H4 bias +0.27R over "
         "234 trades on GBP/USD + gold, −0.12R on EUR/USD + silver.", ""]
    names = {"A": "Test A: draft order block (last opposite candles at the top/bottom)",
             "B": "Test B: Ore's order block (2-candle engulfing or candle + pin bar + engulfing)"}
    entries = {"E1": "market at MSS close", "OB": "OB body edge", "edge": "first candle's near edge",
               "body": "first candle's body"}
    for test in ("A", "B"):
        x = d[d["test"] == test]
        L += [f"## {names[test]}", "",
              "| TF | Entry | Bias | Trades | No costs | **After spread** | t | Hit vs 25% chance | "
              + " | ".join(map(str, YEARS)) + " | Yrs + | Consistent | Fresh (trades · avg · yrs+ · hit) | Verdict |",
              "|---|---|---|---|---|---|---|---|" + "---|" * len(YEARS) + "---|---|---|---|"]
        for (tf, en), g0 in x.groupby(["tf", "entry"]):
            for b in (True, False):
                g = g0[g0["bias"]] if b else g0
                gm, gf = g[g["pair"].isin(MAIN)], g[g["pair"].isin(FRESH)]
                s, fs = stats(gm), stats(gf)
                fok = fs["n"] >= 30 and fs["avg"] > 0 and fs["pos"] >= 3 and fs["hit"] >= fs["ch"]
                L.append(f"| {tf} | {entries[en]} | {'D1+H4' if b else 'none'} | {s['n']} | {f(s['free'])} | "
                         f"**{f(s['avg'])}** | {f(s['t'], '+.1f')} | {f(s['hit'], '.0f')}% | "
                         + " | ".join(f(s["yr"].get(y, np.nan), "+.2f") for y in YEARS)
                         + f" | {s['pos']} | {'YES' if s['ok'] else 'no'} | "
                         f"{fs['n']} · {f(fs['avg'])} · {fs['pos']} · {f(fs['hit'], '.0f')}% | "
                         + (("fresh PASS" if fok else "fresh FAIL") if s["ok"] else "") + " |")
        xm = x[x["pair"].isin(MAIN)]
        unit = xm["tf"] + " " + xm["entry"] + " " + xm["bias"].map({True: "bias", False: "all"}) + " " + xm["pair"]
        wf, _ = walk(pd.DataFrame({"unit": unit, "time": pd.to_datetime(xm["time"], unit="ns", utc=True).astype(str),
                                   "R": xm["R"]}))
        v = verdict(wf, "A")
        L += ["", f"Walk-forward (choose on past years, trade next year blind, 2023–26): {f(v['avg'])}R over "
              f"{v['trades']} trades, positive in {v['years_pos']} of 4 years → **{'PASS' if v['pass'] else 'fail'}**.", ""]
    b = d[(d["test"] == "B") & (d["entry"] == "edge")]
    kinds = b["box"].str.split(";").str[-1].value_counts()
    L += [f"Order blocks found in test B: {', '.join(f'{k} {v:,}' for k, v in kinds.items())} "
          "(counted on the edge-entry rows, all markets, bias on and off).", ""]
    REPORT.write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        df = run_pair(sys.argv[1])
        df.to_csv(OUT / f"ob21_{sys.argv[1]}.csv", index=False)
        print(sys.argv[1], len(df), "trades")
    else:
        raise SystemExit(report())

"""Spec v25 (docs/spec-v25-htf-poi.md): Ore's reversal model after a fresh higher-timeframe POI tap, variation grid.

    python -m backtest.ore_v25 PAIR      (one market -> backtest/out/v25_PAIR.csv)
    python -m backtest.ore_v25           (report -> backtest/reports/ore_htf_poi_v25.md)
"""
from __future__ import annotations

import itertools
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
from engine.smc_models import ore_reversal_setups  # noqa: E402
from engine.smc_structure import external_structure, ore_order_block  # noqa: E402

OUT = ROOT / "backtest" / "out"
REPORT = ROOT / "backtest" / "reports" / "ore_htf_poi_v25.md"
TFS = ("H1", "M15", "M5")
TF_SEC = {"H1": 3600, "M15": 900, "M5": 300}
HOLD = {"H1": "10D", "M15": "5D", "M5": "3D"}
YEARS = range(2022, 2027)
TAP_WINDOW = 20                # LTF candles before the top in which the zone's first tap must fall
POI_COLS = [f"poi_{h}_{t}" for h in ("H4", "D1") for t in ("OB", "BB", "FVG")]


def htf_zones(F, htf: str) -> pd.DataFrame:
    """Zones on one HTF: created (ns, known at that candle close), lo, hi, dir (+1 buy zone / -1 sell zone), type."""
    o, h, l, c = ohlc(F)
    cl = pd.DatetimeIndex(F["close_time_utc"]).as_unit("ns").asi8
    n = len(c)
    rows = []
    for x in range(n - 2):
        if h[x + 2] < l[x]:
            rows.append((int(cl[x + 2]), h[x + 2], l[x], -1, "FVG"))
        if l[x + 2] > h[x]:
            rows.append((int(cl[x + 2]), h[x], l[x + 2], 1, "FVG"))
    for e in external_structure(o, h, l, c, "close"):
        p, d = e["protected"], e["dir"]
        ob = ore_order_block(o, h, l, c, p, d, ahead=max(0, min(2, e["j"] - p)))
        if not ob:
            continue
        lo, hi = min(ob["near"], ob["far"]), max(ob["near"], ob["far"])
        rows.append((int(cl[e["j"]]), lo, hi, d, "OB"))
        # failed: a later HTF candle closes through the far side -> breaker the other way
        for k in range(e["j"] + 1, n):
            if (d == -1 and c[k] > hi) or (d == 1 and c[k] < lo):
                rows.append((int(cl[k]), lo, hi, -d, "BB"))
                break
    z = pd.DataFrame(rows, columns=["created", "lo", "hi", "dir", "type"])
    z["htf"] = htf
    return z


def first_touch(z: pd.DataFrame, H1: pd.DataFrame) -> np.ndarray:
    """Open time (ns) of the first H1 candle that reaches each zone after it was created (int64 max if never)."""
    ho = H1.index.as_unit("ns").asi8
    hh, hl = H1["high"].to_numpy(float), H1["low"].to_numpy(float)
    out = np.full(len(z), np.iinfo(np.int64).max, dtype=np.int64)
    for i, (cr, lo, hi, d) in enumerate(zip(z["created"].to_numpy(), z["lo"].to_numpy(), z["hi"].to_numpy(),
                                             z["dir"].to_numpy())):
        a = int(np.searchsorted(ho, cr, side="left"))
        seg = hh[a:] >= lo if d == -1 else hl[a:] <= hi
        k = int(np.argmax(seg)) if len(seg) else 0
        if len(seg) and seg[k]:
            out[i] = ho[a + k]
    return out


def run_pair(pair: str) -> pd.DataFrame:
    mk = MARKETS[pair]
    sp = mk["spread"]
    m1, _ = clean(load_m1_csv(ROOT / mk["file"]))
    m1 = m1[m1.index >= START - pd.Timedelta("400D")]
    D, H4, H1 = (resample(m1, x, "utc0") for x in ("D1", "H4", "H1"))
    d1 = trend_lookup(D)
    Z = pd.concat([htf_zones(H4, "H4"), htf_zones(D, "D1")], ignore_index=True)
    Z["touch"] = first_touch(Z, H1)
    zc, zlo, zhi, zdir, ztch = (Z[k].to_numpy() for k in ("created", "lo", "hi", "dir", "touch"))
    zkey = (Z["htf"] + "_" + Z["type"]).to_numpy()
    rows = []
    for tf in TFS:
        E = resample(m1, tf, "utc0")
        o, h, l, c = ohlc(E)
        n = len(c)
        Eo, Ec = E.index.as_unit("ns").asi8, pd.DatetimeIndex(E["close_time_utc"]).as_unit("ns").asi8
        oc, free = Outcome(m1, sp, tf), Outcome(m1, 0.0, tf)
        oc.hold = free.hold = pd.Timedelta(HOLD[tf]).value
        win_ns = TAP_WINDOW * TF_SEC[tf] * 10**9
        for mode in ("close", "wick"):
            for s in ore_reversal_setups(o, h, l, c, external_structure(o, h, l, c, mode)):
                j, d = s["decision"], s["dir"]
                t = int(Ec[j])
                if t < START.value or j + 1 >= n:
                    continue
                top = s["top"]
                t_top = int(Eo[top])
                px = h[top] if d == -1 else l[top]
                m = ((zdir == d) & (zc <= t_top) & (zlo <= px) & (px <= zhi)
                     & (ztch >= t_top - win_ns) & (ztch <= t_top))
                flags = {f"poi_{k}": bool(np.any(m & (zkey == k))) for k in
                         ("H4_OB", "H4_BB", "H4_FVG", "D1_OB", "D1_BB", "D1_FVG")}
                side = "long" if d == 1 else "short"
                e = s["entry"]
                stop = s["far"] + 2 * sp * (-1 if d == 1 else 1)
                risk = abs(e - stop)
                win = (int(Eo[j + 1]), int(Ec[min(j + s["valid"], n - 1)]))
                for name, mult in (("3R", 3), ("5R", 5)):
                    tgt = e + d * mult * risk
                    res = oc(side, e, stop, None, tgt, None, win)
                    if not res or res["R"] is None:
                        continue
                    r0 = free(side, e, stop, None, tgt, None, win)
                    rows.append({"pair": pair, "tf": tf, "mode": mode, "variant": s["variant"], "target": name,
                                 "side": side, "t_dec": t, "d1": d1(t) == d, **flags, "time": res["time"],
                                 "R": res["R"], "R_free": r0["R"] if r0 else np.nan, "hit": res["hit_T2"],
                                 "chance": res["p_T2"], "e": e, "stop": stop, "tgt": tgt, "dec_open": int(Eo[j]),
                                 "top_open": t_top,
                                 "zone": f"{Eo[s['zone'][0]]};{Eo[s['zone'][1]]};{s['zone'][2]};{s['zone'][3]}",
                                 "liq": f"{Eo[s['liq_idx']]};{s['liq_px']}"})
        print(pair, tf, sum(r["tf"] == tf for r in rows), flush=True)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ report


def stats(g):
    yr = g.groupby("year")["R"].mean()
    pos = int(sum(1 for y in YEARS if yr.get(y, -1) > 0))
    n = len(g)
    avg = g["R"].mean() if n else np.nan
    sd = g["R"].std() if n > 1 else np.nan
    hit, ch = (g["hit"].mean() * 100, g["chance"].mean() * 100) if n else (np.nan, np.nan)
    return {"n": n, "avg": avg, "free": g["R_free"].mean() if n else np.nan, "pos": pos, "hit": hit, "ch": ch, "yr": yr,
            "t": avg / (sd / np.sqrt(n)) if n > 1 and sd > 0 else np.nan}


def f(v, p="+.3f"):
    return "—" if v is None or v != v else format(v, p)


def poi_mask(d, htf, typ):
    hs = ("H4", "D1") if htf == "either" else (htf,)
    ts = ("OB", "BB", "FVG") if typ == "any" else (typ,)
    m = pd.Series(False, index=d.index)
    for a in hs:
        for b in ts:
            m |= d[f"poi_{a}_{b}"].astype(bool)
    return m


def entry_rows(d, entry):
    if entry in ("OB", "BB"):
        return d[d["variant"] == entry]
    x = d.copy()
    x["pri"] = (x["variant"] != "BB").astype(int)
    return x.sort_values("pri").drop_duplicates(["pair", "tf", "mode", "side", "t_dec", "target"]).drop(columns="pri")


def grid(d):
    """Yield (key dict, index of rows) for every pre-registered row, plus the no-POI baseline."""
    ent = {e: entry_rows(d, e) for e in ("OB", "BB", "nearest")}
    for entry, x in ent.items():
        for tf, mode, tg in itertools.product(TFS, ("close", "wick"), ("3R", "5R")):
            base = x[(x["tf"] == tf) & (x["mode"] == mode) & (x["target"] == tg)]
            for bias in ("D1 trend", "none"):
                b = base[base["d1"]] if bias == "D1 trend" else base
                yield {"htf": "—", "poi": "no POI", "tf": tf, "mode": mode, "entry": entry, "target": tg,
                       "bias": bias}, b.index
                for htf, typ in itertools.product(("H4", "D1", "either"), ("OB", "BB", "FVG", "any")):
                    yield {"htf": htf, "poi": typ, "tf": tf, "mode": mode, "entry": entry, "target": tg,
                           "bias": bias}, b[poi_mask(b, htf, typ)].index


def report() -> int:
    from backtest.walkforward import verdict, walk
    d = pd.concat([pd.read_csv(OUT / f"v25_{p}.csv") for p in MARKETS], ignore_index=True)
    d["year"] = pd.to_datetime(d["t_dec"], unit="ns", utc=True).dt.year
    res = []
    parts = []
    for key, idx in grid(d):
        g = d.loc[idx]
        gm, gf = g[g["pair"].isin(MAIN)], g[g["pair"].isin(FRESH)]
        s, fs = stats(gm), stats(gf)
        res.append({**key, "s": s, "fs": fs})
        if key["poi"] != "no POI" and len(gm):
            parts.append(pd.DataFrame({"unit": "|".join(str(v) for v in key.values()),
                                       "time": pd.to_datetime(gm["time"], unit="ns", utc=True).astype(str), "R": gm["R"]}))
    grid_rows = [r for r in res if r["poi"] != "no POI"]
    elig = [r for r in grid_rows if r["s"]["n"] >= 30 and r["s"]["t"] == r["s"]["t"]]
    top = sorted(elig, key=lambda r: -r["s"]["t"])[:10]
    lucky = sum(1 for r in elig if r["s"]["t"] >= 2)
    wf, picks = walk(pd.concat(parts, ignore_index=True))
    v = verdict(wf, "A")

    def held(fs):
        return fs["n"] >= 30 and fs["avg"] > 0 and fs["pos"] >= 3 and fs["hit"] >= fs["ch"]

    L = ["# Spec v25 result: Ore's reversal model after a fresh higher-timeframe POI tap", "",
         "Spec: `docs/spec-v25-htf-poi.md` (committed before the run). Pattern, orders, stop and hold as spec v24. "
         "Main test GBP/USD + gold, check EUR/USD + silver, Nov 2021 – Nov 2026, Ore's spreads, 1-minute scoring.", "",
         f"Grid: {len(grid_rows)} rows with an HTF POI (+ {len(res) - len(grid_rows)} no-POI baselines). Rows with ≥ 30 "
         f"trades on GBP/USD + gold: {len(elig)}. Of those, {lucky} have t ≥ 2 (about {0.025 * len(elig):.0f} expected by "
         f"luck alone if rows were independent; they overlap heavily, so more).", "",
         "## Top 10 rows on GBP/USD + gold (ranked by t), each checked unchanged on EUR/USD + silver", "",
         "| # | HTF POI | LTF | Structure | Entry | Target | Bias | Trades | No costs | **After spread** | t | Hit vs chance | "
         "Yrs + | EUR/USD + silver (trades · avg · yrs+ · hit) | Holds? |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(top, 1):
        s, fs = r["s"], r["fs"]
        L.append(f"| {i} | {r['htf']} {r['poi']} | {r['tf']} | {r['mode']} | {r['entry']} | {r['target']} | {r['bias']} | "
                 f"{s['n']} | {f(s['free'])} | **{f(s['avg'])}** | {f(s['t'], '+.1f')} | {f(s['hit'], '.0f')}% vs "
                 f"{f(s['ch'], '.0f')}% | {s['pos']} | {fs['n']} · {f(fs['avg'])} · {fs['pos']} · {f(fs['hit'], '.0f')}% | "
                 f"{'**YES**' if held(fs) else 'no'} |")
    L += ["", f"**Walk-forward over the whole grid** (each year pick the best row on past years, trade it blind): "
          f"{f(v['avg'])}R over {v['trades']} trades, positive in {v['years_pos']} of 4 years → "
          f"**{'PASS' if v['pass'] else 'fail'}**. Picks: " + "; ".join(f"{p['year']}: {p['A']}" for p in picks) + ".", ""]
    # does the HTF POI tap help? same LTF rows, with vs without
    L += ["## Does the HTF POI tap help? (D1 trend, entry = nearest, all LTF / structure / targets pooled)", "",
          "| Filter | Trades | No costs | After spread | Hit vs chance | EUR/USD + silver avg (trades) |",
          "|---|---|---|---|---|---|"]
    x = entry_rows(d, "nearest")
    x = x[x["d1"]]
    for name, m in [("no POI requirement", pd.Series(True, index=x.index))] + \
            [(f"{h} {t}", poi_mask(x, h, t)) for h in ("H4", "D1", "either") for t in ("OB", "BB", "FVG", "any")]:
        g = x[m]
        s, fs = stats(g[g["pair"].isin(MAIN)]), stats(g[g["pair"].isin(FRESH)])
        L.append(f"| {name} | {s['n']} | {f(s['free'])} | {f(s['avg'])} | {f(s['hit'], '.0f')}% vs {f(s['ch'], '.0f')}% | "
                 f"{f(fs['avg'])} ({fs['n']}) |")
    REPORT.write_text("\n".join(L) + "\n")
    pd.DataFrame([{**{k: r[k] for k in ("htf", "poi", "tf", "mode", "entry", "target", "bias")},
                   "n": r["s"]["n"], "avg": r["s"]["avg"], "t": r["s"]["t"], "fresh_n": r["fs"]["n"],
                   "fresh_avg": r["fs"]["avg"]} for r in res]).to_csv(OUT / "v25_grid.csv", index=False)
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        df = run_pair(sys.argv[1])
        df.to_csv(OUT / f"v25_{sys.argv[1]}.csv", index=False)
    else:
        raise SystemExit(report())

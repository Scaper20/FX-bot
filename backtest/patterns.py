"""Spec v19 (docs/spec-v19-chart-patterns.md): double top/bottom, head and shoulders, flags, triangles.

    python -m backtest.patterns PAIR      (one market, all timeframes -> backtest/out/pat_PAIR.csv)
    python -m backtest.patterns           (report -> backtest/reports/patterns_v19.md)

Every pattern is coded in its bearish form on prices that may be mirrored (bullish = mirror). A swing is used
only from the close of the 3rd candle after it, so nothing is known before it could be seen on a chart.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.advanced import START, Outcome  # noqa: E402
from backtest.romeo import arrays  # noqa: E402
from engine import config as K  # noqa: E402
from engine.candles import clean, load_m1_csv, resample  # noqa: E402

OUT = ROOT / "backtest" / "out"
REPORT = ROOT / "backtest" / "reports" / "patterns_v19.md"
MAIN = {p: {"spread": K.PAIRS[p]["spread"], "file": K.PAIRS[p]["file"]} for p in K.PAIRS}
FRESH = {"EURUSD": {"spread": 0.0001, "file": "data/eurusd-m1-bid-2021-11-01-2026-11-19.zip"},
         "XAGUSD": {"spread": 0.025, "file": "data/xagusd-m1-bid-2021-11-01-2026-11-19.zip"}}
MARKETS = {**MAIN, **FRESH}
# Extra markets (28 Nov 2026): 5-minute Twelve Data history (Dukascopy refused downloads); spread assumed 1 pip until
# Ore confirms his prop firm's spreads. Not part of MARKETS, so older scripts keep their four markets.
EXTRA = {"USDJPY": {"spread": 0.010, "file": "data/td/usdjpy-m5.csv.gz"},
         "AUDUSD": {"spread": 0.0001, "file": "data/td/audusd-m5.csv.gz"}}
TFS = ("M15", "H1", "H4", "D1")
HOLD = {"M15": "2D", "H1": "5D", "H4": "15D", "D1": "45D"}
N = 3                     # swing: beyond the 3 candles each side, known 3 candles later
VALID = 10                # retest limit valid this many candles
NAMES = {"dtop": "Double top / bottom", "hs": "Head and shoulders", "flag": "Flag", "tri": "Triangle"}
KIND = {"dtop": "reversal", "hs": "reversal", "flag": "continuation", "tri": "continuation"}
YEARS = range(2022, 2027)


# ------------------------------------------------------------------ building blocks

def swings(h, l):
    """Indices of swing highs and lows (bearish space). Known at index + N."""
    n = len(h)
    hi, lo = [], []
    for i in range(N, n - N):
        if h[i] > h[i - N:i].max() and h[i] >= h[i + 1:i + N + 1].max():
            hi.append(i)
        if l[i] < l[i - N:i].min() and l[i] <= l[i + 1:i + N + 1].min():
            lo.append(i)
    return np.array(hi, int), np.array(lo, int)


def atr(h, l, c, n=14):
    tr = np.maximum(h - l, np.abs(h - np.r_[c[0], c[:-1]]))
    tr = np.maximum(tr, np.abs(l - np.r_[c[0], c[:-1]]))
    return pd.Series(tr).rolling(n, min_periods=n).mean().to_numpy()


def line(i0, p0, i1, p1):
    s = (p1 - p0) / (i1 - i0)
    return lambda x: p0 + s * (x - i0)


# ------------------------------------------------------------------ pattern finders (bearish space)
# Each yields dict(d=decision index, line=broken-line price at d, height=measured move, stop=raw stop, pts=key points)

def double_tops(h, l, c, A, hi):
    for a, b in zip(hi[:-1], hi[1:]):
        if not 5 <= b - a <= 60 or np.isnan(A[b]):
            continue
        top = max(h[a], h[b])
        if abs(h[a] - h[b]) > 0.25 * A[b] or h[a + 1:b].max(initial=-np.inf) > top:
            continue
        neck = l[a + 1:b].min()
        height = top - neck
        if height < A[b] or a < 30 or l[a - 30:a].min() >= neck:
            continue
        k = b + N
        j = next((x for x in range(b + 1, min(b + 31, len(c))) if h[x] > top or c[x] < neck), None)
        if j is None or h[j] > top:
            continue
        d = max(j, k)
        if d >= len(c) or h[j:d + 1].max() > top or c[d] >= neck:
            continue
        yield {"d": d, "line": neck, "height": height, "stop": top,
               "pts": [a, int(a + 1 + np.argmin(l[a + 1:b])), b]}


def head_shoulders(h, l, c, A, hi):
    for x1, x2, x3 in zip(hi[:-2], hi[1:-1], hi[2:]):
        if not 10 <= x3 - x1 <= 120 or np.isnan(A[x3]):
            continue
        if not (h[x2] > h[x1] and h[x2] > h[x3]) or abs(h[x1] - h[x3]) > A[x3] or h[x1:x3 + 1].max() > h[x2]:
            continue
        a = int(x1 + 1 + np.argmin(l[x1 + 1:x2]))
        b = int(x2 + 1 + np.argmin(l[x2 + 1:x3]))
        neck = line(a, l[a], b, l[b])
        height = h[x2] - neck(x2)
        if height < A[x3] or x1 < 30 or l[x1 - 30:x1].min() >= min(l[a], l[b]):
            continue
        k = x3 + N
        j = next((x for x in range(x3 + 1, min(x3 + 31, len(c))) if h[x] > h[x2] or c[x] < neck(x)), None)
        if j is None or h[j] > h[x2]:
            continue
        d = max(j, k)
        if d >= len(c) or h[j:d + 1].max() > h[x2] or c[d] >= neck(d):
            continue
        yield {"d": d, "line": neck(d), "height": height, "stop": h[x3], "pts": [x1, a, x2, b, x3]}


def flags(h, l, c, A, lo):
    for ib in lo:
        if ib < 15 or np.isnan(A[ib]):
            continue
        p0 = int(ib - 15 + np.argmax(h[ib - 15:ib]))
        pole = h[p0] - l[ib]
        if pole < 3 * A[ib]:
            continue
        cap = l[ib] + 0.5 * pole
        for j in range(ib + 6, min(ib + 27, len(c))):
            fl = np.arange(ib + 1, j)
            if h[fl].max() > cap:
                break
            sl_c = np.polyfit(fl, c[fl], 1)[0]
            sl_l = np.polyfit(fl, l[fl], 1)[0]
            base = (l[fl] - sl_l * fl).min()
            lv = base + sl_l * j
            if c[j] < lv:
                if sl_c >= 0 and j >= ib + N:
                    yield {"d": j, "line": lv, "height": pole, "stop": h[ib + 1:j + 1].max(), "pts": [p0, ib, j]}
                break


def triangles(h, l, c, A, hi, lo):
    seen = set()
    known = sorted([(i + N, "h", i) for i in hi] + [(i + N, "l", i) for i in lo])
    H, L = [], []
    for k, kind, i in known:
        (H if kind == "h" else L).append(i)
        if len(H) < 2 or len(L) < 2 or k >= len(c):
            continue
        a, b, cc, dd = H[-2], H[-1], L[-2], L[-1]
        key = (a, b, cc, dd)
        if key in seen:
            continue
        seen.add(key)
        first, last = min(a, cc), max(b, dd)
        if not 10 <= last - first <= 80 or first < 30 or np.isnan(A[first]):
            continue
        if not (h[a] > h[b] and l[dd] >= l[cc] - 0.1 * A[first]):
            continue
        if h[first - 30:first].max() < h[a] + A[first]:
            continue
        up, low = line(a, h[a], b, h[b]), line(cc, l[cc], dd, l[dd])
        if any(c[x] < low(x) for x in range(dd + 1, k)):
            continue
        height = h[a] - low(a)
        for j in range(k, min(k + 31, len(c))):
            if c[j] > up(j) or low(j) > up(j):
                break
            if c[j] < low(j):
                yield {"d": j, "line": low(j), "height": height, "stop": h[b], "pts": [a, cc, b, dd]}
                break


# ------------------------------------------------------------------ scoring


def run_pair(pair: str) -> pd.DataFrame:
    mk = MARKETS[pair]
    sp = mk["spread"]
    m1, _ = clean(load_m1_csv(ROOT / mk["file"]))
    m1 = m1[m1.index >= START - pd.Timedelta("400D")]
    rows = []
    for tf in TFS:
        E = resample(m1, tf, "utc0")
        Eo, Ec = E.index.as_unit("ns").asi8, pd.DatetimeIndex(E["close_time_utc"]).as_unit("ns").asi8
        after, free = Outcome(m1, sp, tf), Outcome(m1, 0.0, tf)
        after.hold = free.hold = pd.Timedelta(HOLD[tf]).value
        for mir in (False, True):
            sg = -1.0 if mir else 1.0
            o, h, l, c = arrays(E, mir)
            A = atr(h, l, c)
            hi, lo = swings(h, l)
            found = {"dtop": double_tops(h, l, c, A, hi), "hs": head_shoulders(h, l, c, A, hi),
                     "flag": flags(h, l, c, A, lo), "tri": triangles(h, l, c, A, hi, lo)}
            side = "long" if mir else "short"
            for pat, gen in found.items():
                for p in gen:
                    d = p["d"]
                    t = int(Ec[d])
                    if t < START.value or d + 1 >= len(c):
                        continue
                    stop = p["stop"] + 2 * sp
                    win = (int(Eo[d + 1]), int(Ec[min(d + VALID, len(c) - 1)]))
                    for en, e, t_ns, w in (("E1", c[d], t, None), ("E2", p["line"], None, win)):
                        if stop <= e:
                            continue
                        for tg, tgt in (("MM", e - p["height"]), ("2R", e - 2 * (stop - e))):
                            res = after(side, sg * e, sg * stop, None, sg * tgt, t_ns, w)
                            if not res or res["R"] is None:
                                continue
                            r0 = free(side, sg * e, sg * stop, None, sg * tgt, t_ns, w)
                            rows.append({"pair": pair, "tf": tf, "pattern": pat, "side": side, "entry": en,
                                         "target": tg, "t_dec": t, "time": res["time"], "R": res["R"],
                                         "R_free": r0["R"] if r0 else np.nan, "hit": res["hit_T2"],
                                         "chance": res["p_T2"], "rr": (e - tgt) / (stop - e),
                                         "e": sg * e, "stop": sg * stop, "tgt": sg * tgt,
                                         "pts": ";".join(str(int(Eo[x])) for x in p["pts"])})
        print(pair, tf, "done", sum(r["tf"] == tf for r in rows), flush=True)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ report


def stats(g: pd.DataFrame) -> dict:
    yr = g.groupby("year")["R"].mean()
    pos = int(sum(1 for y in YEARS if yr.get(y, -1) > 0))
    hit, ch = g["hit"].mean() * 100, g["chance"].mean() * 100
    n = len(g)
    avg = g["R"].mean() if n else np.nan
    return {"n": n, "avg": avg, "free": g["R_free"].mean() if n else np.nan, "pos": pos, "hit": hit, "ch": ch,
            "yr": yr, "ok": bool(n >= 30 and avg > 0 and pos >= 4 and hit >= ch),
            "t": avg / (g["R"].std() / np.sqrt(n)) if n > 1 and g["R"].std() > 0 else np.nan}


def f(v, p="+.3f"):
    return "—" if v is None or v != v else format(v, p)


def report() -> int:
    from backtest.walkforward import verdict, walk
    d = pd.concat([pd.read_csv(OUT / f"pat_{p}.csv") for p in MARKETS], ignore_index=True)
    d["year"] = pd.to_datetime(d["t_dec"], unit="ns", utc=True).dt.year
    main, fresh = d[d["pair"].isin(MAIN)], d[d["pair"].isin(FRESH)]
    L = ["# Spec v19 result: classic reversal and continuation chart patterns", "",
         "Spec: `docs/spec-v19-chart-patterns.md` (committed before the run). Main test GBP/USD + gold, fresh check "
         "EUR/USD + silver, Nov 2021 – Nov 2026, Ore's spreads, 1-minute scoring, stop first if both hit in a minute.", "",
         "## By pattern (all timeframes, entries and targets pooled)", "",
         "| Pattern | Type | Patterns found | Trades | Avg R no costs | **Avg R after spread** | Target hit vs chance | "
         "Fresh markets avg R |", "|---|---|---|---|---|---|---|---|"]
    for pat in NAMES:
        g, fr = main[main["pattern"] == pat], fresh[fresh["pattern"] == pat]
        s = stats(g)
        n_pat = g.groupby(["pair", "tf", "side", "t_dec"]).ngroups
        L.append(f"| {NAMES[pat]} | {KIND[pat]} | {n_pat:,} | {s['n']:,} | {f(s['free'])} | **{f(s['avg'])}** | "
                 f"{s['hit']:.1f}% vs {s['ch']:.1f}% | {f(fr['R'].mean())} |")
    L += ["", "## All 64 rows (GBP/USD + gold)", "",
          "| Pattern | TF | Entry | Target | Trades | No costs | **After spread** | t | Hit vs chance | "
          + " | ".join(map(str, YEARS)) + " | Yrs + | Consistent |",
          "|---|---|---|---|---|---|---|---|---|" + "---|" * len(YEARS) + "---|---|"]
    ok_rows = []
    for (pat, tf, en, tg), g in main.groupby(["pattern", "tf", "entry", "target"]):
        s = stats(g)
        if s["ok"]:
            ok_rows.append((pat, tf, en, tg, s))
        L.append(f"| {NAMES[pat]} | {tf} | {en} | {tg} | {s['n']} | {f(s['free'])} | **{f(s['avg'])}** | {f(s['t'], '+.1f')} | "
                 f"{s['hit']:.0f}% vs {s['ch']:.0f}% | " + " | ".join(f(s["yr"].get(y, np.nan), "+.2f") for y in YEARS)
                 + f" | {s['pos']} | {'YES' if s['ok'] else 'no'} |")
    unit = main["pattern"] + " " + main["tf"] + " " + main["entry"] + " " + main["target"] + " " + main["pair"]
    wf, _ = walk(pd.DataFrame({"unit": unit, "time": pd.to_datetime(main["time"], unit="ns", utc=True).astype(str),
                               "R": main["R"]}))
    v = verdict(wf, "A")
    L += ["", f"**Consistent rows: {len(ok_rows)} of {main.groupby(['pattern', 'tf', 'entry', 'target']).ngroups}.** "
          f"Walk-forward (choose on past years, trade next year blind, 2023–26): {f(v['avg'])}R over {v['trades']} trades, "
          f"positive in {v['years_pos']} of 4 years → **{'PASS' if v['pass'] else 'fail'}**.", "",
          "## Consistent rows on fresh markets (EUR/USD + silver, same rule)", ""]
    if not ok_rows:
        L.append("None to check.")
    else:
        L += ["| Row | Main | Fresh trades | Fresh avg R | Fresh yrs + | Fresh hit vs chance | By market | Verdict |",
              "|---|---|---|---|---|---|---|---|"]
        for pat, tf, en, tg, s in ok_rows:
            g = fresh[(fresh["pattern"] == pat) & (fresh["tf"] == tf) & (fresh["entry"] == en) & (fresh["target"] == tg)]
            fs = stats(g)
            ok = fs["n"] >= 30 and fs["avg"] > 0 and fs["pos"] >= 3 and fs["hit"] >= fs["ch"]
            bym = ", ".join(f"{p} {f(x['R'].mean())} ({len(x)})" for p, x in g.groupby("pair"))
            L.append(f"| {NAMES[pat]} {tf} {en} {tg} | {s['n']} · {f(s['avg'])} | {fs['n']} | **{f(fs['avg'])}** | "
                     f"{fs['pos']} | {fs['hit']:.0f}% vs {fs['ch']:.0f}% | {bym} | {'PASS' if ok else 'FAIL'} |")
    L += ["", "## By market (all rows pooled)", "", "| Market | Trades | No costs | After spread |", "|---|---|---|---|"]
    for p, g in d.groupby("pair"):
        L.append(f"| {p} | {len(g):,} | {f(g['R_free'].mean())} | {f(g['R'].mean())} |")
    REPORT.write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        df = run_pair(sys.argv[1])
        df.to_csv(OUT / f"pat_{sys.argv[1]}.csv", index=False)
        print(sys.argv[1], len(df), "trades")
    else:
        raise SystemExit(report())

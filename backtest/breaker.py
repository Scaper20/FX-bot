"""Spec v6 + v6b (docs/spec-v6-breaker.md): ICT breaker blocks as the entry (edge, mid, confirm), inside a CRT
and standalone. All years.

    python -m backtest.breaker
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.advanced import START, Outcome  # noqa: E402
from backtest.romeo import arrays, ny_daily, ny_h4  # noqa: E402
from engine import config as K  # noqa: E402
from engine.candles import clean, load_m1_csv, resample  # noqa: E402

OUT = ROOT / "backtest" / "out"
REPORT = ROOT / "backtest" / "reports" / "breaker_v6.md"
VALID = 20          # entry candles the limit stays valid after the shift
MAX_AGE = 100       # a grab that never shifts is dropped after this many candles


def breakers(eo, eh, el, ec, lo, hi):
    """Bearish breakers in candles lo..hi-1 (bearish space). Yields (shift j, breaker b, top, top_idx).
    Swings need 2 candles each side and are only known 2 candles later."""
    sh = sl = None                    # (idx, price) of last confirmed swing high, and swing low after it
    pat = None                        # active grab: dict(sh, sl, top, start)
    for j in range(lo, hi):
        k = j - 2
        if k - 2 >= lo:
            if eh[k] > eh[k - 2:k].max() and eh[k] > eh[k + 1:j + 1].max():
                sh, sl = (k, eh[k]), None
            if el[k] < el[k - 2:k].min() and el[k] < el[k + 1:j + 1].min() and sh is not None and k > sh[0]:
                sl = (k, el[k])
        if pat is not None:
            if eh[j] > pat["top"]:
                pat["top"], pat["top_idx"] = eh[j], j
            if ec[j] < pat["sl"][1] and j > pat["start"]:
                b = next((x for x in range(pat["sl"][0], pat["sh"][0], -1) if ec[x] < eo[x]), None)
                if b is not None:
                    yield j, b, pat["top"], pat["top_idx"]
                pat = None
            elif j - pat["start"] > MAX_AGE:
                pat = None
        if sh is not None and sl is not None and eh[j] > sh[1] and (pat is None or pat["sh"] != sh):
            pat = {"sh": sh, "sl": sl, "top": eh[j], "top_idx": j, "start": j}


def fill_window(eh, j, top, last):
    """Candle range the order is valid in: from the candle after the shift for VALID candles (to `last`),
    ending at the candle that trades above the top (inclusive: price passes the entry on the way)."""
    a, b = j + 1, min(j + VALID, last)
    if a > b:
        return None
    above = np.where(eh[a:b + 1] > top)[0]
    return (a, a + above[0]) if len(above) else (a, b)


def entries(eh, el, ec, b, span, Eo_t, Ec_t):
    """The three entry kinds (spec v6b). Yields (kind, price, t_ns for market or None, limit window or None)."""
    a, z = span
    yield "edge", el[b], None, (Eo_t[a], Ec_t[z])
    yield "mid", (eh[b] + el[b]) / 2, None, (Eo_t[a], Ec_t[z])
    touched = False
    for x in range(a, z + 1):
        touched = touched or eh[x] >= el[b]
        if touched and ec[x] < el[b]:
            yield "confirm", ec[x], Ec_t[x], None
            break


def run_pair(pair):
    spread = K.PAIRS[pair]["spread"]
    m1, _ = clean(load_m1_csv(ROOT / K.PAIRS[pair]["file"]))
    m1 = m1[m1.index >= START - pd.Timedelta("150D")]
    rows = []
    frames = {"M5": resample(m1, "M5", "utc0"), "M15": resample(m1, "M15", "utc0"), "H1": resample(m1, "H1", "utc0")}
    times = {}
    for tf, E in frames.items():
        times[tf] = (E.index.as_unit("ns").asi8, pd.DatetimeIndex(E["close_time_utc"]).as_unit("ns").asi8)

    def score(out, mir, e, stop, t1, t2, t_ns, window, **tags):
        sg = -1.0 if mir else 1.0
        res = out("long" if mir else "short", sg * e, sg * stop, None if t1 is None else sg * t1, sg * t2, t_ns, window)
        if res:
            res.update(pair=pair, direction="long" if mir else "short", **tags)
            rows.append(res)

    # ---- B. standalone, M15 and H1
    for tf in ("M15", "H1"):
        E = frames[tf]
        Eo_t, Ec_t = times[tf]
        out = Outcome(m1, spread, "D1" if tf == "H1" else "H4")
        first = int(np.searchsorted(Eo_t, START.value))
        for mir in (False, True):
            eo, eh, el, ec = arrays(E, mir)
            for j, b, top, _ in breakers(eo, eh, el, ec, first, len(E) - 1):
                span = fill_window(eh, j, top, len(E) - 1)
                if span is None:
                    continue
                for kind, e, t_ns, w in entries(eh, el, ec, b, span, Eo_t, Ec_t):
                    for stop_name, stop in (("classic", top), ("tight", eh[b])):
                        if stop > e:
                            score(out, mir, e, stop, None, e - 3 * (stop - e), t_ns, w,
                                  variant=f"B standalone {tf} {kind} {stop_name}", tf=tf, entry=kind)

    # ---- A. inside a CRT (v4 frame)
    for rtf, R, etf in (("D1", ny_daily(m1), "M15"), ("H4", ny_h4(m1), "M5")):
        E = frames[etf]
        Eo_t, Ec_t = times[etf]
        out = Outcome(m1, spread, rtf)
        Ro = pd.DatetimeIndex(R["t_open"]).as_unit("ns").asi8
        Rc = pd.DatetimeIndex(R["t_close"]).as_unit("ns").asi8
        for mir in (False, True):
            o, h, l, c = arrays(R, mir)
            eo, eh, el, ec = arrays(E, mir)
            for i in range(61, len(R) - 3):
                if Ro[i] < START.value:
                    continue
                s, c3 = i + 1, i + 2
                if not (h[s] > h[i] and l[i] < c[s] < h[i] and l[s] >= l[i]):
                    continue
                mid, far = (h[i] + l[i]) / 2, l[i]
                s0 = int(np.searchsorted(Eo_t, Ro[s], side="left"))
                a = int(np.searchsorted(Eo_t, Ro[c3], side="left"))              # first candle after C2 closed
                bend = int(np.searchsorted(Ec_t, Rc[c3], side="right")) - 1      # last candle of C3
                for j, b, top, _ in breakers(eo, eh, el, ec, max(4, s0 - 30), bend + 1):
                    if j < a:
                        continue
                    span = fill_window(eh, j, top, bend)
                    if span is None:
                        continue
                    for kind, e, t_ns, w in entries(eh, el, ec, b, span, Eo_t, Ec_t):
                        for stop_name, stop in (("classic", top), ("tight", eh[b])):
                            if stop > e > far:
                                score(out, mir, e, stop, mid if far < mid < e else None, far, t_ns, w,
                                      variant=f"A in CRT {rtf} {kind} {stop_name}", tf=rtf, entry=kind)
                    break                                                         # first breaker per CRT
    return rows


def yearly(df):
    df = df.copy()
    ts = pd.to_datetime(df["time"], utc=True)
    df["year"] = ts.dt.year
    df["lnny"] = ts.dt.hour.between(7, 15)
    groups = []
    for v, g in df.groupby("variant"):
        groups.append((v, g))
        if v.startswith("B"):
            groups.append((v + " (London/NY)", g[g["lnny"]]))
    for (v, p), g in df.groupby(["variant", "pair"]):
        groups.append((f"{v} · {p}", g))
    out = []
    for name, g in groups:
        row = {"variant": name, "trades": len(g)}
        for y in range(2021, 2027):
            r = g.loc[g["year"] == y, "R"].dropna()
            row[str(y)] = r.mean() if len(r) else np.nan
        r = g["R"].dropna()
        row["avg R"], row["total R"] = r.mean(), r.sum()
        x = g[g["hit_T2"].notna()]
        p = x["p_T2"]
        row["target hit%"] = x["hit_T2"].mean() * 100
        row["chance%"] = p.mean() * 100
        row["z"] = (x["hit_T2"].sum() - p.sum()) / np.sqrt((p * (1 - p)).sum()) if len(x) else np.nan
        yrs = [row[str(y)] for y in range(2022, 2027)]
        row["years +"] = int(sum(1 for v in yrs if v == v and v > 0))
        row["consistent"] = row["years +"] >= 4 and row["avg R"] > 0
        out.append(row)
    return pd.DataFrame(out)


def main() -> int:
    rows = []
    for pair in K.PAIRS:
        rows += run_pair(pair)
        print(pair, "done", len(rows), flush=True)
    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "breaker_trades.csv", index=False)
    t = yearly(df)
    t.to_csv(OUT / "breaker_yearly.csv", index=False)
    pd.set_option("display.width", 260)
    pd.set_option("display.max_columns", 30)
    print(t.round(3).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

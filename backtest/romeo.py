"""Spec v2 (docs/spec-v2-romeo.md): Romeo's Candle-3 trap + Model #1 entry, New York clock.

    python -m backtest.romeo                 # Design period (2021-11 .. 2023-12) only
    python -m backtest.romeo --period check  # 2024, only for survivors of the Design rule

Measures, per CRT that triggers: reaching Target 1 (50% of C1) / Target 2 (C1's far side) before the
stop, against the chance rate risk/(risk+reward); and average R after spread with half off at 50%.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine import config as K  # noqa: E402
from engine.structure import crt_inside  # noqa: E402
from engine.candles import clean, load_m1_csv, resample  # noqa: E402
from engine.simulate import simulate  # noqa: E402

NY = "America/New_York"
OUT = ROOT / "backtest" / "out"
VARIANTS = ("none", "F1", "F2", "F3", "F1+F2", "ALL")


# ------------------------------------------------------------------ candles on the New York clock

def ny_daily(m1: pd.DataFrame) -> pd.DataFrame:
    ny = m1.index.tz_convert(NY)
    key = ny.normalize()                                   # NY midnight
    g = m1.groupby(key)
    d = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(),
                      "close": g["close"].last(), "first": g.apply(lambda x: x.index[0]),
                      "last": g.apply(lambda x: x.index[-1])})
    d = d[d.index.weekday < 5]                             # drop the Sunday-evening stub
    d["t_open"] = pd.DatetimeIndex(d.index).tz_convert("UTC")
    d["t_close"] = pd.DatetimeIndex(d["t_open"]) + pd.Timedelta("1D")
    return d.reset_index(drop=True)


def ny_weekly(d1: pd.DataFrame) -> pd.DataFrame:
    wk = pd.DatetimeIndex(d1["t_open"]).tz_convert(NY).tz_localize(None).to_period("W-SUN")
    g = d1.groupby(wk)
    w = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(),
                      "close": g["close"].last(), "t_close": g["t_close"].last()})
    return w.reset_index(drop=True)


def ny_h4(m1: pd.DataFrame) -> pd.DataFrame:
    h4 = resample(m1, "H4", "ny17")                         # opens 17, 21, 01, 05, 09, 13 NY
    h4 = h4.reset_index().rename(columns={"time_utc": "t_open", "close_time_utc": "t_close"})
    return h4


# ------------------------------------------------------------------ helpers (bearish space)

def arrays(df, mirrored):
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    if mirrored:
        o, h, l, c = -o, -l, -h, -c
    return o, h, l, c


def bias_bearish(o, h, l, c, j):
    """Romeo's next-candle rule from candle j vs j-1 (bearish space)."""
    if j < 1:
        return False
    return bool(c[j] < l[j - 1] or (h[j] > h[j - 1] and l[j - 1] < c[j] < h[j - 1]))


def first_passage(h, l, a, b, stop, levels):
    seg_h, seg_l = h[a:b], l[a:b]
    st = np.argmax(seg_h >= stop) if (seg_h >= stop).any() else -1
    out = {}
    for name, lv in levels.items():
        hit = seg_l <= lv
        t = np.argmax(hit) if hit.any() else -1
        out[name] = np.nan if (t < 0 and st < 0) else float(t >= 0 and (st < 0 or t < st))
    return out


# ------------------------------------------------------------------ the scan

def run(m1: pd.DataFrame, pair: str, start: pd.Timestamp, end: pd.Timestamp) -> list[dict]:
    spread = K.PAIRS[pair]["spread"]
    m1 = m1[m1.index < end]
    d1, h4 = ny_daily(m1), ny_h4(m1)
    w1 = ny_weekly(d1)
    entry = {"D1": resample(m1, "M15", "utc0"), "H4": resample(m1, "M5", "utc0")}
    M_t = m1.index.as_unit("ns").asi8
    rows = []
    for tf, R in (("D1", d1), ("H4", h4)):
        E = entry[tf]
        E_t_open = E.index.as_unit("ns").asi8
        E_t_close = pd.DatetimeIndex(E["close_time_utc"]).as_unit("ns").asi8
        R_open = pd.DatetimeIndex(R["t_open"]).as_unit("ns").asi8
        R_close = pd.DatetimeIndex(R["t_close"]).as_unit("ns").asi8
        H = w1 if tf == "D1" else d1
        H_close = pd.DatetimeIndex(H["t_close"]).as_unit("ns").asi8
        for mir in (False, True):
            o, h, l, c = arrays(R, mir)
            eo, eh, el, ec = arrays(E, mir)
            Mo, Mh, Ml, Mc = arrays(m1, mir)
            ho, hh, hl, hc = arrays(H, mir)
            body = np.abs(ec - eo)
            for i in range(11, len(R) - 3):
                if R_open[i] < start.value:
                    continue
                s, c3 = i + 1, i + 2
                if not (h[s] > h[i] and crt_inside(o, h, l, c, i, c[s]) and l[s] >= l[i]):
                    continue
                mid, far = (h[i] + l[i]) / 2, l[i]
                t3o = R_open[c3]
                ny3 = pd.Timestamp(t3o, tz="UTC").tz_convert(NY)
                if tf == "D1":
                    t_end = min(R_close[c3], pd.Timestamp(ny3.normalize() + pd.Timedelta("16h")).value)
                else:
                    t_end = R_close[c3]
                # filters (known at C2's close)
                hj = int(np.searchsorted(H_close, R_close[s], side="right")) - 1
                f1 = hj >= 1 and bias_bearish(ho, hh, hl, hc, hj)
                f2 = bool(h[s] > h[i - 10:i].max())
                ny1 = pd.Timestamp(R_open[i], tz="UTC").tz_convert(NY)
                if tf == "D1":
                    f3 = ny1.weekday() in (0, 1)
                else:
                    f3 = ny1.hour == 1 and pd.Timestamp(R_open[s], tz="UTC").tz_convert(NY).hour == 5
                # control: enter at C2's close
                ctrl = {"e": c[s], "stop": h[s], "t": R_close[s]}
                # Candle-3 trap + Model #1 on the entry timeframe
                a = int(np.searchsorted(E_t_open, t3o, side="left"))
                b = int(np.searchsorted(E_t_close, t_end, side="right"))
                c3open = o[c3]
                run_hi, m1i, above, trig, missed = -np.inf, None, False, None, False
                for j in range(a, b):
                    if m1i is not None and j > m1i and above and ec[j] < eo[m1i]:
                        trig = j
                        break
                    if el[j] <= mid:
                        missed = True
                        break
                    if eh[j] > c3open:
                        above = True
                    if eh[j] > run_hi:
                        run_hi = eh[j]
                        rng = eh[j] - el[j]
                        med = np.median(body[max(0, j - 20):j]) if j > 0 else 0
                        thick = ec[j] > eo[j] and rng > 0 and body[j] >= 0.5 * rng and body[j] >= med
                        m1i = j if thick else None
                model = None
                if trig is not None and not missed:
                    tt = int(E_t_close[trig])
                    if tf == "H4" and f3 and pd.Timestamp(tt, tz="UTC").tz_convert(NY) > ny3.normalize() + pd.Timedelta("10h30min"):
                        f3_entry = False
                    else:
                        f3_entry = True
                    model = {"e": ec[trig], "stop": max(run_hi, eh[a:trig + 1].max()), "t": tt, "f3ok": f3_entry}
                for kind, x in (("control", ctrl), ("c3_m1", model)):
                    if x is None or x["stop"] <= x["e"] or x["e"] <= mid:
                        continue
                    risk = x["stop"] - x["e"]
                    ia = int(np.searchsorted(M_t, x["t"], side="left"))
                    hold = pd.Timedelta("3D" if tf == "D1" else "20h").value
                    ib = int(np.searchsorted(M_t, x["t"] + hold, side="left"))
                    fp = first_passage(Mh, Ml, ia, ib, x["stop"], {"T1": mid, "T2": far})
                    fs, xs = (spread, 0.0) if mir else (0.0, spread)
                    sim = simulate(Mh, Ml, Mc, ia, ia + 1, lambda f, ib=ib: ib, entry=x["e"], market=True,
                                   stop=x["stop"], targets={"T2": far}, t1=mid, fill_shift=fs, exit_shift=xs)
                    res = sim.get("results", {}) if sim["status"] == "filled" else {}
                    rows.append({
                        "pair": pair, "tf": tf, "kind": kind, "direction": "long" if mir else "short",
                        "time": pd.Timestamp(x["t"], tz="UTC"), "risk": risk,
                        "p_T1": risk / (risk + (x["e"] - mid)), "p_T2": risk / (risk + (x["e"] - far)),
                        "hit_T1": fp["T1"], "hit_T2": fp["T2"],
                        "R_half": res.get("M2_T2", {}).get("R"), "R_full": res.get("M1_T2", {}).get("R"),
                        "F1": f1, "F2": f2, "F3": bool(f3 and (kind == "control" or x.get("f3ok", True))),
                    })
    return rows


def variant_mask(df, v):
    if v == "none":
        return pd.Series(True, index=df.index)
    if v == "ALL":
        return df["F1"] & df["F2"] & df["F3"]
    m = pd.Series(True, index=df.index)
    for f in v.split("+"):
        m &= df[f]
    return m


def edge(df, lvl):
    x = df[df[f"hit_{lvl}"].notna()]
    if len(x) == 0:
        return 0, np.nan, np.nan, np.nan
    p = x[f"p_{lvl}"]
    z = (x[f"hit_{lvl}"].sum() - p.sum()) / np.sqrt((p * (1 - p)).sum())
    return len(x), x[f"hit_{lvl}"].mean() * 100, p.mean() * 100, z


def report(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    for kind in ("control", "c3_m1"):
        for tf in ("D1", "H4"):
            for v in VARIANTS:
                x = df[(df.kind == kind) & (df.tf == tf) & variant_mask(df, v)]
                n1, h1, c1, z1 = edge(x, "T1")
                n2, h2, c2, z2 = edge(x, "T2")
                out.append({"entry": kind, "tf": tf, "filter": v, "trades": len(x),
                            "T1 hit%": h1, "T1 chance%": c1, "T1 z": z1, "T2 hit%": h2, "T2 chance%": c2, "T2 z": z2,
                            "avg R (half at 50%, after spread)": x["R_half"].mean(),
                            "GBPUSD z(T1)": edge(x[x.pair == "GBPUSD"], "T1")[3],
                            "XAUUSD z(T1)": edge(x[x.pair == "XAUUSD"], "T1")[3]})
    return pd.DataFrame(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--period", default="design", choices=("design", "check"))
    a = ap.parse_args()
    start, end = (pd.Timestamp(x, tz="UTC") for x in K.PERIODS[a.period])
    rows = []
    for pair in K.PAIRS:
        m1, _ = clean(load_m1_csv(ROOT / K.PAIRS[pair]["file"]))
        m1 = m1[m1.index >= start - pd.Timedelta("120D")]
        rows += run(m1, pair, start, end)
    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / f"romeo_{a.period}.csv", index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 20)
    print(report(df).round(2).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

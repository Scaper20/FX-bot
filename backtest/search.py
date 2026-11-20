"""Combination search over Romeo-style conditions, with protection against luck.

    python -m backtest.search

Stages (fixed before running, see docs/spec-v2-search.md):
  1. Find:    2021-11 .. 2022-12  — combo of up to 3 conditions, >= 40 trades, z(T1 edge) >= 2.5, avg R > 0
  2. Confirm: 2023                — same combo, >= 20 trades, z >= 2.0, avg R > 0
  3. Check:   2024                — survivors only, same thresholds as stage 2 (2024 was looked at once before)
  Luck test:  the same search on shuffled outcomes (30 times) shows how many combos pass stages 1+2 by chance.
2025-2026 is never loaded.
"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.romeo import arrays, bias_bearish, first_passage, ny_daily, ny_h4, ny_weekly  # noqa: E402
from engine import config as K  # noqa: E402
from engine import structure as S  # noqa: E402
from engine.candles import clean, load_m1_csv, resample  # noqa: E402
from engine.simulate import simulate  # noqa: E402

NY = "America/New_York"
OUT = ROOT / "backtest" / "out"
REPORT = ROOT / "backtest" / "reports" / "search_v2.md"
START, END = pd.Timestamp("2021-11-01", tz="UTC"), pd.Timestamp("2025-01-01", tz="UTC")
STAGE = {"find": ("2021-11-01", "2023-01-01"), "confirm": ("2023-01-01", "2024-01-01"), "check": ("2024-01-01", "2025-01-01")}
MIN_N = {"find": 40, "confirm": 20, "check": 20}
MIN_Z = {"find": 2.5, "confirm": 2.0, "check": 2.0}

FLAGS = {
    "close_past_50": "C2 closed past the 50% level",
    "close_near_edge": "C2 closed near the swept edge (<25% in)",
    "sweep_big": "sweep >= 0.25 ATR beyond the range",
    "sweep_tiny": "sweep < 0.05 ATR beyond the range",
    "c1_big": "range candle >= 1.2 ATR",
    "c1_small": "range candle <= 0.6 ATR",
    "c2_closes_with_trade": "C2 closed in the trade direction (bearish for shorts)",
    "c2_long_wick": "C2's sweep wick >= 50% of its range",
    "htf_bias": "higher-timeframe candle bias agrees",
    "old_high_swept": "sweep also took the highest of the previous 10 candles",
    "prev_htf_extreme_swept": "sweep took the previous day's/week's high or low",
    "premium": "C2 closed in the premium (shorts) / discount (longs) half of the 20-candle range",
    "with_trend": "range candle below/above its 20-candle average (with the trend)",
    "against_trend": "range candle on the other side of its 20-candle average (reversal)",
    "sweep_mon": "sweep on Monday", "sweep_tue_wed": "sweep on Tuesday/Wednesday", "sweep_thu_fri": "sweep on Thursday/Friday",
    "london_sweep": "H4 sweep candle opens 01:00 or 05:00 NY", "ny_sweep": "H4 sweep candle opens 09:00 NY",
    "late_sweep": "H4 sweep candle opens 13:00-21:00 NY",
    "time_1_5_9": "H4 1/5/9 model (range 01:00, sweep 05:00 NY)", "range_mon_tue": "D1 range candle on Monday/Tuesday",
    "htf_fvg": "sweep ran into an older higher-timeframe FVG", "htf_ob": "sweep ran into an older higher-timeframe order block",
    "fast_trigger": "Candle-3 trigger in the first quarter of C3",
}


def scan(m1: pd.DataFrame, pair: str) -> list[dict]:
    spread = K.PAIRS[pair]["spread"]
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
            for i in range(21, len(R) - 3):
                if R_open[i] < START.value:
                    continue
                s, c3 = i + 1, i + 2
                if not (h[s] > h[i] and l[i] < c[s] < h[i] and l[s] >= l[i]):
                    continue
                rng = h[i] - l[i]
                atr = np.mean(h[i - 14:i] - l[i - 14:i])
                if rng <= 0 or atr <= 0:
                    continue
                mid, far = (h[i] + l[i]) / 2, l[i]
                hj = int(np.searchsorted(H_close, R_close[s], side="right")) - 1
                ny1 = pd.Timestamp(R_open[i], tz="UTC").tz_convert(NY)
                ny2 = pd.Timestamp(R_open[s], tz="UTC").tz_convert(NY)
                dr_hi, dr_lo = h[i - 20:i + 1].max(), l[i - 20:i + 1].min()
                ma = c[i - 20:i].mean()
                fvg, ob = S.htf_zone_overlap(o, h, l, c, i, h[i], h[s], 60)
                flags = {
                    "close_past_50": (h[i] - c[s]) / rng >= 0.5, "close_near_edge": (h[i] - c[s]) / rng < 0.25,
                    "sweep_big": (h[s] - h[i]) >= 0.25 * atr, "sweep_tiny": (h[s] - h[i]) < 0.05 * atr,
                    "c1_big": rng >= 1.2 * atr, "c1_small": rng <= 0.6 * atr,
                    "c2_closes_with_trade": c[s] < o[s],
                    "c2_long_wick": (h[s] - max(o[s], c[s])) >= 0.5 * (h[s] - l[s]),
                    "htf_bias": hj >= 1 and bias_bearish(ho, hh, hl, hc, hj),
                    "old_high_swept": h[s] > h[i - 10:i].max(),
                    "prev_htf_extreme_swept": hj >= 0 and h[s] > hh[hj],
                    "premium": c[s] >= (dr_hi + dr_lo) / 2,
                    "with_trend": c[i] < ma, "against_trend": c[i] > ma,
                    "sweep_mon": ny2.weekday() == 0, "sweep_tue_wed": ny2.weekday() in (1, 2),
                    "sweep_thu_fri": ny2.weekday() in (3, 4),
                    "london_sweep": tf == "H4" and ny2.hour in (1, 5), "ny_sweep": tf == "H4" and ny2.hour == 9,
                    "late_sweep": tf == "H4" and ny2.hour in (13, 17, 21),
                    "time_1_5_9": tf == "H4" and ny1.hour == 1 and ny2.hour == 5,
                    "range_mon_tue": tf == "D1" and ny1.weekday() in (0, 1),
                    "htf_fvg": bool(fvg), "htf_ob": bool(ob),
                }
                entries = [("c2_close", {"e": c[s], "stop": h[s], "t": R_close[s], "fast": False})]
                # Candle-3 trap + Model #1 (spec v2)
                ny3 = pd.Timestamp(R_open[c3], tz="UTC").tz_convert(NY)
                t_end = min(R_close[c3], (ny3.normalize() + pd.Timedelta("16h")).value) if tf == "D1" else R_close[c3]
                a = int(np.searchsorted(E_t_open, R_open[c3], side="left"))
                b = int(np.searchsorted(E_t_close, t_end, side="right"))
                run_hi, m1i, above, trig = -np.inf, None, False, None
                for j in range(a, b):
                    if m1i is not None and j > m1i and above and ec[j] < eo[m1i]:
                        trig = j
                        break
                    if el[j] <= mid:
                        break
                    if eh[j] > o[c3]:
                        above = True
                    if eh[j] > run_hi:
                        run_hi = eh[j]
                        r_ = eh[j] - el[j]
                        med = np.median(body[max(0, j - 20):j]) if j > 0 else 0
                        m1i = j if (ec[j] > eo[j] and r_ > 0 and body[j] >= 0.5 * r_ and body[j] >= med) else None
                if trig is not None:
                    entries.append(("c3_m1", {"e": ec[trig], "stop": eh[a:trig + 1].max(), "t": int(E_t_close[trig]),
                                              "fast": (E_t_close[trig] - R_open[c3]) <= 0.25 * (R_close[c3] - R_open[c3])}))
                for base, x in entries:
                    if x["stop"] <= x["e"] or x["e"] <= mid:
                        continue
                    risk = x["stop"] - x["e"]
                    ia = int(np.searchsorted(M_t, x["t"], side="left"))
                    ib = int(np.searchsorted(M_t, x["t"] + pd.Timedelta("3D" if tf == "D1" else "20h").value, side="left"))
                    fp = first_passage(Mh, Ml, ia, ib, x["stop"], {"T1": mid, "T2": far})
                    fs, xs = (spread, 0.0) if mir else (0.0, spread)
                    sim = simulate(Mh, Ml, Mc, ia, ia + 1, lambda f, ib=ib: ib, entry=x["e"], market=True, stop=x["stop"],
                                   targets={"T2": far}, t1=mid, fill_shift=fs, exit_shift=xs)
                    res = sim.get("results", {}) if sim["status"] == "filled" else {}
                    row = {"pair": pair, "tf": tf, "base": base, "direction": "long" if mir else "short",
                           "time": pd.Timestamp(x["t"], tz="UTC"), "p_T1": risk / (risk + (x["e"] - mid)),
                           "hit_T1": fp["T1"], "R": res.get("M2_T2", {}).get("R"), "cost_R": spread / risk,
                           **{k: bool(v) for k, v in flags.items()}, "fast_trigger": bool(x["fast"])}
                    rows.append(row)
    return rows


def stats(hit, p, R, mask):
    m = mask & ~np.isnan(hit)
    n = int(m.sum())
    if n == 0:
        return 0, np.nan, np.nan
    var = (p[m] * (1 - p[m])).sum()
    z = (hit[m].sum() - p[m].sum()) / np.sqrt(var) if var > 0 else np.nan
    r = R[mask & ~np.isnan(R)]
    return n, z, (r.mean() if len(r) else np.nan)


def search(df: pd.DataFrame, rng: np.random.Generator | None = None) -> pd.DataFrame:
    """All combos of 1-3 flags per (base, tf). With rng: outcomes shuffled within each stage (luck test)."""
    out = []
    for (base, tf), g in df.groupby(["base", "tf"]):
        g = g.reset_index(drop=True)
        hit, p, R = g["hit_T1"].to_numpy(float), g["p_T1"].to_numpy(float), g["R"].to_numpy(float)
        stage = np.where(g["time"] < pd.Timestamp(STAGE["find"][1], tz="UTC"), "find",
                         np.where(g["time"] < pd.Timestamp(STAGE["confirm"][1], tz="UTC"), "confirm", "check"))
        if rng is not None:
            for st in ("find", "confirm"):
                idx = np.where(stage == st)[0]
                perm = rng.permutation(idx)
                hit[idx], p[idx], R[idx] = hit[perm], p[perm], R[perm]
        flags = [f for f in FLAGS if g[f].mean() >= 0.05]
        B = {f: g[f].to_numpy(bool) for f in flags}
        masks = {st: stage == st for st in STAGE}
        for k in (1, 2, 3):
            for combo in itertools.combinations(flags, k):
                m = np.logical_and.reduce([B[f] for f in combo])
                n1, z1, r1 = stats(hit, p, R, m & masks["find"])
                if n1 < MIN_N["find"] or not (z1 >= MIN_Z["find"]) or not (r1 > 0):
                    continue
                n2, z2, r2 = stats(hit, p, R, m & masks["confirm"])
                passed2 = n2 >= MIN_N["confirm"] and z2 >= MIN_Z["confirm"] and r2 > 0
                row = {"base": base, "tf": tf, "combo": " + ".join(combo), "n_find": n1, "z_find": z1, "R_find": r1,
                       "n_confirm": n2, "z_confirm": z2, "R_confirm": r2, "pass_confirm": passed2}
                if rng is None and passed2:
                    n3, z3, r3 = stats(hit, p, R, m & masks["check"])
                    row.update(n_check=n3, z_check=z3, R_check=r3,
                               pass_check=n3 >= MIN_N["check"] and z3 >= MIN_Z["check"] and r3 > 0)
                out.append(row)
    return pd.DataFrame(out)


def n_combos(df):
    tot = 0
    for _, g in df.groupby(["base", "tf"]):
        f = sum(1 for x in FLAGS if g[x].mean() >= 0.05)
        tot += f + f * (f - 1) // 2 + f * (f - 1) * (f - 2) // 6
    return tot


def main() -> int:
    rows = []
    for pair in K.PAIRS:
        m1, _ = clean(load_m1_csv(ROOT / K.PAIRS[pair]["file"]))
        m1 = m1[(m1.index >= START - pd.Timedelta("150D")) & (m1.index < END)]   # 2025+ never loaded
        rows += scan(m1, pair)
    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "search_v2_trades.csv", index=False)
    real = search(df)
    stage1 = len(real)
    stage2 = real[real["pass_confirm"]] if len(real) else real
    stage3 = stage2[stage2.get("pass_check", False) == True] if len(stage2) else stage2  # noqa: E712
    luck = []
    rng = np.random.default_rng(7)
    for _ in range(30):
        s = search(df, rng)
        luck.append((len(s), int(s["pass_confirm"].sum()) if len(s) else 0))
    luck = np.array(luck)
    pd.set_option("display.width", 250)
    summary = (f"trades: {len(df)} ({df.groupby(['base', 'tf']).size().to_dict()})\n"
               f"combinations tested: {n_combos(df)}\n"
               f"stage 1 (find 2021-22) passed: {stage1} | luck test average {luck[:, 0].mean():.1f} (max {luck[:, 0].max()})\n"
               f"stage 2 (confirm 2023) passed: {len(stage2)} | luck test average {luck[:, 1].mean():.2f} (max {luck[:, 1].max()})\n"
               f"stage 3 (check 2024) passed: {len(stage3)}")
    print(summary)
    if len(stage2):
        print(stage2.sort_values("z_confirm", ascending=False).round(2).to_string(index=False))
    real.to_csv(OUT / "search_v2_results.csv", index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

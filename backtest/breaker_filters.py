"""Spec v8 + v9 (docs/spec-v8-breaker-filters.md, docs/spec-v9-romeo-loose.md): breaker entry inside a CRT,
filtered by Ore's v1.2 rules or by Romeo's 3 filters (strict, loose, any 2 of 3), each with and without MSnR.
All years, per-year results and walk-forward.

    python -m backtest.breaker_filters
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.advanced import START, Outcome, fresh_levels, storyline_bearish  # noqa: E402
from backtest.breaker import breakers, entries, fill_window  # noqa: E402
from backtest.romeo import arrays, bias_bearish, ny_daily, ny_h4, ny_weekly  # noqa: E402
from backtest.walkforward import verdict, walk  # noqa: E402
from engine import config as K  # noqa: E402
from engine import structure as S  # noqa: E402
from engine.candles import clean, load_m1_csv, resample  # noqa: E402
from engine.sessions import friday_late, session_flags  # noqa: E402

NY = "America/New_York"
OUT = ROOT / "backtest" / "out"
REPORT = ROOT / "backtest" / "reports" / "breaker_filters_v8.md"
REPORT_V9 = ROOT / "backtest" / "reports" / "romeo_loose_v9.md"
TESTS = {"1. v1.2 filters": ["v12"], "2. Romeo 3 filters": ["F1", "F2", "F3"],
         "3. v1.2 filters + MSnR": ["v12", "msnr"], "4. Romeo 3 filters + MSnR": ["F1", "F2", "F3", "msnr"]}
INFO = {"Romeo F1 only": ["F1"], "Romeo F2 only": ["F2"], "Romeo F3 only": ["F3"], "no filter (v6b baseline)": []}
TESTS_V9 = {"5. Romeo loose 3 filters": ["F1L", "F2L", "F3L"], "6. Romeo loose 3 filters + MSnR": ["F1L", "F2L", "F3L", "msnr"],
            "7. Romeo any 2 of 3 strict": ["two_of_three"], "8. Romeo any 2 of 3 strict + MSnR": ["two_of_three", "msnr"]}
INFO_V9 = {"loose F1 only (not against HTF)": ["F1L"], "loose F2 only (key level)": ["F2L"], "loose F3 only (time)": ["F3L"]}


def _ts(ns):
    return pd.Timestamp(int(ns), tz="UTC")


FRESH = {"EURUSD": {"spread": 0.00010, "file": "data/eurusd-m1-bid-2021-11-01-2026-11-19.zip"},
         "XAGUSD": {"spread": 0.03, "file": "data/xagusd-m1-bid-2021-11-01-2026-11-19.zip"}}   # spec v10


def run_pair(pair, markets=K.PAIRS):
    spread = markets[pair]["spread"]
    m1, _ = clean(load_m1_csv(ROOT / markets[pair]["file"]))
    m1 = m1[m1.index >= START - pd.Timedelta("150D")]
    d1, h4 = ny_daily(m1), ny_h4(m1)
    w1 = ny_weekly(d1)
    D_close = pd.DatetimeIndex(d1["t_close"]).as_unit("ns").asi8
    rows = []
    for rtf, R, etf, H in (("D1", d1, "M15", w1), ("H4", h4, "M5", d1)):
        E = resample(m1, etf, "utc0")
        Eo_t = E.index.as_unit("ns").asi8
        Ec_t = pd.DatetimeIndex(E["close_time_utc"]).as_unit("ns").asi8
        out = Outcome(m1, spread, rtf)
        Ro = pd.DatetimeIndex(R["t_open"]).as_unit("ns").asi8
        Rc = pd.DatetimeIndex(R["t_close"]).as_unit("ns").asi8
        Hc = pd.DatetimeIndex(H["t_close"]).as_unit("ns").asi8
        for mir in (False, True):
            sg = -1.0 if mir else 1.0
            o, h, l, c = arrays(R, mir)
            eo, eh, el, ec = arrays(E, mir)
            ho, hh, hl, hc = arrays(H, mir)
            do, dh, dl, dc = arrays(d1, mir)
            ema = pd.Series(dc).ewm(span=20, adjust=False).mean().to_numpy()
            for i in range(61, len(R) - 3):
                if Ro[i] < START.value:
                    continue
                s, c3 = i + 1, i + 2
                if not (h[s] > h[i] and l[i] < c[s] < h[i] and l[s] >= l[i]):
                    continue
                mid, far = (h[i] + l[i]) / 2, l[i]
                atr = np.mean(h[i - 14:i] - l[i - 14:i])
                # ---- filters known at C2's close
                hj = int(np.searchsorted(Hc, Rc[s], side="right")) - 1
                dj = int(np.searchsorted(D_close, Rc[s], side="right")) - 1
                with_dir = dj >= 1 and dc[dj] < ema[dj] and ema[dj] < ema[dj - 1]
                fvg, ob = S.htf_zone_overlap(o, h, l, c, i, h[i], h[s], 60)
                v12_static = bool((with_dir or fvg or ob) and h[s] - h[i] >= 0.1 * atr)
                f1 = bool(hj >= 1 and bias_bearish(ho, hh, hl, hc, hj))
                f2 = bool(h[s] > h[i - 10:i].max())
                # v9 loose: F1 = not bullish (inside bar allowed); F2 = 5-candle high, previous HTF high or HTF zone
                bull = hj >= 1 and (hc[hj] > hh[hj - 1] or (hl[hj] < hl[hj - 1] and hl[hj - 1] < hc[hj] < hh[hj - 1]))
                f1l = bool(f1 or (hj >= 1 and not bull))
                f2l = bool(h[s] > h[i - 5:i].max() or (hj >= 0 and h[s] > hh[hj]) or fvg or ob)
                ny1 = _ts(Ro[i]).tz_convert(NY)
                f3 = (ny1.weekday() in (0, 1)) if rtf == "D1" else (ny1.hour == 1 and _ts(Ro[s]).tz_convert(NY).hour == 5)
                ny2 = _ts(Ro[s]).tz_convert(NY)
                f3l_static = (ny2.weekday() in (0, 1, 2)) if rtf == "D1" else ny2.hour in (1, 5, 9)
                msnr = False
                if hj > 10 and storyline_bearish(ho, hc, hj):
                    resist, _ = fresh_levels(o, h, l, c, i, 60, atr)
                    msnr = any(h[i] - 0.1 * atr <= lv <= h[s] + 0.1 * atr for lv in resist)
                c3_day = _ts(Ro[c3]).tz_convert(NY).normalize()
                # ---- breaker inside C3
                s0 = int(np.searchsorted(Eo_t, Ro[s], side="left"))
                a = int(np.searchsorted(Eo_t, Ro[c3], side="left"))
                bend = int(np.searchsorted(Ec_t, Rc[c3], side="right")) - 1
                for j, b, top, _ in breakers(eo, eh, el, ec, max(4, s0 - 30), bend + 1):
                    if j < a:
                        continue
                    span = fill_window(eh, j, top, bend)
                    if span is None:
                        continue
                    for kind, e, t_ns, w in entries(eh, el, ec, b, span, Eo_t, Ec_t):
                        decided = _ts(t_ns if t_ns is not None else Ec_t[j])
                        v12 = v12_static and session_flags(decided) != "" and not friday_late(decided)
                        f3ok = f3 and (rtf == "D1" or decided.tz_convert(NY) <= c3_day + pd.Timedelta("10h30min"))
                        f3l = f3l_static and (rtf == "D1" or decided.tz_convert(NY) < c3_day + pd.Timedelta("16h"))
                        for stop_name, stop in (("classic", top), ("tight", eh[b])):
                            if not stop > e > far:
                                continue
                            res = out("long" if mir else "short", sg * e, sg * stop,
                                      sg * mid if far < mid < e else None, sg * far, t_ns, w)
                            if res:
                                res.update(pair=pair, tf=rtf, entry=kind, stop=stop_name,
                                           direction="long" if mir else "short", v12=v12, F1=f1, F2=f2,
                                           F3=bool(f3ok), msnr=bool(msnr), F1L=f1l, F2L=f2l, F3L=bool(f3l))
                                rows.append(res)
                    break                                                     # first breaker per CRT
    return rows


def table(g):
    out = []
    for (tf, entry, stop), x in g.groupby(["tf", "entry", "stop"]):
        r = x["R"].dropna()
        row = {"row": f"{tf} {entry} {stop}", "trades": len(r)}
        for y in range(2021, 2027):
            ry = x.loc[x["year"] == y, "R"].dropna()
            row[str(y)] = ry.mean() if len(ry) else np.nan
        row["avg R"], row["total R"] = r.mean() if len(r) else np.nan, r.sum()
        row["years +"] = int(sum(1 for y in range(2022, 2027) if row[str(y)] == row[str(y)] and row[str(y)] > 0))
        row["consistent"] = bool(len(r) >= 30 and row["years +"] >= 4 and row["avg R"] > 0)
        out.append(row)
    return pd.DataFrame(out)


def mask(df, flags):
    m = pd.Series(True, index=df.index)
    for f in flags:
        m &= df[f].astype(bool)
    return m


def fmt(x, p="+.2f"):
    return "—" if x != x else format(x, p)


def report(df, tests, info, title, spec, path):
    """Per-row yearly tables, walk-forward and a summary for each test; keeps any hand-written
    '## Reading' section already in the report."""
    keep = ""
    if path.exists() and "\n## Reading" in path.read_text():
        keep = path.read_text()[path.read_text().index("\n## Reading"):]
    lines = [f"# {title}", "",
             f"Spec: `{spec}` (committed before the run). GBP/USD + gold, Nov 2021 – Nov 2026, "
             "average R after spread. Consistent = 30+ trades, positive in 4 of 5 years (2022–2026) and in total.", ""]
    summary = []
    for name, flags in {**tests, **info}.items():
        g = df[mask(df, flags)]
        t = table(g)
        wf, _ = walk(pd.DataFrame({"unit": g["tf"] + " " + g["entry"] + " " + g["stop"] + " " + g["pair"],
                                   "time": g["time"], "R": g["R"]}).dropna(subset=["R"]))
        va = verdict(wf, "A")
        wf_text = (f"blind average {va['avg']:+.3f} over {va['trades']} trades, positive in {va['years_pos']} of 4 years "
                   f"-> {'PASS' if va['pass'] else 'fail'}" if va["trades"] else "too few trades to walk forward (no unit had 30 training trades)")
        summary.append({"test": name, "trades": int(g["R"].notna().sum()), "rows": len(t),
                        "consistent rows": int(t["consistent"].sum()) if len(t) else 0,
                        "best avg R": t["avg R"].max() if len(t) else np.nan, "walk-forward": wf_text})
        print(f"\n== {name}")
        print(t.round(3).to_string(index=False))
        print("walk-forward:", wf_text)
        lines += [f"## {name}{' (for information)' if name in info else ''}", "",
                  "| Row (TF entry stop) | Trades | 2022 | 2023 | 2024 | 2025 | 2026 | Avg R | Years + | Consistent |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
        for _, r in t.iterrows():
            lines.append(f"| {r['row']} | {r['trades']} | " + " | ".join(fmt(r[str(y)]) for y in range(2022, 2027))
                         + f" | {fmt(r['avg R'])} | {r['years +']} | {'YES' if r['consistent'] else 'no'} |")
        lines += ["", f"Walk-forward: {wf_text}.", ""]
    s = pd.DataFrame(summary)
    print("\n== SUMMARY")
    print(s.round(3).to_string(index=False))
    lines += ["## Summary", "", "| Test | Trades | Consistent rows (of 12) | Best row avg R | Walk-forward |", "|---|---|---|---|---|"]
    for _, r in s.iterrows():
        lines.append(f"| {r['test']} | {r['trades']} | {r['consistent rows']} | {fmt(r['best avg R'])} | {r['walk-forward']} |")
    path.write_text("\n".join(lines) + "\n" + keep)


def main() -> int:
    rows = []
    for pair in K.PAIRS:
        rows += run_pair(pair)
        print(pair, "done", len(rows), flush=True)
    df = pd.DataFrame(rows)
    df["year"] = pd.to_datetime(df["time"], utc=True).dt.year
    df["two_of_three"] = df[["F1", "F2", "F3"]].astype(int).sum(axis=1) >= 2
    df.to_csv(OUT / "breaker_filters_trades.csv", index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 20)
    report(df, TESTS, INFO, "Spec v8 result: breaker entry with Ore's v1.2 filters / Romeo's 3 filters, with and without MSnR",
           "docs/spec-v8-breaker-filters.md", REPORT)
    report(df, TESTS_V9, INFO_V9, "Spec v9 result: Romeo's filters loosened (and any 2 of 3), with the breaker entry",
           "docs/spec-v9-romeo-loose.md", REPORT_V9)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

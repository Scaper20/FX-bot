"""Spec v7 (docs/spec-v7-walkforward.md): anchored yearly walk-forward for every strategy family.

Choose using only past years, trade the next year blind, repeat. Only next-year results are reported.

    python -m backtest.walkforward
"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine import config as K  # noqa: E402
from engine.candles import clean, load_m1_csv  # noqa: E402

OUT = ROOT / "backtest" / "out"
REPORT = ROOT / "backtest" / "reports" / "walkforward_v7.md"
START, END = pd.Timestamp("2021-11-01", tz="UTC"), pd.Timestamp("2026-11-19", tz="UTC")
TEST_YEARS = (2023, 2024, 2025, 2026)
MIN_TRAIN = 30
T_ALL = 2.0
PARTNER = {"GBPUSD": "data/eurusd-m1-bid-2021-11-01-2026-11-19.zip",
           "XAUUSD": "data/xagusd-m1-bid-2021-11-01-2026-11-19.zip"}


def _m1(path):
    m1, _ = clean(load_m1_csv(ROOT / path))
    return m1[(m1.index >= START - pd.Timedelta("150D")) & (m1.index < END)]


def _cached(name, build):
    f = OUT / name
    if f.exists():
        return pd.read_csv(f)
    df = build()
    df.to_csv(f, index=False)
    return df


# ------------------------------------------------------------------ families: (unit, time, R)

def fam_v12():
    cols = ["pair", "range_tf", "entry_tf", "k", "trigger", "entry_type", "stop_type", "mgmt", "status", "R", "fill_time"]
    parts = [pd.read_csv(OUT / f"trades_{p}.csv", usecols=cols) for p in ("design", "check", "final")]
    d = pd.concat(parts)
    d = d[(d["status"] == "filled") & d["R"].notna()]
    unit = d[cols[:8]].astype(str).agg(" ".join, axis=1)
    return pd.DataFrame({"unit": unit, "time": d["fill_time"], "R": d["R"]})


def fam_romeo():
    from backtest.romeo import run

    def build():
        rows = []
        for pair in K.PAIRS:
            rows += run(_m1(K.PAIRS[pair]["file"]), pair, START, END)
        return pd.DataFrame(rows)
    d = _cached("wf_romeo_all.csv", build)
    d = d[d["R_half"].notna()]
    out = []
    base = d["pair"] + " " + d["tf"] + " " + d["kind"]
    for name, m in (("none", np.ones(len(d), bool)), ("F1", d["F1"].astype(bool)), ("F2", d["F2"].astype(bool)),
                    ("F3", d["F3"].astype(bool)), ("ALL", d["F1"].astype(bool) & d["F2"].astype(bool) & d["F3"].astype(bool))):
        m = np.asarray(m, bool)
        out.append(pd.DataFrame({"unit": base[m] + " " + name, "time": d["time"][m], "R": d["R_half"][m]}))
    return pd.concat(out)


def fam_search():
    from backtest.search import FLAGS, scan

    def build():
        rows = []
        for pair in K.PAIRS:
            rows += scan(_m1(K.PAIRS[pair]["file"]), pair, partner=_m1(PARTNER[pair]))
        return pd.DataFrame(rows)
    d = _cached("wf_search_all.csv", build)
    d = d[d["R"].notna()].reset_index(drop=True)
    flags = [f for f in list(FLAGS) + ["smt"] if f in d.columns]
    F = {f: np.array(d[f].fillna(False).astype(bool), dtype=bool) for f in flags}
    if "smt" in F and "smt_known" in d.columns:
        F["smt"] &= d["smt_known"].fillna(False).astype(bool).to_numpy()
    base = (d["pair"] + " " + d["tf"] + " " + d["base"]).to_numpy()
    out = [pd.DataFrame({"unit": base, "time": d["time"], "R": d["R"]})]
    for combo in itertools.chain(itertools.combinations(flags, 1), itertools.combinations(flags, 2)):
        m = np.logical_and.reduce([F[f] for f in combo])
        if m.sum() >= MIN_TRAIN:
            out.append(pd.DataFrame({"unit": base[m] + " +" + "+".join(combo), "time": d["time"][m], "R": d["R"][m]}))
    return pd.concat(out)


def fam_edge_hunt():
    d = pd.read_csv(OUT / "edge_hunt_trades.csv.gz")
    return pd.DataFrame({"unit": d["fam"] + " " + d["var"] + " " + d["mkt"], "time": d["time"], "R": d["gross"] - d["cost"]})


def fam_advanced():
    d = pd.read_csv(OUT / "advanced_trades.csv")
    d = d[d["R"].notna()]
    return pd.DataFrame({"unit": d["model"] + " " + d["tf"] + " " + d["pair"], "time": d["time"], "R": d["R"]})


def fam_breaker():
    d = pd.read_csv(OUT / "breaker_trades.csv")
    d = d[d["R"].notna()]
    return pd.DataFrame({"unit": d["variant"] + " " + d["pair"], "time": d["time"], "R": d["R"]})


FAMILIES = {"v1.2 CRT variants": fam_v12, "Romeo v2": fam_romeo, "Combination search + SMT": fam_search,
            "Edge hunt v3 (ATR units)": fam_edge_hunt, "v4 advanced models": fam_advanced, "v6 breakers": fam_breaker}


# ------------------------------------------------------------------ the walk-forward

def tstat(g):
    n = g["n"]
    se = np.sqrt(g["var"] / n)
    return np.where((n >= MIN_TRAIN) & (se > 0), g["mean"] / se, np.nan)


def walk(d: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    d = d.copy()
    d["year"] = pd.to_datetime(d["time"], utc=True, format="mixed").dt.year
    d = d[d["year"] >= 2021]
    rows, picks = [], []
    for y in TEST_YEARS:
        train, test = d[d["year"] < y], d[d["year"] == y]
        g = train.groupby("unit")["R"].agg(n="count", mean="mean", var="var")
        g["t"] = tstat(g)
        g = g.dropna(subset=["t"]).sort_values("t", ascending=False)
        best = g.index[0] if len(g) else None
        good = list(g.index[g["t"] >= T_ALL])
        a = test[test["unit"] == best]["R"] if best else pd.Series(dtype=float)
        b = test[test["unit"].isin(good)].groupby("unit")["R"].mean() if good else pd.Series(dtype=float)
        bt = test[test["unit"].isin(good)]["R"] if good else pd.Series(dtype=float)
        rows.append({"year": y, "units": len(g), "A unit": best, "A train t": g["t"].iloc[0] if len(g) else np.nan,
                     "A train avg": g["mean"].iloc[0] if len(g) else np.nan, "A trades": len(a),
                     "A avg R": a.mean() if len(a) else np.nan, "B units": len(good), "B trades": len(bt),
                     "B avg R": b.mean() if len(b) else np.nan})          # B: equal weight per unit
        picks.append({"year": y, "A": best, "B": good[:10]})
    return pd.DataFrame(rows), picks


def verdict(t: pd.DataFrame, k: str) -> dict:
    yrs = t[f"{k} avg R"]
    n = int(t[f"{k} trades"].sum())
    w = t[f"{k} trades"]
    if k == "A":
        overall = (yrs * w).sum() / w.sum() if w.sum() else np.nan
    else:   # B: average of the yearly equal-weight results, weighted by trades
        overall = (yrs.fillna(0) * w).sum() / w.sum() if w.sum() else np.nan
    pos = int((yrs > 0).sum())
    return {"avg": overall, "trades": n, "years_pos": pos,
            "pass": bool(n >= 30 and overall == overall and overall > 0 and pos >= 3)}


# ------------------------------------------------------------------ trend (daily long history)

def trend_walk():
    from backtest.trend_long import COST, SIGNALS, load, market_returns
    data = load()
    rets = {code: pd.DataFrame({m: market_returns(s, code, COST.get(m, 0.0002)) for m, s in data.items()}) for code in SIGNALS}
    out = {}
    for name, pick in (("portfolio", lambda df: df.mean(axis=1, skipna=True)), ("GBPUSD", lambda df: df["GBPUSD"]),
                       ("XAUUSD", lambda df: df["XAUUSD"])):
        series = {c: pick(r).dropna() for c, r in rets.items()}
        oos, chosen = [], []
        first = 1981 if name != "XAUUSD" else 2011
        for y in range(first, 2027):
            sh = {}
            for c, s in series.items():
                tr = s[s.index.year < y]
                if len(tr) > 252 * 5 and tr.std() > 0:
                    sh[c] = tr.mean() / tr.std() * np.sqrt(252)
            if not sh:
                continue
            c = max(sh, key=sh.get)
            chosen.append((y, c))
            oos.append(series[c][series[c].index.year == y])
        o = pd.concat(oos)

        def sharpe(x):
            return x.mean() / x.std() * np.sqrt(252) if len(x) > 60 and x.std() > 0 else np.nan
        out[name] = {"1981-2012": sharpe(o[o.index.year <= 2012]), "2013-2026": sharpe(o[o.index.year >= 2013]),
                     "2021-2026": sharpe(o[o.index.year >= 2021]), "chosen": chosen[-6:],
                     "pass": bool(sharpe(o[o.index.year >= 2013]) > 0.3)}
    return out


def main() -> int:
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 20)
    lines = ["# Spec v7 result: walk-forward for every strategy", "",
             "Spec: `docs/spec-v7-walkforward.md` (committed before the run). Each year, the unit is chosen using only "
             "earlier years, then traded blind for the year. Only those blind years are shown. R after spread "
             "(edge hunt in ATR units).", ""]
    summary = []
    for fam, fn in FAMILIES.items():
        d = fn()
        t, picks = walk(d)
        va, vb = verdict(t, "A"), verdict(t, "B")
        summary.append({"family": fam, "units": d["unit"].nunique(),
                        "A avg": va["avg"], "A trades": va["trades"], "A years +": va["years_pos"], "A pass": va["pass"],
                        "B avg": vb["avg"], "B trades": vb["trades"], "B years +": vb["years_pos"], "B pass": vb["pass"]})
        print(f"\n== {fam} ({d['unit'].nunique()} units)")
        print(t.round(3).to_string(index=False))
        lines += [f"## {fam} ({d['unit'].nunique():,} units)", "",
                  "| Test year | Pick A (best past t) | past t | past avg | trades | **blind avg R** | Pick B units (t ≥ 2) | trades | **blind avg R** |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for _, r in t.iterrows():
            def f(x, p="+.3f"):
                return "—" if x != x or x is None else format(x, p)
            lines.append(f"| {r['year']} | {r['A unit'] or '—'} | {f(r['A train t'], '.2f')} | {f(r['A train avg'])} | "
                         f"{r['A trades']} | **{f(r['A avg R'])}** | {r['B units']} | {r['B trades']} | **{f(r['B avg R'])}** |")
        b_text = (f"{vb['avg']:+.3f} over {vb['trades']} trades, {vb['years_pos']} of 4" if vb["trades"]
                  else "no unit ever reached t ≥ 2 in training, so no trades")
        lines += ["", f"Pick A: blind average {va['avg']:+.3f} over {va['trades']} trades, positive in {va['years_pos']} of 4 years "
                  f"-> **{'PASS' if va['pass'] else 'fail'}**. Pick B: {b_text} -> **{'PASS' if vb['pass'] else 'fail'}**.", ""]
    s = pd.DataFrame(summary)
    print("\n== SUMMARY")
    print(s.round(3).to_string(index=False))
    tr = trend_walk()
    print("\n== TREND (next-year Sharpe)")
    for k, v in tr.items():
        print(k, {a: (round(b, 2) if isinstance(b, float) else b) for a, b in v.items()})
    lines += ["## v5 trend following (daily, signal re-chosen every year from all earlier years)", "",
              "| Market | blind Sharpe 1981–2012 | **2013–2026** | 2021–2026 | last picks | Pass |", "|---|---|---|---|---|---|"]
    for k, v in tr.items():
        lines.append(f"| {k} | {v['1981-2012']:.2f} | **{v['2013-2026']:.2f}** | {v['2021-2026']:.2f} | "
                     f"{', '.join(f'{y}:{c}' for y, c in v['chosen'])} | {'PASS' if v['pass'] else 'fail'} |")
    lines += ["", "## Summary", "", "| Family | Units | Pick A blind avg | trades | years + | Pick B blind avg | trades | years + |",
              "|---|---|---|---|---|---|---|---|"]
    for _, r in s.iterrows():
        b = f"{r['B avg']:+.3f}{' PASS' if r['B pass'] else ''}" if r["B trades"] else "none qualified"
        lines.append(f"| {r['family']} | {r['units']:,} | {r['A avg']:+.3f}{' PASS' if r['A pass'] else ''} | {r['A trades']} | "
                     f"{r['A years +']} | {b} | {r['B trades']} | {r['B years +']} |")
    REPORT.write_text("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

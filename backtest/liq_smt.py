"""Spec v17 (docs/spec-v17-liquidity-smt.md): the v14 liquidity models with and without SMT divergence.

Reuses the v14 setups and scored trades (backtest/out/liquidity_ie_*), adds the SMT flag from the partner
market (GBP/USD<->EUR/USD, gold<->silver), known before each entry.

    python -m backtest.liq_smt
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.advanced import START  # noqa: E402
from backtest.report_liquidity import stats  # noqa: E402
from backtest.walkforward import verdict, walk  # noqa: E402
from engine import config as K  # noqa: E402
from engine.candles import clean, load_m1_csv, resample  # noqa: E402

OUT = ROOT / "backtest" / "out"
REPORT = ROOT / "backtest" / "reports" / "liquidity_smt_v17.md"
PARTNER = {"GBPUSD": "data/eurusd-m1-bid-2021-11-01-2026-11-19.zip",
           "XAUUSD": "data/xagusd-m1-bid-2021-11-01-2026-11-19.zip",
           "EURUSD": "data/gbpusd-m1-bid-2021-11-01-2026-11-19.csv",     # roles swapped (fresh-market check)
           "XAGUSD": "data/xauusd-m1-bid-2021-11-01-2026-11-19.csv"}
TF_SEC = {"M5": 300, "M15": 900, "H1": 3600, "H4": 14400, "D1": 86400}
MODEL = {"sniper": "4-candle sniper", "core": "induce → trap"}
YEARS = range(2022, 2027)


def smt_flags(pair: str, setups: list[dict], trades: pd.DataFrame, main_file: str) -> pd.Series:
    """SMT flag (True/False, NaN if unknown) for each trade row of one pair."""
    m1, _ = clean(load_m1_csv(ROOT / main_file))
    m1 = m1[m1.index >= START - pd.Timedelta("400D")]               # same frames as backtest/liquidity_ie
    p1, _ = clean(load_m1_csv(ROOT / PARTNER[pair]))
    pt = p1.index.as_unit("ns").asi8
    ph, pl = p1["high"].to_numpy(), p1["low"].to_numpy()
    by_key = {(s["tf"], s["model"], s["entry_kind"], s["place_ns"], "long" if s["mir"] else "short"): s
              for s in setups if s["pair"] == pair}
    out = pd.Series(np.nan, index=trades.index, dtype=object)
    for tf in trades["tf"].unique():
        E = resample(m1, tf, "utc0")
        P = resample(p1, tf, "utc0")
        pos = {t: i for i, t in enumerate(P.index.as_unit("ns").asi8)}
        Et = E.index.as_unit("ns").asi8
        PH, PL = P["high"].to_numpy(), P["low"].to_numpy()
        sub = trades[trades["tf"] == tf]
        for ix, r in sub.iterrows():
            s = by_key.get((tf, r["model"], r["entry_kind"], int(r["place_ns"]), r["direction"]))
            if s is None:
                continue
            sell = r["direction"] == "short"
            if s["model"] == "sniper":
                a, b = pos.get(int(Et[s["idx"]["c1"]])), pos.get(int(Et[s["idx"]["c2"]]))
                if a is None or b is None:
                    continue
                out[ix] = bool(PH[b] <= PH[a]) if sell else bool(PL[b] >= PL[a])     # partner did NOT sweep
            else:
                t_hr = int(Et[s["idx"]["retail_high"]])
                k = pos.get(t_hr)
                if k is None:
                    continue
                lo = int(np.searchsorted(pt, t_hr + TF_SEC[tf] * 10**9, side="left"))
                hi = int(np.searchsorted(pt, int(r["time"]), side="left"))         # minutes before the fill
                if hi <= lo:
                    out[ix] = True
                    continue
                out[ix] = bool(ph[lo:hi].max() <= PH[k]) if sell else bool(pl[lo:hi].min() >= PL[k])
    return out


def main() -> int:
    setups = pd.read_pickle(OUT / "liquidity_ie_setups.pkl")
    d = pd.read_csv(OUT / "liquidity_ie_trades.csv", low_memory=False)
    d = d[(d["family"] == "pure") & d["R"].notna()].copy()
    d["year"] = pd.to_datetime(d["time"], unit="ns", utc=True).dt.year
    d["smt"] = pd.Series([None] * len(d), index=d.index, dtype=object)
    for pair in K.PAIRS:
        m = d["pair"] == pair
        d.loc[m, "smt"] = smt_flags(pair, setups, d[m], K.PAIRS[pair]["file"])
        print(pair, "SMT flags done", flush=True)
    d.to_csv(OUT / "liq_smt_trades.csv", index=False)
    known = d[d["smt"].notna()].copy()
    known["smt"] = known["smt"].astype(bool)
    lines = ["# Spec v17 result: liquidity models with and without SMT divergence", "",
             "Spec: `docs/spec-v17-liquidity-smt.md` (committed before the run). Same v14 trades (GBP/USD + gold, "
             "Nov 2021 – Nov 2026, after Ore's spreads), split by whether the partner market (EUR/USD / silver) "
             f"failed to take its matching level. SMT present on {known['smt'].mean():.0%} of trades.", "",
             "| Model · row | SMT trades | SMT avg R | SMT years + | SMT hit vs chance | No-SMT trades | No-SMT avg R | Counts? |",
             "|---|---|---|---|---|---|---|---|"]
    rows = []
    for (model, kind, tf, mg), g in known.groupby(["model", "entry_kind", "tf", "mgmt"]):
        a, b = stats(g[g["smt"]]), stats(g[~g["smt"]])
        ok = bool(a["consistent"] and a["avg"] > b["avg"])
        rows.append({"model": model, "row": f"{tf} {kind} · mgmt {mg}", "smt": a, "no": b, "ok": ok})
    rows.sort(key=lambda x: -(x["smt"]["avg"] if x["smt"]["avg"] == x["smt"]["avg"] else -9))
    for x in rows:
        a, b = x["smt"], x["no"]
        lines.append(f"| {MODEL[x['model']]} · {x['row']} | {a['trades']} | **{a['avg']:+.3f}** | {a['years+']} | "
                     f"{a['hit']:.0f}% vs {a['chance']:.0f}% | {b['trades']} | {b['avg']:+.3f} | {'YES' if x['ok'] else 'no'} |")
    sm, no = known[known["smt"]], known[~known["smt"]]
    lines += ["", f"**Rows that count: {sum(x['ok'] for x in rows)} of {len(rows)}.** All trades: SMT {sm['R'].mean():+.3f}R "
              f"({len(sm):,} trades) vs no SMT {no['R'].mean():+.3f}R ({len(no):,} trades).", "",
              "| Model | SMT avg R | No-SMT avg R | SMT walk-forward |", "|---|---|---|---|"]
    for model in ("sniper", "core"):
        g = known[known["model"] == model]
        s = g[g["smt"]]
        unit = s["entry_kind"] + " " + s["tf"] + " " + s["mgmt"] + " " + s["pair"]
        wf, _ = walk(pd.DataFrame({"unit": unit, "time": pd.to_datetime(s["time"], unit="ns", utc=True).astype(str),
                                   "R": s["R"]}))
        v = verdict(wf, "A")
        lines.append(f"| {MODEL[model]} | {s['R'].mean():+.3f} | {g[~g['smt']]['R'].mean():+.3f} | blind {v['avg']:+.3f}R, "
                     f"{v['trades']} trades, {v['years_pos']} of 4 years → {'PASS' if v['pass'] else 'fail'} |")
    REPORT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

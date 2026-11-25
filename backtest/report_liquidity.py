"""Spec v14 report: yearly results, target hits vs chance, consistency and walk-forward per family.

    python -m backtest.report_liquidity     -> backtest/reports/liquidity_v14.md
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from backtest.walkforward import verdict, walk

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "backtest" / "out"
REPORT = ROOT / "backtest" / "reports" / "liquidity_v14.md"
YEARS = range(2022, 2027)
MODEL = {"sniper": "4-candle sniper", "core": "induce → trap"}


def stats(x: pd.DataFrame) -> dict:
    r = x["R"].dropna()
    yr = x.dropna(subset=["R"]).groupby("year")["R"].mean()
    y = x[x["hit_T2"].notna()]
    p = y["p_T2"]
    z = (y["hit_T2"].sum() - p.sum()) / np.sqrt((p * (1 - p)).sum()) if len(y) else np.nan
    out = {"trades": len(r), "avg": r.mean() if len(r) else np.nan, "hit": y["hit_T2"].mean() * 100 if len(y) else np.nan,
           "chance": p.mean() * 100 if len(y) else np.nan, "z": z,
           **{str(k): yr.get(k, np.nan) for k in YEARS},
           "years+": int(sum(1 for k in YEARS if yr.get(k, -1) > 0))}
    out["consistent"] = bool(out["trades"] >= 30 and out["avg"] > 0 and out["years+"] >= 4
                             and out["hit"] >= out["chance"])
    return out


def fmt(v, p="+.2f"):
    return "—" if v is None or v != v else format(v, p)


def main() -> int:
    d = pd.read_csv(OUT / "liquidity_ie_trades.csv")
    d["year"] = pd.to_datetime(d["time"], unit="ns", utc=True).dt.year
    rows = []
    pure = d[d["family"] == "pure"]
    for (model, kind, tf, mg), g in pure.groupby(["model", "entry_kind", "tf", "mgmt"]):
        filters = [("all", g)]
        if tf in ("H1", "M15", "M5"):
            filters.append(("NY session", g[g["ny"]]))
        filters.append(("daily bias", g[g["bias"]]))
        for fname, x in filters:
            rows.append({"family": f"{MODEL[model]} alone", "row": f"{tf} {kind} · {fname} · mgmt {mg}", **stats(x)})
    crt = d[d["family"] == "crt"]
    for (model, ctf, mg), g in crt.groupby(["model", "crt_tf", "mgmt"]):
        etf = "M15" if ctf == "D1" else "M5"
        rows.append({"family": "with CRT", "row": f"{MODEL[model]} · CRT {ctf}→{etf} · {mg}", **stats(g)})
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "liquidity_v14_rows.csv", index=False)
    lines = ["# Spec v14 result: Inter Equity liquidity strategy, alone and paired with CRT", "",
             "Spec: `docs/spec-v14-liquidity.md` (committed before any run). GBP/USD + gold, Nov 2021 – Nov 2026, Exness "
             "candles (GMT+0), Ore's spreads, 1-minute outcomes. Avg = average R per trade after spread. Hit = final "
             "target reached before the stop; chance = what a random market gives for the same distances. "
             "Mgmt A = all out at the target; B = half at the nearest liquidity, stop to entry, rest at the target.", ""]
    for fam in t["family"].unique():
        x = t[t["family"] == fam].sort_values("avg", ascending=False)
        lines += [f"## {fam}", "", f"{len(x)} rows; consistent: **{int(x['consistent'].sum())}**. Best 12 by average:", "",
                  "| Row | Trades | Avg R | 2022 | 2023 | 2024 | 2025 | 2026 | Years + | Hit vs chance | Consistent |",
                  "|---|---|---|---|---|---|---|---|---|---|---|"]
        for _, r in x.head(12).iterrows():
            lines.append(f"| {r['row']} | {r['trades']} | **{fmt(r['avg'])}** | " + " | ".join(fmt(r[str(k)]) for k in YEARS)
                         + f" | {r['years+']} | {fmt(r['hit'], '.0f')}% vs {fmt(r['chance'], '.0f')}% | "
                         f"{'YES' if r['consistent'] else 'no'} |")
        allx = x["trades"].sum()
        lines += ["", f"All {len(x)} rows together: {allx:,} trades (rows overlap), median row average {fmt(x['avg'].median())}.", ""]
    # walk-forward per family (unit = row + pair)
    lines += ["## Walk-forward (choose on past years, trade the next year blind)", "",
              "| Family | Units | Blind avg R | Trades | Blind years + of 4 | Verdict |", "|---|---|---|---|---|---|"]
    fams = {"4-candle sniper alone": pure[pure["model"] == "sniper"], "induce → trap alone": pure[pure["model"] == "core"],
            "with CRT": crt}
    for name, g in fams.items():
        unit = (g["model"] + " " + g["entry_kind"] + " " + g["tf"] + " " + g["mgmt"] + " "
                + g.get("crt_tf", pd.Series("", index=g.index)).fillna("") + " " + g["pair"])
        if name != "with CRT":
            unit = unit + np.where(g["ny"], " NY", "")
        wf, _ = walk(pd.DataFrame({"unit": unit, "time": pd.to_datetime(g["time"], unit="ns", utc=True).astype(str),
                                   "R": g["R"]}).dropna(subset=["R"]))
        v = verdict(wf, "A")
        lines.append(f"| {name} | {unit.nunique()} | {fmt(v['avg'], '+.3f')} | {v['trades']} | {v['years_pos']} | "
                     f"{'PASS' if v['pass'] else 'fail'} |")
    REPORT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

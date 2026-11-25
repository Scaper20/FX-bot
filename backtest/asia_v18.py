"""Spec v18 (docs/spec-v18-asia.md): Asian-session trades for both live strategies, vs London/NY and Late.

Reads existing trade logs only (CRT body-close rule, order-block v16 logs).

    python -m backtest.asia_v18
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.pattern_stats import ore_rules  # noqa: E402
from backtest.report_liquidity import YEARS, stats  # noqa: E402

OUT = ROOT / "backtest" / "out"
REPORT = ROOT / "backtest" / "reports" / "asia_v18.md"
SESS = ("asia", "lnny", "late")
LABEL = {"asia": "Asia", "lnny": "London/NY", "late": "Late"}
ENTRY = {"E1": "market at MSS close", "E2": "FVG near edge", "E3": "FVG middle", "E4": "OB open", "E5": "OB middle"}


def bucket(t: pd.Series, lnny: pd.Series) -> pd.Series:
    """asia = 00:00-07:00 London time; lnny = Ore's London/NY rule; late = the rest."""
    hr = t.dt.tz_convert("Europe/London").dt.hour
    return pd.Series(np.where(lnny, "lnny", np.where(hr < 7, "asia", "late")), index=t.index)


def crt() -> pd.DataFrame:
    parts = []
    for per in ("design", "check", "final"):
        d = pd.read_csv(OUT / f"trades_{per}.csv", low_memory=False)
        d = d[(d["status"] == "filled") & d["R"].notna()].copy()
        d["decision_time"] = pd.to_datetime(d["decision_time"], utc=True)
        lnny = d["session"].fillna("").isin(["london", "newyork", "overlap"])
        d["sess"] = bucket(d["decision_time"], lnny)
        d = d[ore_rules(d.assign(session="london"))]          # Ore's other rules, session rule swapped out
        parts.append(d)
    t = pd.concat(parts, ignore_index=True)
    risk = (t["stop"] - t["entry"]).abs()
    tgt = np.where(t["mgmt"].str.endswith("T3"), t["T3_px"], t["T2_px"])
    t["p_T2"] = risk / (risk + (t["entry"] - tgt).abs())
    t["hit_T2"] = (t["exit_reason"] == "target").astype(float)
    t["year"] = t["decision_time"].dt.year
    return t


def smc(prefix: str, pairs: tuple[str, ...], tfs: tuple[str, ...]) -> pd.DataFrame:
    parts = []
    for p in pairs:
        for tf in tfs:
            f = OUT / f"{prefix}_{p}_{tf}.csv"
            if f.exists():
                parts.append(pd.read_csv(f))
    d = pd.concat(parts, ignore_index=True)
    d = d[d["bias_both"].astype(bool) & d["R"].notna()].copy()
    t = pd.to_datetime(d["mss_time"], unit="ns", utc=True)
    d["sess"] = bucket(t, d["session"].astype(bool))
    d["year"] = t.dt.year
    d["hit_T2"], d["p_T2"] = d["hit"], d["chance"]
    return d


def f(v, p="+.3f"):
    return "—" if v is None or v != v else format(v, p)


def cell(s: dict) -> str:
    return f"{s['trades']} · **{f(s['avg'])}** · {s['years+']}/5 · {f(s['hit'], '.0f')}% vs {f(s['chance'], '.0f')}%"


def table(groups, title: str) -> tuple[list[str], list[tuple]]:
    lines = [f"### {title}", "", "Each cell: trades · avg R after spread · years positive · target hit vs chance. "
             "✓ = consistent.", "", "| Row | Asia | London/NY | Late |", "|---|---|---|---|"]
    passes = []
    for name, g in groups:
        cells = []
        for s in SESS:
            st = stats(g[g["sess"] == s])
            cells.append(cell(st) + (" ✓" if st["consistent"] else ""))
            if s == "asia" and st["consistent"]:
                passes.append((title, name, st))
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    return lines + [""], passes


def yearly(g: pd.DataFrame) -> str:
    return " · ".join(f"{y}: {f(g[g['year'] == y]['R'].mean(), '+.2f')} ({(g['year'] == y).sum()})" for y in YEARS)


def main() -> int:
    t = crt()
    ob = smc("smc", ("GBPUSD", "XAUUSD"), ("H1", "M15"))
    fresh = smc("smcfresh", ("EURUSD", "XAGUSD"), ("H1",))
    L = ["# Spec v18 result: Asian-session trades", "",
         "Spec: `docs/spec-v18-asia.md` (committed before the run). Asia = trigger / MSS candle closing 00:00–07:00 "
         "London time. GBP/USD + gold, Nov 2021 – Nov 2026, after Ore's spreads. Existing trade logs only.", ""]
    share = t.groupby("sess").size() / len(t)
    L += ["## Summary", "",
          "| Strategy | Asia | London/NY | Late |", "|---|---|---|---|"]
    L.append("| CRT, all options (Ore's other rules) | " + " | ".join(cell(stats(t[t["sess"] == s])) for s in SESS) + " |")
    h = ob[(ob["tf"] == "H1") & (ob["entry"] == "E4")]
    L.append("| Order block H1 OB open (live strategy) | " + " | ".join(cell(stats(h[h["sess"] == s])) for s in SESS) + " |")
    L.append("| Order block, all TFs and entries | " + " | ".join(cell(stats(ob[ob["sess"] == s])) for s in SESS) + " |")
    L += ["", f"CRT trades by session: Asia {share.get('asia', 0):.0%}, London/NY {share.get('lnny', 0):.0%}, "
          f"Late {share.get('late', 0):.0%}.", ""]
    # no-cost check for the order block (R_free)
    L += ["Order block before costs (no spread): " + ", ".join(
        f"{LABEL[s]} {f(ob[ob['sess'] == s]['R_free'].mean())}R" for s in SESS) + ".", ""]

    allpass = []
    g1 = [("All options", t)] + [(f"{tf} · {e} · {m}", g) for (tf, e, m), g in
                                 t.groupby(["range_tf", "entry_type", "mgmt"])]
    lines, p = table(g1, "CRT by range timeframe · entry · management")
    L += lines
    allpass += p
    g2 = [(f"{tf} · {ENTRY[e]}", g) for (tf, e), g in ob.groupby(["tf", "entry"])]
    lines, p = table(g2, "Order block by timeframe · entry (D1+H4 bias)")
    L += lines
    allpass += p
    L += ["### Pairs separately (headline rows)", "", "| Row | Pair | Asia | London/NY |", "|---|---|---|---|"]
    for name, g in (("CRT all options", t), ("Order block H1 OB open", h)):
        for pair, gp in g.groupby("pair"):
            L.append(f"| {name} | {pair} | {cell(stats(gp[gp['sess'] == 'asia']))} | {cell(stats(gp[gp['sess'] == 'lnny']))} |")
    L += ["", "## Asia rows that passed the consistency rule", ""]
    if not allpass:
        L.append("None.")
    for title, name, st in allpass:
        L.append(f"- {title}: **{name}**: {cell(st)}.")
        if title.startswith("Order block") and "H1" in name:
            e = next(k for k, v in ENTRY.items() if name.endswith(v))
            fr = fresh[(fresh["entry"] == e) & (fresh["sess"] == "asia")]
            fs = stats(fr)
            L.append(f"  - Fresh markets (EUR/USD + silver, unchanged rule): {cell(fs)} → "
                     f"{'PASS' if fs['consistent'] else 'FAIL'}. Years: {yearly(fr)}")
        elif title.startswith("Order block"):
            L.append("  - Fresh markets: M15 order-block logs for EUR/USD + silver don't exist; not run.")
        else:
            L.append("  - Fresh markets (EUR/USD + silver): CRT trade logs for those markets don't exist; not run.")
    REPORT.write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

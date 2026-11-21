"""Spec v11 (docs/spec-v11-market-entry.md): market entry at the trigger close (E1) vs limit entries (E2-E5),
compared on exactly the same setups, Nov 2021 - Nov 2026.

    python -m backtest.market_entry
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "backtest" / "out"
REPORT = ROOT / "backtest" / "reports" / "market_entry_v11.md"
KEY = ["pair", "range_tf", "entry_tf", "range_open", "direction", "k", "trigger", "decision_time"]
COLS = KEY + ["entry_type", "stop_type", "mgmt", "status", "R", "exit_reason", "rr_T2", "session", "friday_late",
              "trend_struct", "htf_ob", "htf_fvg", "fill_time"]
STOP = "S1p"
MGMTS = {"M1_T2": "all out at the opposite side", "M2_T2": "half at 50%, stop to entry, rest at the opposite side"}
LIMITS = {"E2": "limit at FVG edge", "E3": "limit at FVG middle", "E4": "limit at OB open", "E5": "limit at OB middle"}
YEARS = range(2022, 2027)


def load() -> pd.DataFrame:
    parts = [pd.read_csv(OUT / f"trades_{p}.csv", usecols=COLS) for p in ("design", "check", "final")]
    d = pd.concat(parts, ignore_index=True)
    d = d[(d["stop_type"] == STOP) & d["mgmt"].isin(MGMTS)]
    d["year"] = pd.to_datetime(d["decision_time"], utc=True).dt.year
    d["ore_rules"] = (d["session"].notna() & (d["session"] != "") & ~d["friday_late"].astype(bool)
                      & ((d["trend_struct"] == "with") | d["htf_ob"].astype(bool) | d["htf_fvg"].astype(bool)))
    return d


def summarize(r: pd.Series, years: pd.Series) -> dict:
    r = r.dropna()
    yr = r.groupby(years.loc[r.index]).mean()
    return {"trades": len(r), "avg R": r.mean() if len(r) else np.nan, "total R": r.sum(),
            **{str(y): yr.get(y, np.nan) for y in YEARS},
            "years +": int(sum(1 for y in YEARS if yr.get(y, np.nan) > 0))}


def fmt(x, p="+.3f"):
    return "—" if x != x else format(x, p)


def main() -> int:
    d = load()
    lines = ["# Spec v11 result: instant market entry vs limit orders, same setups", "",
             "Spec: `docs/spec-v11-market-entry.md` (committed before the run). v1.2 engine trade logs, Nov 2021 – Nov 2026, "
             "GBP/USD + gold, stop = sweep extreme + 2 spreads, spread included. E1 = market at the trigger candle's close.", ""]
    verdicts = []
    for scope, sub in (("All setups", d), ("Ore's rules only", d[d["ore_rules"]])):
        for mg, mlabel in MGMTS.items():
            x = sub[sub["mgmt"] == mg]
            e1 = x[x["entry_type"] == "E1"].set_index(KEY)
            s = summarize(e1["R"].reset_index(drop=True), e1["year"].reset_index(drop=True))
            ok = s["trades"] >= 100 and s["avg R"] > 0 and s["years +"] >= 4
            verdicts.append((scope, mlabel, s, ok))
            # chance for E1 (all-out at opposite side only: hit = reached target)
            chance = ""
            if mg == "M1_T2":
                hit = (e1["exit_reason"] == "target").mean() * 100
                ch = (1 / (1 + e1["rr_T2"])).mean() * 100
                chance = f" Target hit {hit:.1f}% vs chance {ch:.1f}%."
            lines += [f"## {scope} · {mlabel}", "",
                      f"**Market entry (E1):** {s['trades']} trades, average {fmt(s['avg R'])}R, total {s['total R']:+.1f}R, "
                      f"positive in {s['years +']} of 5 years ({', '.join(f'{y}: {fmt(s[str(y)], '+.2f')}' for y in YEARS)}).{chance} "
                      f"-> **{'WORKS' if ok else 'does not work'}** by the spec rule.", "",
                      "| Limit entry | Limit filled: trades / avg R | E1 on those same setups | **Limit cancelled or expired: setups** | **E1 on those setups (avg R)** | E1 on them, years + |",
                      "|---|---|---|---|---|---|"]
            for le, llabel in LIMITS.items():
                lim = x[x["entry_type"] == le].set_index(KEY)
                both = lim.join(e1[["R", "year"]], rsuffix="_e1", how="inner")
                filled = both[both["status"] == "filled"]
                missed = both[both["status"].isin(["cancelled", "expired"])]
                ms = summarize(missed["R_e1"].reset_index(drop=True), missed["year_e1"].reset_index(drop=True))
                lines.append(f"| {llabel} | {filled['R'].notna().sum()} / {fmt(filled['R'].mean())} | {fmt(filled['R_e1'].mean())} | "
                             f"{len(missed)} | **{fmt(ms['avg R'])}** | {ms['years +']} of 5 |")
            lines.append("")
    lines += ["## Verdict", "", "| Scope | Management | E1 trades | E1 avg R | Years + | Works? |", "|---|---|---|---|---|---|"]
    for scope, mlabel, s, ok in verdicts:
        lines.append(f"| {scope} | {mlabel} | {s['trades']} | {fmt(s['avg R'])} | {s['years +']} of 5 | {'YES' if ok else 'no'} |")
    REPORT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

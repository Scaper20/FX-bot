"""Spec v12 part 1: the CRT premise with Ore's body-close rule vs the old range rule, side by side.
Exness candles (GMT+0), D1 and H4, k = 1 and 2. Entry at C2's close, stop at the sweep extreme,
targets 50% of C1 and C1's far side; 1-minute outcomes, Ore's spreads.

    python -m backtest.premise_v12
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

YEARS = range(2022, 2027)


def run() -> pd.DataFrame:
    rows = []
    for pair in K.PAIRS:
        m1, _ = clean(load_m1_csv(ROOT / K.PAIRS[pair]["file"]))
        for tf in ("D1", "H4"):
            R = resample(m1, tf, "utc0")
            out = Outcome(m1, K.PAIRS[pair]["spread"], tf)
            t_open = R.index.as_unit("ns").asi8
            t_close = pd.DatetimeIndex(R["close_time_utc"]).as_unit("ns").asi8
            for mir in (False, True):
                sg = -1.0 if mir else 1.0
                o, h, l, c = arrays(R, mir)
                for i in range(20, len(R) - 3):
                    if t_open[i] < START.value or h[i] <= l[i]:
                        continue
                    for k in (1, 2):
                        s = i + k
                        if k == 2 and (h[i + 1] > h[i] or l[i + 1] < l[i]):
                            continue
                        if not (h[s] > h[i] and l[s] >= l[i] and l[i] < c[s] < h[i]):
                            continue
                        body = min(o[i], c[i]) < c[s] < max(o[i], c[i])
                        mid, far = (h[i] + l[i]) / 2, l[i]
                        res = out("long" if mir else "short", sg * c[s], sg * h[s],
                                  sg * mid if far < mid < c[s] else None, sg * far, int(t_close[s]))
                        if res:
                            res.update(pair=pair, tf=tf, k=k, body=bool(body))
                            rows.append(res)
    return pd.DataFrame(rows)


def stats(x: pd.DataFrame) -> dict:
    out = {"setups": len(x)}
    for lv in ("T1", "T2"):
        y = x[x[f"hit_{lv}"].notna()]
        p = y[f"p_{lv}"]
        out[f"{lv} hit%"] = y[f"hit_{lv}"].mean() * 100
        out[f"{lv} chance%"] = p.mean() * 100
        out[f"{lv} z"] = (y[f"hit_{lv}"].sum() - p.sum()) / np.sqrt((p * (1 - p)).sum()) if len(y) else np.nan
    r = x["R"].dropna()
    out["avg R"] = r.mean()
    yr = x.assign(y=pd.to_datetime(x["time"], unit="ns", utc=True).dt.year).groupby("y")["R"].mean()
    out["years +"] = int(sum(1 for y in YEARS if yr.get(y, np.nan) > 0))
    return out


def main() -> int:
    df = run()
    df.to_csv(ROOT / "backtest" / "out" / "premise_v12.csv", index=False)
    rows = []
    for name, sub in (("Body rule (Ore)", df[df["body"]]), ("Old range rule", df), ("Wick-only closes (removed)", df[~df["body"]])):
        rows.append({"rule": name, "group": "all", **stats(sub)})
        for (pair, tf), g in sub.groupby(["pair", "tf"]):
            rows.append({"rule": name, "group": f"{pair} {tf}", **stats(g)})
    t = pd.DataFrame(rows)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 20)
    print(t.round(2).to_string(index=False))
    t.to_csv(ROOT / "backtest" / "out" / "premise_v12_summary.csv", index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

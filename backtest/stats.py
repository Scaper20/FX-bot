"""Turn trades_<period>.csv into variant statistics.

A "variant" = pair + range TF + entry TF + sweep candle (k) + trigger + entry +
stop + management + expiry + one confluence filter. The filter list is fixed
here, before results are seen; it is not tuned.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

KEYS = ["pair", "range_tf", "entry_tf", "k", "trigger", "entry_type", "stop_type", "mgmt", "expiry"]
CONFLUENCES = ["has_fvg", "has_ob", "kz", "htf_fvg", "htf_ob", "htf_mss", "mtf_mss", "msnr", "other_trigger"]
FILTERS = ["all"] + CONFLUENCES + ["score>=2", "score>=3", "score>=4"]


def load(path) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False, parse_dates=["exit_time", "fill_time", "decision_time", "range_open"])
    df["kz"] = df["killzone"].fillna("").astype(str).ne("")
    for c in CONFLUENCES:
        df[c] = df[c].astype(bool)
    df["score"] = df[CONFLUENCES].sum(axis=1)
    # expiry 2 = everything; expiry 1 = decision and fill inside the first candle after the sweep
    e2 = df.assign(expiry=2)
    e1 = df[df["min_expiry"] == 1].copy()
    late = (e1["status"] == "filled") & ~e1["filled_by_exp1"].astype(bool)
    e1.loc[late, ["R", "exit_reason"]] = [np.nan, np.nan]
    e1.loc[late, "status"] = "expired"
    e1["expiry"] = 1
    out = pd.concat([e2, e1], ignore_index=True)
    out["trade"] = out["status"].eq("filled") & out["R"].notna()
    return out


def filter_mask(df: pd.DataFrame, f: str) -> pd.Series:
    if f == "all":
        return pd.Series(True, index=df.index)
    if f.startswith("score>="):
        return df["score"] >= int(f.split(">=")[1])
    return df[f]


def variant_table(df: pd.DataFrame) -> pd.DataFrame:
    parts = []
    trades = df[df["trade"]]
    for f in FILTERS:
        t = trades[filter_mask(trades, f)]
        g = t.groupby(KEYS, dropna=False)["R"]
        s = pd.DataFrame({"n": g.size(), "avg_R": g.mean(), "win_rate": g.apply(lambda r: (r > 0).mean()),
                          "total_R": g.sum(), "sd": g.std()}).reset_index()
        s["filter"] = f
        parts.append(s)
    out = pd.concat(parts, ignore_index=True)
    out["t"] = out["avg_R"] / (out["sd"] / np.sqrt(out["n"]))
    return out


def path_stats(r: pd.Series) -> dict:
    """Worst losing run and max drawdown (in R) for trades in exit-time order."""
    r = r.to_numpy()
    worst = cur = 0
    for x in r:
        cur = cur + 1 if x <= 0 else 0
        worst = max(worst, cur)
    eq = np.cumsum(r)
    dd = float((np.maximum.accumulate(np.r_[0, eq])[1:] - eq).max()) if len(r) else 0.0
    return {"worst_losing_run": int(worst), "max_dd_R": round(dd, 1)}


def select(df: pd.DataFrame, row: pd.Series) -> pd.DataFrame:
    m = df["trade"] & filter_mask(df, row["filter"])
    for k in KEYS:
        m &= df[k] == row[k]
    return df[m].sort_values("exit_time")


def main_effects(df: pd.DataFrame, by: str) -> pd.DataFrame:
    t = df[df["trade"] & (df["expiry"] == 2)]
    g = t.groupby(["pair", by])["R"]
    return pd.DataFrame({"n": g.size(), "avg_R": g.mean().round(3), "win%": (g.apply(lambda r: (r > 0).mean()) * 100).round(1)})

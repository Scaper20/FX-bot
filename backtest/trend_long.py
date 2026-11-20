"""Spec v5 (docs/spec-v5-trend.md): weekly and monthly trend following on long daily history.

    python -m backtest.trend_long
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "long"
REPORT = ROOT / "backtest" / "reports" / "trend_long_v5.md"
COST = {"XAUUSD": 0.0005, "XAGUSD": 0.0005}          # FX default 0.0002
WINDOWS = {"all": ("1971-01-01", "2026-12-31"), "1971-2012": ("1971-01-01", "2012-12-31"),
           "2013-2026": ("2013-01-01", "2026-12-31"), "2021-2026": ("2021-01-01", "2026-12-31")}
SIGNALS = ["M12", "M6", "M3", "M1", "SMA10", "W52", "W26", "W13", "W4", "DON"]


def load() -> dict[str, pd.Series]:
    out = {}
    for f in sorted(DATA.glob("*.csv")):
        name = f.name.split("_")[0]
        d = pd.read_csv(f, parse_dates=["date"]).dropna()
        s = d.set_index("date")["close"].astype(float)
        out[name] = s[~s.index.duplicated()].sort_index()
    return out


def period_ends(idx: pd.DatetimeIndex, freq: str) -> pd.DatetimeIndex:
    key = idx.to_period("M" if freq == "M" else "W-FRI")
    s = pd.Series(idx, index=idx)
    return pd.DatetimeIndex(s.groupby(key).last().values)


def signal_series(close: pd.Series, code: str) -> pd.Series:
    """Signal (+1/-1/0) decided at each rebalance date, using closes up to that date only."""
    freq = "M" if code.startswith(("M", "SMA")) else "W"
    ends = period_ends(close.index, freq)
    pc = close.reindex(ends)
    if code == "SMA10":
        sig = np.sign(pc - pc.rolling(10).mean())
    elif code == "DON":
        hi, lo = pc.rolling(26).max().shift(1), pc.rolling(13).min().shift(1)
        lo26, hi13 = pc.rolling(26).min().shift(1), pc.rolling(13).max().shift(1)
        state, vals = 0, []
        for p, h26, l13, l26, h13 in zip(pc, hi, lo, lo26, hi13):
            if state <= 0 and p > h26:
                state = 1
            elif state >= 0 and p < l26:
                state = -1
            elif state == 1 and p < l13:
                state = 0
            elif state == -1 and p > h13:
                state = 0
            vals.append(state)
        sig = pd.Series(vals, index=pc.index, dtype=float)
    else:
        n = int(code[1:])
        sig = np.sign(pc / pc.shift(n) - 1)
    return sig.fillna(0)


def market_returns(close: pd.Series, code: str, cost: float) -> pd.Series:
    r = close.pct_change()
    vol = r.rolling(60).std() * np.sqrt(252)
    size = (0.10 / vol).clip(upper=3.0)
    sig = signal_series(close, code)
    pos_at = (sig * size.reindex(sig.index)).dropna()
    pos = pos_at.reindex(close.index).ffill().shift(1)     # trade from the day after the decision
    gross = pos * r
    turnover = pos.diff().abs().fillna(0)
    return (gross - turnover * cost).dropna()


def stats(x: pd.Series) -> dict:
    if len(x) < 60:
        return {"sharpe": np.nan, "ret": np.nan, "maxdd": np.nan, "pos_years": np.nan, "years": 0}
    ann, vol = x.mean() * 252, x.std() * np.sqrt(252)
    eq = x.cumsum()
    yr = x.groupby(x.index.year).sum()
    return {"sharpe": ann / vol if vol > 0 else np.nan, "ret": ann, "maxdd": (eq.cummax() - eq).max(),
            "pos_years": (yr > 0).mean(), "years": len(yr)}


def main() -> int:
    data = load()
    rows, per_market = [], {}
    for code in SIGNALS:
        rets = {m: market_returns(s, code, COST.get(m, 0.0002)) for m, s in data.items()}
        port = pd.DataFrame(rets).mean(axis=1, skipna=True).dropna()
        per_market[code] = rets
        row = {"signal": code}
        for w, (a, b) in WINDOWS.items():
            st = stats(port[a:b])
            row[f"portfolio Sharpe {w}"] = st["sharpe"]
            if w == "2013-2026":
                row["portfolio % years up 2013-26"] = st["pos_years"]
                row["portfolio yearly return 2013-26"] = st["ret"]
                row["portfolio max drawdown 2013-26"] = st["maxdd"]
        for m in ("GBPUSD", "XAUUSD"):
            for w in ("all", "2013-2026", "2021-2026"):
                a, b = WINDOWS[w]
                row[f"{m} Sharpe {w}"] = stats(rets[m][a:b])["sharpe"]
        row["works (spec)"] = bool(row["portfolio Sharpe 2013-2026"] > 0.3 and row["portfolio % years up 2013-26"] >= 0.6)
        rows.append(row)
    t = pd.DataFrame(rows)
    pd.set_option("display.width", 260)
    pd.set_option("display.max_columns", 30)
    print(t.round(2).to_string(index=False))
    t.to_csv(ROOT / "backtest" / "out" / "trend_long.csv", index=False)
    # per-market detail for the best signal after publication
    best = t.sort_values("portfolio Sharpe 2013-2026", ascending=False).iloc[0]["signal"]
    det = pd.DataFrame({m: {w: stats(r[a:b])["sharpe"] for w, (a, b) in WINDOWS.items()}
                        for m, r in per_market[best].items()}).T
    print(f"\nPer market, signal {best} (Sharpe by window):")
    print(det.round(2).to_string())
    det.to_csv(ROOT / "backtest" / "out" / f"trend_long_{best}_markets.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Run the rules on fake prices: real 1-minute returns shuffled in random order.
Same volatility and trading hours, no real market structure.
If the rules find as many setups, with similar results, on noise, they have no edge.

    python -m backtest.noise_check
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.run import run_pair  # noqa: E402
from engine import config as K  # noqa: E402
from engine.candles import clean, load_m1_csv  # noqa: E402


def shuffled(m1: pd.DataFrame, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    c = m1["close"].to_numpy()
    rel = m1[["open", "high", "low"]].to_numpy() / c[:, None]           # candle shape relative to its close
    ret = np.diff(np.log(c))
    perm = rng.permutation(len(ret))
    new_c = c[0] * np.exp(np.r_[0, np.cumsum(ret[perm])])
    shape = rel[np.r_[0, perm + 1]]
    out = pd.DataFrame(shape * new_c[:, None], index=m1.index, columns=["open", "high", "low"])
    out["close"] = new_c
    out["high"] = out[["open", "high", "low", "close"]].max(axis=1)
    out["low"] = out[["open", "high", "low", "close"]].min(axis=1)
    return out[["open", "high", "low", "close"]]


def main() -> int:
    end = pd.Timestamp(K.PERIODS["design"][1], tz="UTC")
    rows = []
    for pair in K.PAIRS:
        m1, _ = clean(load_m1_csv(ROOT / K.PAIRS[pair]["file"]))
        m1 = m1[m1.index < end]
        for label, data in (("real", m1), ("noise", shuffled(m1, seed=7))):
            df, _ = run_pair(pair, "design", m1=data, verbose=False)
            t = df[(df["status"] == "filled") & df["R"].notna()]
            rows.append({"pair": pair, "data": label, "setups": df["decision_time"].nunique(),
                         "trades": len(t), "avg_R": round(t["R"].mean(), 3),
                         "win%": round((t["R"] > 0).mean() * 100, 1)})
    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

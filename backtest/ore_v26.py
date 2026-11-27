"""Spec v26: re-score the live Ore's-model rules with the exact live function (engine.smc_models.ore_poi_setups).

The entry is chosen at decision time (breaker if valid, else order block); an order that never fills is no trade.
(Spec v25's 'nearest' rows dropped unfilled orders first, so they fell back to the order block when the breaker
did not fill: a choice live can't make. This run removes that.)

    python -m backtest.ore_v26        -> backtest/out/v26_trades.csv, printed summary
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.advanced import START, Outcome  # noqa: E402
from backtest.ob_v21 import ohlc, trend_lookup  # noqa: E402
from backtest.patterns import FRESH, MAIN, MARKETS  # noqa: E402
from engine.candles import clean, load_m1_csv, resample  # noqa: E402
from engine.smc_models import ore_poi_setups  # noqa: E402
from engine.smc_poi import first_touch, htf_zones  # noqa: E402
from engine.smc_structure import external_structure  # noqa: E402

OUT = ROOT / "backtest" / "out" / "v26_trades.csv"
TF, MODE, MULT, HOLD = "M15", "wick", 3, "5D"


def run_pair(pair: str) -> list[dict]:
    mk = MARKETS[pair]
    sp = mk["spread"]
    m1, _ = clean(load_m1_csv(ROOT / mk["file"]))
    m1 = m1[m1.index >= START - pd.Timedelta("400D")]
    D, H4, H1, E = (resample(m1, x, "utc0") for x in ("D1", "H4", "H1", TF))
    d1 = trend_lookup(D)
    Z = htf_zones(H4, "H4")
    Z["touch"] = first_touch(Z, H1)
    o, h, l, c = ohlc(E)
    n = len(c)
    Eo, Ec = E.index.as_unit("ns").asi8, pd.DatetimeIndex(E["close_time_utc"]).as_unit("ns").asi8
    oc = Outcome(m1, sp, TF)
    oc.hold = pd.Timedelta(HOLD).value
    rows = []
    for s in ore_poi_setups(o, h, l, c, external_structure(o, h, l, c, MODE), Z, Eo, 900):
        j, d = s["decision"], s["dir"]
        t = int(Ec[j])
        if t < START.value or j + 1 >= n or d1(t) != d:
            continue
        side = "long" if d == 1 else "short"
        e = s["entry"]
        stop = s["far"] + 2 * sp * (-1 if d == 1 else 1)
        tgt = e + d * MULT * abs(e - stop)
        res = oc(side, e, stop, None, tgt, None, (int(Eo[j + 1]), int(Ec[min(j + s["valid"], n - 1)])))
        filled = bool(res) and res["R"] is not None
        rows.append({"pair": pair, "side": side, "variant": s["variant"], "poi": s["htf_poi"]["type"], "t_dec": t,
                     "e": e, "stop": stop,
                     "filled": filled, "R": res["R"] if filled else None, "hit": res["hit_T2"] if filled else None,
                     "chance": res["p_T2"] if filled else None})
    return rows


def summary(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["year"] = pd.to_datetime(d["t_dec"], unit="ns", utc=True).dt.year
    out = []
    for name, g in [("GBP/USD + gold", d[d["pair"].isin(MAIN)]), ("EUR/USD + silver", d[d["pair"].isin(FRESH)])] + \
            [(p, d[d["pair"] == p]) for p in MARKETS]:
        f = g[g["filled"]]
        yrs = f.groupby("year")["R"].mean()
        out.append({"set": name, "setups": len(g), "filled": len(f), "avg_R": round(f["R"].mean(), 3),
                    "total_R": round(f["R"].sum(), 1), "hit": round(f["hit"].mean(), 3),
                    "chance": round(f["chance"].mean(), 3), "years_pos": f"{int((yrs > 0).sum())}/{len(yrs)}",
                    "BB_share": round((f["variant"] == "BB").mean(), 2)})
    return pd.DataFrame(out)


if __name__ == "__main__":
    d = pd.DataFrame([r for p in MARKETS for r in run_pair(p)])
    d.to_csv(OUT, index=False)
    print(summary(d).to_string(index=False))

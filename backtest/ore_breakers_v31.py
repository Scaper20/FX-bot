"""Spec v31 (docs/spec-v31-ore-breakers.md): H4 breakers as POI and breaker-only entry in Ore's model.

    python -m backtest.ore_breakers_v31
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
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

VARIANTS = {"live": (("OB", "FVG"), False), "1: H4 breakers back": (("OB", "FVG", "BB"), False),
            "2: breaker-only entry": (("OB", "FVG"), True), "3: both": (("OB", "FVG", "BB"), True)}


def run_pair(pair: str) -> list[dict]:
    mk = MARKETS[pair]
    sp = mk["spread"]
    m1, _ = clean(load_m1_csv(ROOT / mk["file"]))
    m1 = m1[m1.index >= START - pd.Timedelta("400D")]
    D, H4, H1, E = (resample(m1, x, "utc0") for x in ("D1", "H4", "H1", "M15"))
    d1 = trend_lookup(D)
    Z = htf_zones(H4, "H4")
    Z["touch"] = first_touch(Z, H1)
    o, h, l, c = ohlc(E)
    n = len(c)
    Eo, Ec = E.index.as_unit("ns").asi8, pd.DatetimeIndex(E["close_time_utc"]).as_unit("ns").asi8
    ev = external_structure(o, h, l, c, "wick")
    oc = Outcome(m1, sp, "M15")
    oc.hold = pd.Timedelta("5D").value
    rows = []
    for name, (types, bb_only) in VARIANTS.items():
        for s in ore_poi_setups(o, h, l, c, ev, Z, Eo, 900, types=types):
            j, d = s["decision"], s["dir"]
            t = int(Ec[j])
            if t < START.value or j + 1 >= n or d1(t) != d or (bb_only and s["variant"] != "BB"):
                continue
            side = "long" if d == 1 else "short"
            e = s["entry"]
            stop = s["far"] + 2 * sp * (-1 if d == 1 else 1)
            res = oc(side, e, stop, None, e + d * 3 * abs(e - stop), None,
                     (int(Eo[j + 1]), int(Ec[min(j + s["valid"], n - 1)])))
            if res and res["R"] is not None:
                rows.append({"pair": pair, "variant": name, "poi": s["htf_poi"]["type"], "entry": s["variant"],
                             "t": t, "R": res["R"]})
    print(pair, "done", flush=True)
    return rows


if __name__ == "__main__":
    with Pool(4) as pool:
        d = pd.DataFrame([r for rows in pool.map(run_pair, list(MARKETS)) for r in rows])
    d.to_csv(ROOT / "backtest" / "out" / "v31_trades.csv", index=False)
    out = []
    for set_name, pairs in (("A: GBP/USD + gold", MAIN), ("B: EUR/USD + silver", FRESH)):
        g = d[d.pair.isin(pairs)]
        for v in VARIANTS:
            x = g[g.variant == v]
            out.append({"set": set_name, "variant": v, "trades": len(x), "avg_R": round(x.R.mean(), 3),
                        "total_R": round(x.R.sum(), 1), "win": round((x.R > 0).mean(), 3),
                        "H4 BB POI trades": int((x.poi == "BB").sum())})
    r = pd.DataFrame(out)
    print(r.to_string(index=False))
    for v in list(VARIANTS)[1:]:
        ok = True
        for set_name in ("A: GBP/USD + gold", "B: EUR/USD + silver"):
            q = r[r.set == set_name].set_index("variant")
            ok &= (q.loc[v, "trades"] >= 20 and q.loc[v, "avg_R"] > 0
                   and q.loc[v, "avg_R"] >= q.loc["live", "avg_R"] + 0.10 and q.loc[v, "total_R"] >= q.loc["live", "total_R"])
        print(v, "PASS" if ok else "FAIL")

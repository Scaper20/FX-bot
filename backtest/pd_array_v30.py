"""Spec v30 (docs/spec-v30-pd-array.md): Ore's PD array priority order inside Ore's model and IRL/ERL.

    python -m backtest.pd_array_v30 PAIR     -> backtest/out/v30_PAIR.csv
    python -m backtest.pd_array_v30          -> results table (+ appends nothing; see the spec for the record)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.advanced import START, Outcome  # noqa: E402
from backtest.ob_v21 import ohlc, trend_lookup  # noqa: E402
from backtest.patterns import FRESH, MAIN, MARKETS  # noqa: E402
from engine.candles import clean, load_m1_csv, resample  # noqa: E402
from engine.smc_models import orderblock_setups, ore_reversal_setups  # noqa: E402
from engine.smc_poi import first_touch, htf_zones, tapped_zone  # noqa: E402
from engine.smc_structure import dealing_range, external_structure, irl_erl_bias  # noqa: E402

OUT = ROOT / "backtest" / "out"
ORDER = ("RB", "OB", "FVG", "BB")


def lookup(F, arr):
    close = pd.DatetimeIndex(F["close_time_utc"]).as_unit("ns").asi8
    return lambda t: arr[max(0, int(np.searchsorted(close, t, side="right")) - 1)]


def atr14(h, l, c):
    pc = np.r_[c[0], c[:-1]]
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    return pd.Series(tr).rolling(14, min_periods=14).mean().to_numpy()


def zones_for(o, h, l, c, atr, p, j, d):
    """Rejection block at the extreme candle p and the first FVG of the move p..j (sell: bearish), with the move's
    extreme as the far side. Returns {name: (entry, far)}."""
    out = {}
    ext = h[p] if d == -1 else l[p]
    body_top, body_bot = max(o[p], c[p]), min(o[p], c[p])
    rng = h[p] - l[p]
    wick = (h[p] - body_top) if d == -1 else (body_bot - l[p])
    if rng > 0 and not np.isnan(atr[p]) and wick >= 0.5 * rng and wick >= 0.5 * atr[p]:
        out["RB"] = (body_top if d == -1 else body_bot, ext)
    for k in range(p, j - 1):
        if d == -1 and h[k + 2] < l[k]:
            out["FVG"] = (h[k + 2], max(ext, l[k]))
            break
        if d == 1 and l[k + 2] > h[k]:
            out["FVG"] = (l[k + 2], min(ext, h[k]))
            break
    return out


def run_pair(pair: str) -> pd.DataFrame:
    mk = MARKETS[pair]
    sp = mk["spread"]
    m1, _ = clean(load_m1_csv(ROOT / mk["file"]))
    m1 = m1[m1.index >= START - pd.Timedelta("400D")]
    D, H4, H1, M15 = (resample(m1, x, "utc0") for x in ("D1", "H4", "H1", "M15"))
    d1 = trend_lookup(D)
    h4o, h4h, h4l, h4c = ohlc(H4)
    ie = lookup(H4, irl_erl_bias(h4o, h4h, h4l, h4c)[0])
    rhi, rlo = dealing_range(h4o, h4h, h4l, h4c, "close")
    rng_hi, rng_lo = lookup(H4, rhi), lookup(H4, rlo)
    Z = htf_zones(H4, "H4")
    Z["touch"] = first_touch(Z, H1)
    rows = []
    for strat, E, mode, valid in (("ore_poi", M15, "wick", 30), ("irl_erl", H1, "close", 12)):
        o, h, l, c = ohlc(E)
        n = len(c)
        Eo, Ec = E.index.as_unit("ns").asi8, pd.DatetimeIndex(E["close_time_utc"]).as_unit("ns").asi8
        atr = atr14(h, l, c)
        ev = external_structure(o, h, l, c, mode)
        oc = Outcome(m1, sp, strat == "ore_poi" and "M15" or "H1")
        oc.hold = pd.Timedelta("5D").value
        groups = {}
        if strat == "ore_poi":
            for s in ore_reversal_setups(o, h, l, c, ev):
                j, d, top = s["decision"], s["dir"], s["top"]
                if j - top > 30:
                    continue
                px = h[top] if d == -1 else l[top]
                if tapped_zone(Z, d, int(Eo[top]), float(px), 20 * 900 * 10**9) is None:
                    continue
                g = groups.setdefault((j, d), {"p": top, "liq": s["liq_px"], "zones": {}})
                g["zones"][s["variant"]] = (s["entry"], s["far"])
        else:
            for s in orderblock_setups(o, h, l, c, ev):
                j, d = s["decision"], s["dir"]
                t = int(Ec[j])
                if ie(t) != d:
                    continue
                groups[(j, d)] = {"p": s["origin"], "liq": None, "zones": {"OB": (s["entry"], s["far"])}}
        for (j, d), g in groups.items():
            t = int(Ec[j])
            if t < START.value or j + 1 >= n or d1(t) != d:
                continue
            g["zones"].update(zones_for(o, h, l, c, atr, g["p"], j, d))
            ok = {}
            for name, (e, far) in g["zones"].items():
                ahead = e > c[j] if d == -1 else e < c[j]
                right = far > e if d == -1 else far < e
                beyond = g["liq"] is None or (e > g["liq"] if d == -1 else e < g["liq"])
                if ahead and right and beyond:
                    ok[name] = (float(e), float(far))
            if not ok:
                continue
            live = ("BB" if "BB" in ok else "OB" if "OB" in ok else None) if strat == "ore_poi" else ("OB" if "OB" in ok else None)
            pd_pick = next((z for z in ORDER if z in ok), None)
            mid = (rng_hi(t) + rng_lo(t)) / 2
            side = "long" if d == 1 else "short"
            for name, (e, far) in ok.items():
                stop = far + 2 * sp * (-1 if d == 1 else 1)
                tgt = e + d * 3 * abs(e - stop)
                res = oc(side, e, stop, None, tgt, None, (int(Eo[j + 1]), int(Ec[min(j + valid, n - 1)])))
                filled = bool(res) and res["R"] is not None
                rows.append({"pair": pair, "strategy": strat, "t_dec": t, "side": side, "zone": name,
                             "is_live": name == live, "is_pd": name == pd_pick,
                             "premium": bool((e > mid) if d == -1 else (e < mid)) if not np.isnan(mid) else False,
                             "e": e, "filled": filled, "R": res["R"] if filled else np.nan})
        print(pair, strat, len(groups), "setups", flush=True)
    return pd.DataFrame(rows)


def report() -> pd.DataFrame:
    d = pd.concat([pd.read_csv(OUT / f"v30_{p}.csv") for p in MARKETS], ignore_index=True)
    d = d[d.filled]
    out = []
    for strat in ("ore_poi", "irl_erl"):
        for set_name, pairs in (("A: GBP/USD + gold", MAIN), ("B: EUR/USD + silver", FRESH)):
            g = d[(d.strategy == strat) & d.pair.isin(pairs)]
            rows = {"live": g[g.is_live], "PD priority": g[g.is_pd], "PD + premium/discount": g[g.is_pd & g.premium]}
            for z in ORDER:
                rows[f"{z} only"] = g[g.zone == z]
            for name, x in rows.items():
                out.append({"strategy": strat, "set": set_name, "variant": name, "trades": len(x),
                            "avg_R": round(x.R.mean(), 3) if len(x) else np.nan,
                            "total_R": round(x.R.sum(), 1), "win": round((x.R > 0).mean(), 3) if len(x) else np.nan})
    r = pd.DataFrame(out)
    verdict = []
    for strat in ("ore_poi", "irl_erl"):
        ok = True
        for set_name in ("A: GBP/USD + gold", "B: EUR/USD + silver"):
            q = r[(r.strategy == strat) & (r.set == set_name)].set_index("variant")
            pdr, live = q.loc["PD priority"], q.loc["live"]
            ok &= pdr.trades >= 20 and pdr.avg_R > 0 and pdr.avg_R >= live.avg_R + 0.10
        verdict.append((strat, "PASS" if ok else "FAIL"))
    print(r.to_string(index=False))
    print("\nverdict:", verdict)
    return r


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_pair(sys.argv[1]).to_csv(OUT / f"v30_{sys.argv[1]}.csv", index=False)
    else:
        report()

"""Zone trainer data (Ore's request, 27 Nov 2026): order blocks and breaker blocks from real charts, shown at the
moment price first comes back to them, so Ore can label them before seeing what happened.

    python scripts/build_zone_training.py      -> web/data/zone_training.json.gz

Zone kinds:
- ob_ore:   Ore's order block (2-candle engulfing or candle + pin bar + engulfing) at the top/bottom of a BOS or MSS
- ob_run:   the draft order block (last run of opposite candles at the top/bottom), for contrast
- breaker:  an ob_ore that price later closed through (failed); traded in the direction of the break
Each item: candles up to the candle before the first return (shown), candles after (revealed only after a label),
the zone box, the BOS/MSS line, features for the analysis, and the outcome of a limit at the zone's near edge,
stop beyond its far edge + 2 spreads, at 1R / 2R / 3R. Nothing in the shown part uses later candles.
"""
from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.advanced import Outcome  # noqa: E402
from engine import config as K  # noqa: E402
from engine.candles import clean, load_m1_csv, resample  # noqa: E402
from engine.smc_structure import external_structure, ore_order_block, order_block  # noqa: E402

OUT = ROOT / "web" / "data" / "zone_training.json.gz"
START = pd.Timestamp("2022-01-01", tz="UTC")
HOLD = {"H1": "5D", "H4": "15D"}
RETURN_WITHIN = 40          # candles: the zone must be revisited within this many candles
BEFORE, AFTER = 40, 40      # candles shown before the zone / revealed after the return
QUOTA = {"ob_ore": 150, "ob_run": 75, "breaker": 75}


def ohlc(F):
    return tuple(F[k].to_numpy(float) for k in ("open", "high", "low", "close"))


def trend_fn(F):
    ev = external_structure(*ohlc(F), "close")
    cl = pd.DatetimeIndex(F["close_time_utc"]).as_unit("ns").asi8
    ts = np.array([cl[e["j"]] for e in ev], dtype=np.int64)
    dirs = np.array([e["dir"] for e in ev])
    return lambda t: int(dirs[np.searchsorted(ts, t, side="right") - 1]) if np.searchsorted(ts, t, side="right") else 0


def first_return(h, l, c, start, near, d, n):
    """First candle >= start whose range reaches the zone's near edge; None if no return within RETURN_WITHIN.
    The caller starts 3 candles after the zone was made, so price has left it before it counts as a return."""
    for k in range(start, min(start + RETURN_WITHIN, n)):
        if (d == -1 and h[k] >= near) or (d == 1 and l[k] <= near):
            return k
    return None


def candles(E, a, b):
    w = E.iloc[a:b]
    return [[t.isoformat(), round(float(r.open), 5), round(float(r.high), 5), round(float(r.low), 5),
             round(float(r.close), 5)] for t, r in zip(w.index, w.itertuples())]


def build_pair(pair: str, rng) -> list[dict]:
    sp = K.PAIRS[pair]["spread"]
    m1, _ = clean(load_m1_csv(ROOT / K.PAIRS[pair]["file"]))
    m1 = m1[m1.index >= START - pd.Timedelta("400D")]
    d1, h4 = trend_fn(resample(m1, "D1", "utc0")), trend_fn(resample(m1, "H4", "utc0"))
    items = []
    for tf in ("H1", "H4"):
        E = resample(m1, tf, "utc0")
        o, h, l, c = ohlc(E)
        n = len(c)
        Eo, Ec = E.index.as_unit("ns").asi8, pd.DatetimeIndex(E["close_time_utc"]).as_unit("ns").asi8
        A = pd.Series(np.maximum(h - l, 0)).rolling(14).mean().to_numpy()
        res = {r: Outcome(m1, sp, tf) for r in (1, 2, 3)}
        for oc in res.values():
            oc.hold = pd.Timedelta(HOLD[tf]).value
        events = external_structure(o, h, l, c, "close")
        for ev in events:
            j, d, p = ev["j"], ev["dir"], ev["protected"]
            if Ec[j] < START.value or j + 2 >= n or np.isnan(A[j]):
                continue
            zones = []
            ob = ore_order_block(o, h, l, c, p, d, ahead=min(2, j - p))
            if ob:
                zones.append(("ob_ore", ob["first"], ob["last"], ob["near"], ob["far"], ob["kind"], d, j))
                # breaker: price later CLOSES through the far side of this block -> trade the other way on return
                for k in range(j + 1, min(j + 120, n)):
                    if (d == -1 and c[k] > ob["far"]) or (d == 1 and c[k] < ob["far"]):
                        # for the breaker the "near" edge is the old far edge, traded from the other side
                        zones.append(("breaker", ob["first"], ob["last"], ob["far"], ob["near"], ob["kind"], -d, k))
                        break
            run = order_block(o, h, l, c, p, d)
            if run:
                near = run["body_edge"]
                far = run["high"] if d == -1 else run["low"]
                zones.append(("ob_run", run["first"], run["last"], near, far, "run", d, j))
            for kind, f0, last, near, far, shape, td, made in zones:
                if (td == -1 and not far > near) or (td == 1 and not far < near):
                    continue
                if (td == -1 and c[made] >= near) or (td == 1 and c[made] <= near):
                    continue                                   # price must be away from the zone when it is made
                k = first_return(h, l, c, made + 3, near, td, n)      # price must leave the zone first
                if k is None or k - f0 > 160:
                    continue
                stop = far + 2 * sp * (1 if td == -1 else -1)
                risk = abs(stop - near)
                win = (int(Eo[k]), int(Ec[k]))
                side = "short" if td == -1 else "long"
                out = {}
                for r, oc in res.items():
                    x = oc(side, near, stop, None, near + td * r * risk, None, win)
                    out[f"R{r}"] = None if not x or x["R"] is None else round(float(x["R"]), 3)
                if out["R1"] is None:
                    continue
                prior = h[max(0, f0 - 20):f0] if td == -1 else l[max(0, f0 - 20):f0]
                ext = h[f0:last + 1].max() if td == -1 else l[f0:last + 1].min()
                took_liq = bool(len(prior) and ((td == -1 and ext > prior.max()) or (td == 1 and ext < prior.min())))
                fvg = any((td == -1 and h[x + 2] < l[x]) or (td == 1 and l[x + 2] > h[x]) for x in range(last, made - 1))
                lo_w = max(0, min(f0 - 10, max(f0 - BEFORE, k - 70)))      # ~70 candles, zone start always shown
                hi_w = min(n, k + AFTER)
                items.append({
                    "kind": kind, "shape": shape, "pair": pair, "tf": tf, "direction": side,
                    "event": ev["kind"] if kind != "breaker" else "failed " + ("sell" if td == 1 else "buy") + " block",
                    "zone": {"start": E.index[f0].isoformat(), "end": E.index[last].isoformat(),
                             "near": round(near, 5), "far": round(far, 5)},
                    "line": {"start": E.index[ev["broken"]].isoformat(), "end": E.index[j].isoformat(),
                             "price": round(ev["level"], 5), "label": ev["kind"]},
                    "made": E.index[made].isoformat(), "touch": E.index[k].isoformat(),
                    "entry": round(near, 5), "stop": round(stop, 5),
                    "targets": {f"R{r}": round(near + td * r * risk, 5) for r in (1, 2, 3)},
                    "outcome": out,
                    "features": {"with_htf": bool(d1(int(Ec[k - 1])) == td and h4(int(Ec[k - 1])) == td),
                                 "took_liquidity": took_liq, "left_fvg": bool(fvg),
                                 "size_atr": round(float(abs(far - near) / A[j]), 2),
                                 "candles_to_return": int(k - made), "shape": shape},
                    "candles": candles(E, lo_w, k), "after": candles(E, k, hi_w),
                })
    return items


def main() -> int:
    rng = np.random.default_rng(27)
    allitems = []
    for pair in K.PAIRS:
        allitems += build_pair(pair, rng)
        print(pair, len(allitems), flush=True)
    df = pd.DataFrame({"i": range(len(allitems)), "kind": [x["kind"] for x in allitems]})
    chosen = []
    for kind, q in QUOTA.items():
        idx = df.loc[df["kind"] == kind, "i"].to_numpy()
        chosen += list(rng.choice(idx, min(q, len(idx)), replace=False))
    rng.shuffle(chosen)
    out = []
    for n_, i in enumerate(chosen):
        it = allitems[int(i)]
        it["id"] = f"Z{n_ + 1:03d}"
        out.append(it)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUT, "wt") as fh:
        json.dump(out, fh, separators=(",", ":"))
    kinds = pd.Series([x["kind"] for x in out]).value_counts().to_dict()
    print(f"{len(out)} zones -> {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1e6:.1f} MB) {kinds}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

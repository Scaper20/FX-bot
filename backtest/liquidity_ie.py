"""Spec v14 (docs/spec-v14-liquidity.md): Inter Equity's liquidity + inducement strategy.

Model 1 = the 4-candle "sniper" entry, Model 2 = induce -> trap -> trade with a liquidity-block stop.
Each alone (pure) and inside a CRT's Candle-3 window (paired). Bearish logic throughout; buys run the
same code on mirrored prices (backtest.romeo.arrays).

    python -m backtest.liquidity_ie
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
from engine.structure import crt_inside  # noqa: E402

OUT = ROOT / "backtest" / "out"
NY = "America/New_York"
FRAC = 2              # 5-bar fractal
LOOK = 300            # candles searched back for liquidity blocks and targets
WIN_CORE = 20         # candles a Model-2 order stays valid
HOLD_N = 20           # time stop, in candles of the setup timeframe
MIN_RR = K.MIN_RR
TF_SEC = {"M5": 300, "M15": 900, "H1": 3600, "H4": 14400, "D1": 86400}
SNIPER_TFS = ("D1", "H4", "H1", "M15", "M5")
CORE_TFS = ("H4", "H1", "M15", "M5")


# ------------------------------------------------------------------ helpers

def swing_flags(h: np.ndarray, l: np.ndarray):
    """5-bar fractal swings (strict). A swing at k is only known once candle k+2 has closed."""
    n = len(h)
    sh = np.zeros(n, bool)
    sl = np.zeros(n, bool)
    if n > 4:
        m = slice(2, n - 2)
        sh[m] = (h[2:-2] > h[1:-3]) & (h[2:-2] > h[:-4]) & (h[2:-2] > h[3:-1]) & (h[2:-2] > h[4:])
        sl[m] = (l[2:-2] < l[1:-3]) & (l[2:-2] < l[:-4]) & (l[2:-2] < l[3:-1]) & (l[2:-2] < l[4:])
    return sh, sl


def rr(e: float, t: float, stop: float, sp: float) -> float:
    """Reward:risk after spread, bearish space (entry above target, stop above entry)."""
    return (e - t - sp) / (stop - e + sp)


def intact_lows(l: np.ndarray, sl_idx: np.ndarray, now: int, below: float) -> list[tuple[float, int]]:
    """Swing lows confirmed by candle `now`, below `below`, not traded through since; nearest first."""
    out = []
    lo = now - LOOK
    for k in sl_idx[::-1]:
        if k < lo:
            break
        if k > now - FRAC or l[k] >= below:
            continue
        if l[k + 1:now + 1].min() > l[k]:
            out.append((float(l[k]), int(k)))
    out.sort(key=lambda x: -x[0])
    return out


def pick_targets(e, stop, sp, lows):
    """Final target = first level giving 1:3; TP1 = nearest level if it's nearer than the final one."""
    final = next(((t, k) for t, k in lows[:3] if rr(e, t, stop, sp) >= MIN_RR), None)
    if final is None:
        return None, None
    tp1 = lows[0] if lows and lows[0][0] > final[0] else None
    return final, tp1


# ------------------------------------------------------------------ Model 1: sniper (bearish = sell)

def sniper_orders(o, h, l, c, Eo_t, Ec_t, sp):
    sh, sl = swing_flags(h, l)
    sl_idx = np.flatnonzero(sl)
    out = []
    for c3 in range(LOOK, len(h) - 1):
        c1, c2, c4 = c3 - 2, c3 - 1, c3 + 1
        if not (h[c2] > h[c1] and c[c2] < h[c1] and h[c3] < h[c2] and c[c3] < o[c3]):
            continue
        stop = h[c2] + 2 * sp
        for entry_kind, e in (("edge", h[c3]), ("mid", (h[c3] + h[c2]) / 2)):
            final, tp1 = pick_targets(e, stop, sp, intact_lows(l, sl_idx, c3, e))
            if final is None:
                continue
            out.append({"model": "sniper", "entry_kind": entry_kind, "e": e, "stop": stop,
                        "target": final[0], "target_idx": final[1], "tp1": tp1[0] if tp1 else None,
                        "place": c3, "window": (int(Eo_t[c4]), int(Ec_t[c4])),
                        "idx": {"c1": c1, "c2": c2, "c3": c3, "c4": c4}})
    return out


# ------------------------------------------------------------------ Model 2: induce -> trap (bearish = sell)

def core_orders(o, h, l, c, Eo_t, Ec_t, sp):
    sh, sl = swing_flags(h, l)
    n = len(h)
    sh_list, sl_list = [], []
    last_sl = None                    # (price, idx) latest confirmed swing low
    induced, leg_low, leg_idx, broken = False, None, None, None
    out = []
    for j in range(FRAC * 2, n - 1):
        k = j - FRAC                  # swing at k is known now
        if sh[k]:
            sh_list.append(k)
        if sl[k]:
            sl_list.append(k)
            last_sl = (l[k], k)
        if not induced:
            if last_sl is not None and l[j] < last_sl[0]:
                induced, leg_low, leg_idx, broken = True, l[j], j, last_sl[1]     # sellers induced
            continue
        if l[j] < leg_low:            # the leg extends: wait for a new pullback high after the new low
            leg_low, leg_idx = l[j], j
            continue
        if not (sh[k] and k > leg_idx):
            continue
        e, hr = h[k], k               # retail sell high: sell when it's taken (sellers trapped)
        induced = False
        lb = next((s for s in reversed(sh_list) if s < hr and s >= j - LOOK and h[s] > e), None)
        if lb is None:
            continue                  # no liquidity block, no trade
        stop = h[lb] + 2 * sp
        lows = [(float(leg_low), int(leg_idx))] + [
            x for x in intact_lows(l, np.array(sl_list, int), j, leg_low) if x[1] < leg_idx]
        final, tp1 = pick_targets(e, stop, sp, lows)
        if final is None:
            continue
        end = min(j + WIN_CORE, n - 1)
        brk = np.flatnonzero(l[j + 1:end + 1] < leg_low)
        last = j + brk[0] if len(brk) else end          # stop the window before the leg low breaks
        if last < j + 1:
            continue
        out.append({"model": "core", "entry_kind": "trap", "e": e, "stop": stop, "target": final[0],
                    "target_idx": final[1], "tp1": tp1[0] if tp1 else None, "place": j,
                    "window": (int(Eo_t[j + 1]), int(Ec_t[last])),
                    "idx": {"broken_low": int(broken), "leg_low": int(leg_idx), "retail_high": int(hr),
                            "lb": int(lb), "place": int(j)}})
    return out


# ------------------------------------------------------------------ CRTs (Ore's body rule, Exness candles)

def crts(R: pd.DataFrame, mir: bool):
    o, h, l, c = arrays(R, mir)
    t_open = R.index.as_unit("ns").asi8
    t_close = pd.DatetimeIndex(R["close_time_utc"]).as_unit("ns").asi8
    for i in range(20, len(R) - 3):
        if t_open[i] < START.value or h[i] <= l[i]:
            continue
        for k in (1, 2):
            s = i + k
            if k == 2 and (h[i + 1] > h[i] or l[i + 1] < l[i]):
                continue
            if h[s] > h[i] and l[s] >= l[i] and crt_inside(o, h, l, c, i, c[s]):
                yield {"i": i, "s": s, "c2_close": int(t_close[s]), "c3_close": int(t_close[s + 1]),
                       "mid": (h[i] + l[i]) / 2, "far": l[i], "open": int(t_open[i])}


# ------------------------------------------------------------------ run

JOBS = {"slow_tfs": (("D1", "H4", "H1"), ()), "m15": (("M15",), (("D1", "M15"),)), "m5": (("M5",), (("H4", "M5"),))}


def run_pair(pair: str, markets=K.PAIRS, tfs=tuple(TF_SEC), pairings=(("D1", "M15"), ("H4", "M5"))
             ) -> tuple[list[dict], list[dict]]:
    sp = markets[pair]["spread"]
    m1, _ = clean(load_m1_csv(ROOT / markets[pair]["file"]))
    m1 = m1[m1.index >= START - pd.Timedelta("400D")]
    out = Outcome(m1, sp, "H4")
    need = set(tfs) | {"D1"} | {r for r, _ in pairings}
    frames = {tf: resample(m1, tf, "utc0") for tf in need}
    d1 = frames["D1"]
    d1_close = pd.DatetimeIndex(d1["close_time_utc"]).as_unit("ns").asi8
    rows, setups = [], []

    def bias_ok(t_ns, mir):
        j = int(np.searchsorted(d1_close, t_ns, side="right")) - 1
        if j < 1:
            return False
        y, p = d1.iloc[j], d1.iloc[j - 1]
        if mir:                                   # buy: yesterday took the day-before low, not its high
            return bool(y["low"] < p["low"] and y["high"] <= p["high"])
        return bool(y["high"] > p["high"] and y["low"] >= p["low"])

    def score(od, mir, tf, t1, t2, window, hold_ns, tags):
        sg = -1.0 if mir else 1.0
        out.hold = hold_ns
        res = out("long" if mir else "short", sg * od["e"], sg * od["stop"], None if t1 is None else sg * t1,
                  sg * t2, None, window)
        if res:
            rows.append({**tags, "pair": pair, "tf": tf, "direction": "long" if mir else "short", **res})

    by_tf = {}
    for tf in tfs:
        E = frames[tf]
        Eo_t = E.index.as_unit("ns").asi8
        Ec_t = pd.DatetimeIndex(E["close_time_utc"]).as_unit("ns").asi8
        hold = int(HOLD_N * TF_SEC[tf] * 1.4 * 1e9)          # x1.4 so weekends don't cut the trade short
        for mir in (False, True):
            o, h, l, c = arrays(E, mir)
            orders = []
            if tf in SNIPER_TFS:
                orders += sniper_orders(o, h, l, c, Eo_t, Ec_t, sp)
            if tf in CORE_TFS:
                orders += core_orders(o, h, l, c, Eo_t, Ec_t, sp)
            sg = -1.0 if mir else 1.0
            for od in orders:
                place_ns = int(Ec_t[od["place"]])
                if place_ns < START.value:
                    continue
                od.update(pair=pair, tf=tf, mir=mir, place_ns=place_ns)
                ny = pd.Timestamp(place_ns, tz="UTC").tz_convert(NY)
                tags = {"family": "pure", "model": od["model"], "entry_kind": od["entry_kind"],
                        "ny": bool(8 <= ny.hour < 17 and ny.weekday() < 5), "bias": bias_ok(place_ns, mir),
                        "place_ns": place_ns}
                score(od, mir, tf, None, od["target"], od["window"], hold, {**tags, "mgmt": "A"})
                if od["tp1"] is not None:
                    score(od, mir, tf, od["tp1"], od["target"], od["window"], hold, {**tags, "mgmt": "B"})
                setups.append({**{k: v for k, v in od.items() if k not in ("window",)},
                               "window_start": od["window"][0], "window_end": od["window"][1],
                               "e_real": sg * od["e"], "stop_real": sg * od["stop"], "target_real": sg * od["target"],
                               "tp1_real": None if od["tp1"] is None else sg * od["tp1"]})
            by_tf[(tf, mir)] = orders
    # ---- paired with CRT: Candle-3 window, CRT direction, model stop; CRT or liquidity targets
    for rtf, etf in pairings:
        crt_hold = int(pd.Timedelta("3D" if rtf == "D1" else "20h").value)
        liq_hold = int(HOLD_N * TF_SEC[etf] * 1.4 * 1e9)
        for mir in (False, True):
            orders = sorted(by_tf[(etf, mir)], key=lambda x: x["place_ns"] if "place_ns" in x else 0)
            places = np.array([x.get("place_ns", 0) for x in orders])
            for cr in crts(frames[rtf], mir):
                a = int(np.searchsorted(places, cr["c2_close"], side="left"))
                b = int(np.searchsorted(places, cr["c3_close"], side="left"))
                seen = set()
                for od in orders[a:b]:
                    key = (od["model"], od["entry_kind"])
                    if key in seen or od["entry_kind"] == "mid":
                        continue
                    seen.add(key)
                    w = (od["window"][0], min(od["window"][1], cr["c3_close"]))
                    if w[1] <= w[0]:
                        continue
                    tags = {"family": "crt", "model": od["model"], "entry_kind": od["entry_kind"], "ny": False,
                            "bias": False, "place_ns": od["place_ns"], "crt_tf": rtf}
                    far, mid = cr["far"], cr["mid"]
                    if od["e"] > far and rr(od["e"], far, od["stop"], sp) >= MIN_RR:
                        score(od, mir, etf, mid if far < mid < od["e"] else None, far, w, crt_hold,
                              {**tags, "mgmt": "CRT targets"})
                    score(od, mir, etf, None, od["target"], w, liq_hold, {**tags, "mgmt": "A"})
                    if od["tp1"] is not None:
                        score(od, mir, etf, od["tp1"], od["target"], w, liq_hold, {**tags, "mgmt": "B"})
    return rows, setups


def main() -> int:
    """No args: merge the parts. With PAIR JOB: run one part (pairs x JOBS run in parallel)."""
    import sys as _s
    if len(_s.argv) == 3:
        pair, job = _s.argv[1], _s.argv[2]
        tfs, pairings = JOBS[job]
        r, st = run_pair(pair, tfs=tfs, pairings=pairings)
        pd.DataFrame(r).to_csv(OUT / f"liq_part_{pair}_{job}.csv", index=False)
        pd.to_pickle(st, OUT / f"liq_part_{pair}_{job}.pkl")
        print(pair, job, len(r), "trades scored,", len(st), "setups", flush=True)
        return 0
    rows = pd.concat([pd.read_csv(OUT / f"liq_part_{p}_{j}.csv") for p in K.PAIRS for j in JOBS], ignore_index=True)
    setups = [x for p in K.PAIRS for j in JOBS for x in pd.read_pickle(OUT / f"liq_part_{p}_{j}.pkl")]
    rows.to_csv(OUT / "liquidity_ie_trades.csv", index=False)
    pd.to_pickle(setups, OUT / "liquidity_ie_setups.pkl")
    print(len(rows), "trades scored,", len(setups), "setups")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Find CRT setups and turn them into orders. The ONLY place the rules live.

Bearish logic throughout; bullish setups use mirrored prices (structure.mirror).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import config as K
from . import structure as S
from .calendar import next_closes
from .candles import resample, resample_from, with_close_times
from .sessions import friday_late, in_killzone, session_flags
from .simulate import simulate


@dataclass
class TF:
    """One timeframe in one orientation (normal or mirrored)."""
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    t_open: np.ndarray   # int64 ns UTC
    t_close: np.ndarray  # int64 ns UTC
    m1_count: np.ndarray


def _tf(df: pd.DataFrame, mirrored: bool) -> TF:
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    if mirrored:
        o, h, l, c = S.mirror(o, h, l, c)
    return TF(o, h, l, c,
              df.index.as_unit("ns").asi8.copy(),
              pd.DatetimeIndex(df["close_time_utc"]).as_unit("ns").asi8.copy(),
              df["m1_count"].to_numpy())


class Market:
    """All timeframes for one pair. Backtest: built from 1-minute candles that end before
    `data_end`. Live: Market.from_frames() with H1, M15, M5 candles and the current time."""

    TFS = ("M5", "M15", "H1", "H4", "D1")
    live = False
    now_ns = None

    def __init__(self, m1: pd.DataFrame | None, data_end: pd.Timestamp | None = None,
                 day_close: str = K.DAY_CLOSE, frames: dict | None = None):
        if frames is None:
            m1 = m1[m1.index < data_end]
            self.last_time = m1.index[-1] + pd.Timedelta("1min")
            frames = {"M1": m1.assign(m1_count=1, close_time_utc=m1.index + pd.Timedelta("1min"))}
            for tf in self.TFS:
                df = resample(m1, tf, day_close)
                frames[tf] = df[df["close_time_utc"] <= self.last_time]   # complete candles only
        self.day_close = day_close
        self.frames = frames
        self.view = {(tf, mir): _tf(df, mir) for tf, df in frames.items() for mir in (False, True)}
        d1 = frames["D1"]
        prev_c = d1["close"].shift()
        tr = np.maximum(d1["high"] - d1["low"],
                        np.maximum((d1["high"] - prev_c).abs(), (d1["low"] - prev_c).abs()))
        self.d1_atr = tr.rolling(14).mean().to_numpy()     # ATR of candle i, known at its close
        self.atr = {tf: _atr(frames[tf]) for tf in self.TFS}
        # Daily "market direction", real orientation: +1 up, -1 down, 0 unknown. Known at each D1 close.
        self.d1_struct = S.structure_direction(d1["high"].to_numpy(), d1["low"].to_numpy(),
                                               d1["close"].to_numpy(), K.SWING_N)
        ema = d1["close"].ewm(span=20, adjust=False).mean()
        up = (d1["close"] > ema) & (ema > ema.shift(3))
        dn = (d1["close"] < ema) & (ema < ema.shift(3))
        self.d1_ema = np.where(up, 1, np.where(dn, -1, 0))


    @classmethod
    def from_frames(cls, base: dict, now: pd.Timestamp, day_close: str = K.DAY_CLOSE) -> "Market":
        """Live market from H1, M15 and M5 candles (indexed by open time, UTC). Only candles
        that had closed at `now` are kept; H4 and D1 are built from H1."""
        frames = {}
        for tf in ("M5", "M15", "H1"):
            df = with_close_times(base[tf][["open", "high", "low", "close"]], tf, day_close)
            frames[tf] = df[df["close_time_utc"] <= now]
        for tf in ("H4", "D1"):
            df = resample_from(frames["H1"], tf, day_close)
            frames[tf] = df[df["close_time_utc"] <= now]
        mkt = cls(None, frames=frames, day_close=day_close)
        mkt.live = True
        mkt.now_ns = int(now.value)
        mkt.last_time = now
        return mkt


def _atr(df: pd.DataFrame, n: int = 14) -> np.ndarray:
    prev_c = df["close"].shift()
    tr = np.maximum(df["high"] - df["low"],
                    np.maximum((df["high"] - prev_c).abs(), (df["low"] - prev_c).abs()))
    return tr.rolling(n).mean().to_numpy()


def _idx_closed_by(tf: TF, t_ns: int) -> int:
    """Index of the last candle whose close time <= t_ns (-1 if none)."""
    return int(np.searchsorted(tf.t_close, t_ns, side="right")) - 1


def window_ends(mkt: Market, range_tf: str, R: TF, s: int) -> dict:
    """Close times of the 1st and 2nd range candles after the sweep candle: the setup
    expires at the second. Real candles when they exist; live, projected by the calendar."""
    have = [int(R.t_close[j]) for j in (s + 1, s + 2) if j < len(R.t_close)]
    if len(have) < 2:
        last = have[-1] if have else int(R.t_close[s])
        have += next_closes(range_tf, last, 2 - len(have))
    return {1: have[0], 2: have[1]}


def find_orders(mkt: Market, range_tf: str, entry_tf: str, i: int, k: int, mirrored: bool,
                spread: float, info: dict | None = None) -> tuple[list[dict], str]:
    """Evaluate range candle i with sweep candle i+k (k = 1 or 2) in one direction.
    Returns (orders, reason) where reason explains why there are none. Live reasons:
    'waiting' (armed: valid sweep, no trigger yet, window open) and 'invalidated'.
    If `info` is a dict it receives the range/sweep levels for display."""
    R = mkt.view[(range_tf, mirrored)]
    s = i + k
    if s >= len(R.o) or (s + 2 >= len(R.o) and not mkt.live):
        return [], "no_room"
    rh, rl = R.h[i], R.l[i]
    if rh <= rl:
        return [], "flat"
    if k == 2:      # middle candle must stay inside without sweeping either side
        if R.h[i + 1] > rh or R.l[i + 1] < rl:
            return [], "middle_broke"
    if not (R.h[s] > rh and rl < R.c[s] < rh):
        return [], "no_sweep"
    if R.l[s] < rl:
        return [], "both_sides"
    # Sweep candle must be contiguous in time (no multi-day data hole inside)
    sweep_hi = R.h[s]
    t_s_open, t_s_close = R.t_open[s], R.t_close[s]
    end_by_exp = window_ends(mkt, range_tf, R, s)
    if info is not None:
        info.update(range_high=float(rh), range_low=float(rl), sweep_extreme=float(sweep_hi),
                    sweep_close=float(R.c[s]), sweep_open_ns=int(t_s_open), sweep_close_ns=int(t_s_close),
                    window_end_ns=int(end_by_exp[2]))

    E = mkt.view[(entry_tf, mirrored)]
    e0 = int(np.searchsorted(E.t_open, t_s_open, side="left"))
    e_s_last = _idx_closed_by(E, t_s_close)
    e_end = _idx_closed_by(E, end_by_exp[2]) + 1           # exclusive
    if e_s_last < e0:
        return [], "no_entry_data"
    top = e0 + int(np.argmax(E.h[e0:e_s_last + 1]))
    # cancelled if a later candle goes above the sweep high before entry
    inv = S.first_true(E.h[top + 1:e_end] > sweep_hi)
    scan_end = top + 1 + inv if inv >= 0 else e_end

    triggers = {
        "CISD": S.first_cisd(E.o, E.c, top, scan_end),
        "MSS": S.first_mss(E.l, E.c, top, scan_end, K.SWING_N),
    }
    if all(v < 0 for v in triggers.values()):
        if inv >= 0:
            return [], "invalidated"
        if mkt.live and mkt.now_ns < end_by_exp[2]:
            return [], "waiting"
        return [], "no_trigger"

    # ---------- features known at the sweep candle's close (range-TF context)
    feats = _htf_features(mkt, range_tf, mirrored, i, s, top_time=E.t_open[top])
    feats.update(
        k=k,
        close_pos=float((rh - R.c[s]) / (rh - rl)),
        range_small=bool(R.m1_count[i] < 0.5 * (1440 if range_tf == "D1" else 240)),
        range_open=pd.Timestamp(R.t_open[i], tz="UTC"),
    )
    # v1.2: market direction, sweep size (all known at the sweep candle's open/close)
    D = mkt.view[("D1", mirrored)]
    di = _idx_closed_by(D, t_s_open)
    trade_sign = 1 if mirrored else -1            # real direction: +1 long, -1 short
    def rel(d):
        return "none" if d == 0 else ("with" if d == trade_sign else "against")
    atr_r = mkt.atr[range_tf][s - 1]
    feats.update(
        trend_struct=rel(int(mkt.d1_struct[di])) if di >= 0 else "none",
        trend_ema=rel(int(mkt.d1_ema[di])) if di >= 0 else "none",
        sweep_depth_atr=float((R.h[s] - rh) / atr_r) if np.isfinite(atr_r) and atr_r > 0 else np.nan,
        sweep_ratio=float((R.h[s] - R.l[s]) / (rh - rl)),
    )
    targets_base = {"T1": (rh + rl) / 2, "T2": rl, "T3": _t3(R, i, s, rl)}

    orders = []
    for trig_name, ti in triggers.items():
        if ti < 0:
            continue
        decision = max(ti, e_s_last)
        t_dec = int(E.t_close[decision])
        if decision >= scan_end:
            continue
        exp = 1 if t_dec <= end_by_exp[1] else 2
        other = "MSS" if trig_name == "CISD" else "CISD"
        f = dict(feats)
        t_dec_ts = pd.Timestamp(t_dec, tz="UTC")
        f.update(trigger=trig_name, other_trigger=bool(0 <= triggers[other] <= decision),
                 killzone=in_killzone(pd.Timestamp(int(E.t_close[ti]), tz="UTC")),
                 session=session_flags(t_dec_ts), friday_late=friday_late(t_dec_ts),
                 decision_time=pd.Timestamp(t_dec, tz="UTC"), min_expiry=exp,
                 mtf_mss=_mtf_mss(mkt, range_tf, mirrored, E.t_open[top], t_dec))
        fvg = S.latest_open_bear_fvg(E.h, E.l, top, decision)
        ob = S.bear_order_block(E.o, E.h, E.l, E.c, top, decision, K.OB_SEARCH)
        f.update(has_fvg=fvg is not None, has_ob=ob is not None)
        price_now = E.c[decision]
        entries = [("E1", price_now, None, True)]
        if fvg:
            entries += [("E2", fvg["bottom"], fvg["top"], False), ("E3", fvg["mid"], fvg["top"], False)]
        if ob:
            entries += [("E4", ob["open"], ob["high"], False), ("E5", ob["mean"], ob["high"], False)]
        atr_e = mkt.atr[entry_tf][decision]
        atr_e = atr_e if np.isfinite(atr_e) else 0.0
        stops = (("S1", sweep_hi), ("S1p", sweep_hi + 2 * spread), ("S1a", sweep_hi + 0.1 * atr_e))
        for ename, lvl, tight, market in entries:
            if not market and lvl <= price_now:     # already past it: no chasing
                continue
            for sname, stop in stops + (("S2", tight),):
                if stop is None or stop <= lvl:
                    continue
                rr = {t: ((lvl - p - spread) / (stop - lvl + spread) if p is not None else None)
                      for t, p in targets_base.items()}
                if not any(v is not None and v >= K.MIN_RR for v in rr.values()):
                    continue
                orders.append(dict(f, entry_type=ename, stop_type=sname, entry=lvl, stop=stop,
                                   risk_spreads=(stop - lvl) / spread,
                                   market=market, targets=targets_base, rr=rr,
                                   t_dec=t_dec, t_end={1: int(end_by_exp[1]), 2: int(end_by_exp[2])}))
    return orders, ("ok" if orders else "rr_too_small")


def _t3(R: TF, i: int, s: int, rl: float):
    """Nearest swing low below the range low, confirmed by the sweep candle and not yet taken."""
    for t in range(s - K.SWING_N, max(i - K.HTF_LOOKBACK, K.SWING_N) - 1, -1):
        if S.is_swing_low(R.l, t, K.SWING_N) and R.l[t] < rl and R.l[t + 1:s + 1].min() > R.l[t]:
            return float(R.l[t])
    return None


def _htf_features(mkt: Market, range_tf: str, mirrored: bool, i: int, s: int, top_time: int) -> dict:
    R = mkt.view[(range_tf, mirrored)]
    lo, hi = R.h[i], R.h[s]
    fvg, ob = S.htf_zone_overlap(R.o, R.h, R.l, R.c, i, lo, hi, K.HTF_LOOKBACK)
    if range_tf == "H4":            # also check D1 zones that were complete before the sweep began
        D = mkt.view[("D1", mirrored)]
        di = _idx_closed_by(D, R.t_open[s])
        if di > 3:
            f2, o2 = S.htf_zone_overlap(D.o, D.h, D.l, D.c, di, lo, hi, K.HTF_LOOKBACK)
            fvg, ob = fvg or f2, ob or o2
    t = S.last_swing_low(R.l, s - 1, K.SWING_N, K.HTF_LOOKBACK)
    htf_mss = bool(t >= 0 and R.c[s] < R.l[t])
    # MSnR: a fresh A-level between the range high and just above the sweep high
    D = mkt.view[("D1", mirrored)]
    di = _idx_closed_by(D, R.t_open[s])
    atr = mkt.d1_atr[di] if di >= 0 else np.nan
    tol = K.MSNR_TOL_ATR * atr if np.isfinite(atr) else 0.0
    levels = S.fresh_a_levels(R.o, R.h, R.l, R.c, i, K.HTF_LOOKBACK)
    msnr = any(lo - tol <= lv <= hi + tol for lv in levels)
    return {"htf_fvg": bool(fvg), "htf_ob": bool(ob), "htf_mss": htf_mss, "msnr": bool(msnr)}


def _mtf_mss(mkt: Market, range_tf: str, mirrored: bool, top_time: int, t_dec: int) -> bool:
    M = mkt.view[(K.MID_TF[range_tf], mirrored)]
    top = int(np.searchsorted(M.t_open, top_time, side="right")) - 1
    last = _idx_closed_by(M, t_dec)
    if top < 0 or last <= top:
        return False
    return S.first_mss(M.l, M.c, top, last + 1, K.SWING_N) >= 0


def simulate_order(mkt: Market, order: dict, range_tf: str, mirrored: bool, spread: float) -> dict:
    """Run one order on 1-minute candles. Returns the simulate() result plus times."""
    M = mkt.view[("M1", mirrored)]
    start = int(np.searchsorted(M.t_open, order["t_dec"], side="left"))
    pend_end = int(np.searchsorted(M.t_open, order["t_end"][2], side="left"))
    R = mkt.view[(range_tf, mirrored)]

    def hold_end(fill_idx: int) -> int:
        """Time stop after HOLD_RANGE_CANDLES *trading* range candles (weekends don't count)."""
        t0 = M.t_close[fill_idx] if fill_idx >= 0 else order["t_dec"]
        j = int(np.searchsorted(R.t_close, t0, side="left")) + K.HOLD_RANGE_CANDLES - 1
        t_stop = R.t_close[j] if j < len(R.t_close) else M.t_close[-1]
        return int(np.searchsorted(M.t_open, t_stop, side="left"))

    fill_shift, exit_shift = (spread, 0.0) if mirrored else (0.0, spread)
    out = simulate(M.h, M.l, M.c, start, pend_end, hold_end, entry=order["entry"], market=order["market"],
                   stop=order["stop"], targets=order["targets"], t1=order["targets"]["T1"],
                   fill_shift=fill_shift, exit_shift=exit_shift)
    if out["status"] == "filled":
        out["fill_time"] = int(M.t_close[out["fill"]]) if out["fill"] >= 0 else order["t_dec"]
        for r in out["results"].values():
            r["exit_time"] = int(M.t_close[r["exit"]])
    return out


def track_order(mkt: Market, order: dict, range_tf: str, mirrored: bool, spread: float) -> dict:
    """Live status of an order using the finest candles available (M1 in a backtest
    market, M5 live), with the same rules as simulate(). Unlike simulate_order it knows
    the data stops at 'now': an unfilled order whose window is still open is 'pending'
    and a filled trade with no exit yet is 'open' (with its R at the last close).
    Returns {status, fill_time?, results: {mgmt: {state, R, exit_time?}}}."""
    tf = "M1" if ("M1", mirrored) in mkt.view else "M5"
    M = mkt.view[(tf, mirrored)]
    R = mkt.view[(range_tf, mirrored)]
    n = len(M.t_open)
    start = int(np.searchsorted(M.t_open, order["t_dec"], side="left"))
    pend_true = int(order["t_end"][2])
    pend_end = int(np.searchsorted(M.t_open, pend_true, side="left"))
    last_close = int(M.t_close[-1]) if n else 0

    def hold_stop_ns(t0: int) -> int:
        j = int(np.searchsorted(R.t_close, t0, side="left")) + K.HOLD_RANGE_CANDLES - 1
        if j < len(R.t_close):
            return int(R.t_close[j])
        have = int(R.t_close[-1]) if len(R.t_close) else t0
        extra = j - (len(R.t_close) - 1)
        return next_closes(range_tf, have, extra)[-1]

    def hold_end(fill_idx: int) -> int:
        t0 = M.t_close[fill_idx] if fill_idx >= 0 else order["t_dec"]
        return int(np.searchsorted(M.t_open, hold_stop_ns(int(t0)), side="left"))

    fill_shift, exit_shift = (spread, 0.0) if mirrored else (0.0, spread)
    if start >= n:
        return {"status": "pending", "tf": tf, "results": {}}
    out = simulate(M.h, M.l, M.c, start, pend_end, hold_end, entry=order["entry"], market=order["market"],
                   stop=order["stop"], targets=order["targets"], t1=order["targets"]["T1"],
                   fill_shift=fill_shift, exit_shift=exit_shift)
    status = out["status"]
    if status == "expired" and pend_true > last_close:
        return {"status": "pending", "tf": tf, "results": {}}
    res = {"status": status, "tf": tf, "results": {}}
    if status != "filled":
        return res
    fill_i = out["fill"]
    res["fill_time"] = int(M.t_close[fill_i]) if fill_i >= 0 else int(order["t_dec"])
    res["entry_px"] = out["entry_px"]
    still_open = hold_stop_ns(res["fill_time"]) > last_close
    for m, r in out["results"].items():
        state = r["reason"]
        if state == "time" and still_open:
            state = "open"
        res["results"][m] = {"state": state, "R": float(r["R"]),
                             "exit_time": int(M.t_close[r["exit"]]) if state != "open" else None}
    return res

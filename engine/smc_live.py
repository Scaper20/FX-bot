"""Live H1 order-block model (spec v16), WATCH ONLY: D1 + H4 structure bias, H1 market structure shift
in the bias direction, limit order at the order block's open, stop above the top + 2 spreads, 3R.

Backtest: +0.27R a trade on GBP/USD + gold (2021-26) but -0.12R on EUR/USD + silver, so it failed the
fresh-market test. Logged live (at the moment it forms, before the outcome) so Ore can watch it forward.
Same detection as backtest/smc_bias.py (engine/structure.py).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as K
from . import structure as S
from .calendar import next_closes
from .sessions import friday_late, in_killzone, session_flags
from .setups import Market

MODEL = "smc_h1_ob"
LABEL = "H1 order block · D1+H4 bias"
NOTE = ("Watch-only model (spec v16). Backtest 2021–26: +0.27R a trade on GBP/USD + gold, but −0.12R on "
        "EUR/USD + silver, so it failed the fresh-market test. Logged here to measure it live.")
VALID = 12            # H1 candles the limit order stays valid
RR_T = 3.0
RECENT = 6            # only MSS candles among the last 6 closed H1 candles become cards
HOLD = {"hold_tf": "D1", "hold_n": 3}


def _ts(ns: int) -> str:
    return pd.Timestamp(int(ns), tz="UTC").isoformat()


def _bias(mkt: Market, tf: str, t_ns: int) -> int:
    F = mkt.frames[tf]
    if len(F) < 10:
        return 0
    d = S.structure_direction(F["high"].to_numpy(), F["low"].to_numpy(), F["close"].to_numpy(), K.SWING_N)
    tc = pd.DatetimeIndex(F["close_time_utc"]).as_unit("ns").asi8
    i = int(np.searchsorted(tc, t_ns, side="right")) - 1
    return int(d[i]) if i >= 0 else 0


def scan_smc_pair(mkt: Market, pair: str, spread: float) -> list[dict]:
    from .live import ENGINE_VERSION, _candles, all_tf_candles   # live imports this module

    if len(mkt.frames["H1"]) < 60:
        return []
    out = []
    for mir in (False, True):
        V = mkt.view[("H1", mir)]
        o, h, l, c = V.o, V.h, V.l, V.c
        n = len(c)
        sg = -1.0 if mir else 1.0
        real = 1 if mir else -1                                   # +1 buy, -1 sell
        for j, top, swing in S.mss_events(o, h, l, c, include_last=True):
            if j < n - RECENT:
                continue
            t_dec = int(V.t_close[j])
            b_d1, b_h4 = _bias(mkt, "D1", t_dec), _bias(mkt, "H4", t_dec)
            if not (b_d1 == real and b_h4 == real):
                continue
            ob = S.bear_order_block(o, h, l, c, top, j, K.OB_SEARCH)
            if not ob:
                continue
            e, stop = ob["open"], h[top] + 2 * spread
            if not (stop > e > c[j]):
                continue
            risk = stop - e
            tgt = e - RR_T * risk
            far = e - 1000 * risk                                   # no cancel-at-50% for this model
            last = j + VALID
            t_end = int(V.t_close[last]) if last < n else next_closes("H1", int(V.t_close[-1]), last - (n - 1))[-1]
            rr = (e - tgt - spread) / (risk + spread)
            dec = pd.Timestamp(t_dec, tz="UTC")
            session = session_flags(dec)
            side = "long" if mir else "short"
            oid = "H1-MSS-E4-S1p-M1_T2"
            option = {
                "id": oid, "entry_tf": "H1", "trigger": "MSS", "entry_type": "E4", "stop_type": "S1p", "mgmt": "M1_T2",
                "entry": sg * e, "stop": sg * stop, "target": sg * tgt, "t1": None, "market": False,
                "rr": round(float(rr), 2), "risk": float(risk), "cost_share": round(float(spread / risk), 3),
                "chance": 0.25, "p_target": 0.25, "breakeven": round(float((risk + spread) / (risk + (e - tgt))), 3),
                "chance_avg_R": round(-float(spread / risk), 3), "decision_time": dec.isoformat(),
                "session": session, "killzone": in_killzone(dec) or "", "friday_late": bool(friday_late(dec)),
                "recommended": False, "rules": {"session_ok": session != "", "direction_ok": True, "backed": False},
                "stats": None,
                "order": {"t_dec": t_dec, "t_end": {"1": t_end, "2": t_end}, "entry": float(e), "stop": float(stop),
                          "market": False, "targets": {"T1": float(far), "T2": float(tgt)}, **HOLD},
            }
            word = "bullish" if mir else "bearish"
            card = {
                "id": f"{pair}-SMCH1-{dec.strftime('%Y%m%d%H%M')}-{side}", "model": MODEL, "model_label": LABEL,
                "model_note": NOTE, "pair": pair, "range_tf": "H1", "k": 0, "direction": side,
                "range_open": _ts(V.t_open[top]), "range_close": _ts(t_dec),
                "range_high": None, "range_low": None, "range_mid": None, "sweep_extreme": None,
                "sweep_open": None, "sweep_close": None, "window_end": _ts(t_end),
                "smc": {"bias": f"D1 and H4 {word}", "top_time": _ts(V.t_open[top]), "top_price": float(sg * h[top]),
                        "swing_time": _ts(V.t_open[swing]), "swing_price": float(sg * l[swing]),
                        "mss_time": _ts(V.t_open[j]), "ob_time": _ts(V.t_open[ob["idx"]]),
                        "ob_open": float(sg * e), "ob_far": float(sg * ob["high"])},
                "entry_status": {"H1": "ok"}, "options": [option], "features": {}, "engine": ENGINE_VERSION,
                "state": "ready", "recommended": False, "best": oid, "decision_time": dec.isoformat(),
                "checks": [
                    {"group": "Bias", "label": f"D1 structure {word}", "ok": True, "note": ""},
                    {"group": "Bias", "label": f"H4 structure {word}", "ok": True, "note": ""},
                    {"group": "Structure", "label": "H1 closed " + ("above the latest swing high" if mir else
                                                                    "below the latest swing low") + " (MSS)",
                     "ok": True, "note": ""},
                    {"group": "Entry", "label": "Order block took liquidity and left an FVG", "ok": True, "note": ""},
                    {"group": "Session", "label": "MSS in London / New York", "ok": session != "",
                     "note": session or "outside both sessions"},
                ],
                "chart": {"range": _candles(mkt.frames["H1"].iloc[max(0, top - 30):], None, 60),
                          "entry": _candles(mkt.frames["H1"].iloc[max(0, swing - 20):], None, 120),
                          "entry_tf": "H1", "tfs": all_tf_candles(mkt)},
            }
            out.append(card)
    return out

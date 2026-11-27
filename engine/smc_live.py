"""Live SMC strategies (spec v22, 27 Nov 2026): order block, Toni Iyke, Lingard.

The rules live in engine/smc_models.py and run on engine/smc_structure.external_structure, the same code as the
backtest (backtest/smc_v22.py). The old tiny-swing order-block detection (v16) is retired.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from .calendar import next_closes
from .sessions import friday_late, in_killzone, session_flags
from .setups import Market
from .smc_models import LOOK, lingard_setups, orderblock_setups, toni_setups
from .smc_structure import external_structure, irl_erl_bias
from .strategies import STRATEGIES

STATS_FILE = Path(__file__).resolve().parent / "data" / "smc_v22_stats.json"
MODELS = {
    "smc_ob": {"tf": "H1", "mode": "close", "bias": ("D1", "H4"), "target": "3R", "recent": 6, "hold": 5},
    "toni": {"tf": "H1", "mode": "close", "bias": ("D1",), "target": "liq", "recent": 6, "hold": 5},
    "irl_erl": {"tf": "H1", "mode": "close", "bias": ("H4 IRL/ERL", "D1"), "target": "3R", "recent": 6, "hold": 5},
    "lingard": {"tf": "H4", "mode": "wick", "bias": ("D1",), "target": "5R", "recent": 2, "hold": 10,
                "session": True},
}
MODEL = "smc_ob"            # kept for older imports
WORD = {1: "bullish", -1: "bearish", 0: "no clear trend"}


@lru_cache(maxsize=1)
def _stats() -> dict:
    return json.loads(STATS_FILE.read_text()) if STATS_FILE.exists() else {}


def _ts(t) -> str:
    return pd.Timestamp(t).isoformat() if not isinstance(t, (int, np.integer)) else pd.Timestamp(int(t), tz="UTC").isoformat()


def _ohlc(F):
    return tuple(F[k].to_numpy(float) for k in ("open", "high", "low", "close"))


def _atr(h, l, c, n=14):
    tr = np.maximum(h - l, np.abs(h - np.r_[c[0], c[:-1]]))
    tr = np.maximum(tr, np.abs(l - np.r_[c[0], c[:-1]]))
    return pd.Series(tr).rolling(n, min_periods=n).mean().to_numpy()


def trend(mkt: Market, tf: str, t_ns: int) -> int:
    """External trend (+1/-1/0) on timeframe tf known at t_ns (close breaks)."""
    F = mkt.frames[tf]
    if len(F) < 25:
        return 0
    ev = external_structure(*_ohlc(F), "close")
    cl = pd.DatetimeIndex(F["close_time_utc"]).as_unit("ns").asi8
    out = 0
    for e in ev:
        if cl[e["j"]] > t_ns:
            break
        out = e["dir"]
    return out


IE_TEXT = {"erl_high": "took the range high (buy-side ERL), next draw: IRL below",
           "erl_low": "took the range low (sell-side ERL), next draw: IRL above",
           "irl_bull": "traded into a bullish FVG (IRL), next draw: ERL high",
           "irl_bear": "traded into a bearish FVG (IRL), next draw: ERL low", "": "no liquidity event yet"}


def irl_erl(mkt: Market, tf: str, t_ns: int) -> dict:
    """IRL/ERL state on tf known at t_ns (spec v23): bias +1/-1/0 and the last liquidity event."""
    F = mkt.frames[tf]
    if len(F) < 25:
        return {"bias": 0, "event": "", "text": IE_TEXT[""]}
    b, last = irl_erl_bias(*_ohlc(F))
    cl = pd.DatetimeIndex(F["close_time_utc"]).as_unit("ns").asi8
    i = int(np.searchsorted(cl, t_ns, side="right")) - 1
    if i < 0:
        return {"bias": 0, "event": "", "text": IE_TEXT[""]}
    return {"bias": int(b[i]), "event": str(last[i]), "text": IE_TEXT[str(last[i])]}


def _ie_summary(mkt: Market, t_ns: int, d: int | None = None) -> dict:
    out = {}
    for tf in ("H4", "D1"):
        st = irl_erl(mkt, tf, t_ns)
        st["word"] = WORD[st["bias"]]
        if d is not None:
            st["agrees"] = st["bias"] == d
        out[tf] = st
    return out


def bias_value(mkt: Market, spec: str, t_ns: int) -> int:
    """A bias source: 'D1' / 'H4' = external trend on that timeframe; 'H4 IRL/ERL' = the IRL/ERL draw (spec v23)."""
    if spec.endswith(" IRL/ERL"):
        return irl_erl(mkt, spec.split()[0], t_ns)["bias"]
    return trend(mkt, spec, t_ns)


def _bias_label(spec: str, v: int) -> str:
    return f"{spec} {WORD[v]}" if spec.endswith("IRL/ERL") else f"{spec} trend {WORD[v]}"


def _setups(key: str, o, h, l, c):
    m = MODELS[key]
    ev = external_structure(o, h, l, c, m["mode"])
    if key in ("smc_ob", "irl_erl"):
        out = orderblock_setups(o, h, l, c, ev)
        for x in out:
            x["model"] = key
        return out, ev
    if key == "toni":
        return toni_setups(o, h, l, c, ev), ev
    return lingard_setups(o, h, l, c, ev, _atr(h, l, c)), ev


def scan_smc_pair(mkt: Market, pair: str, spread: float) -> list[dict]:
    from .live import ENGINE_VERSION, _candles, all_tf_candles   # live imports this module

    out = []
    for key, m in MODELS.items():
        F = mkt.frames[m["tf"]]
        if len(F) < 60:
            continue
        o, h, l, c = _ohlc(F)
        n = len(c)
        to = F.index.as_unit("ns").asi8
        tc = pd.DatetimeIndex(F["close_time_utc"]).as_unit("ns").asi8
        setups, _ = _setups(key, o, h, l, c)
        for s in setups:
            j, d = s["decision"], s["dir"]
            if j < n - m["recent"]:
                continue
            t_dec = int(tc[j])
            biases = {tf: bias_value(mkt, tf, t_dec) for tf in m["bias"]}
            if any(v != d for v in biases.values()):
                continue
            dec = pd.Timestamp(t_dec, tz="UTC")
            session = session_flags(dec)
            if m.get("session") and not session:
                continue
            e, stop = float(s["entry"]), float(s["far"] + (-2 if d == 1 else 2) * spread)
            risk = abs(e - stop)
            if m["target"] == "liq":
                if s["liq"] is None or (d == 1 and s["liq"] <= e) or (d == -1 and s["liq"] >= e):
                    continue
                tgt = float(s["liq"])
            else:
                tgt = e + d * float(m["target"][0]) * risk
            rr = (abs(tgt - e) - spread) / (risk + spread)
            last = j + s["valid"]
            t_end = int(tc[last]) if last < n else next_closes(m["tf"], int(tc[-1]), last - (n - 1))[-1]
            side = "long" if d == 1 else "short"
            st_key = f"toni_{s['struct']}" if key == "toni" else key
            stats = (_stats().get(st_key) or {}).get(pair)
            trig = s["line"][3]
            mg = {"3R": "T3R", "5R": "T5R", "liq": "TLIQ"}[m["target"]]
            oid = f"{m['tf']}-{key}-Z-SZ-{mg}"
            option = {
                "id": oid, "entry_tf": m["tf"], "trigger": "SMC", "entry_type": "Z", "stop_type": "SZ", "mgmt": mg,
                "entry": e, "stop": stop, "target": tgt, "t1": None, "market": False, "rr": round(float(rr), 2),
                "risk": float(risk), "cost_share": round(float(spread / risk), 3),
                "chance": round(float(risk / (risk + abs(tgt - e))), 3),
                "p_target": round(float(risk / (risk + abs(tgt - e))), 3),
                "breakeven": round(float((risk + spread) / (risk + abs(tgt - e))), 3),
                "chance_avg_R": round(-float(spread / risk), 3), "decision_time": dec.isoformat(),
                "session": session, "killzone": in_killzone(dec) or "", "friday_late": bool(friday_late(dec)),
                "recommended": True, "rules": {"session_ok": True, "direction_ok": True, "backed": False},
                "stats": stats,
                "order": {"t_dec": t_dec, "t_end": {"1": t_end, "2": t_end}, "entry": e, "stop": stop,
                          "market": False, "targets": {"T1": e + d * 1000 * risk, "T2": tgt},
                          "hold_tf": "D1", "hold_n": m["hold"]},
            }
            zf, zl, zlo, zhi = s["zone"]
            lf, lt, lpx, llab = s["line"]
            if key in ("smc_ob", "irl_erl"):
                p = s["origin"]
                origin = {"time": _ts(to[p]), "price": float(h[p] if d == -1 else l[p]),
                          "label": "Top of the move" if d == -1 else "Bottom of the move"}
                zone_label = f"Order block ({s['variant']})"
            elif key == "toni":
                origin = {"time": _ts(to[j]), "price": float(s["inducement"]), "label": "Inducement"}
                zone_label = s["variant"].split(" · ")[1].capitalize()
            else:
                origin = {"time": _ts(to[s["pullback"]]), "price": float(s["liquidity"]),
                          "label": "Liquidity (first pullback)"}
                zone_label = "Order block (POI)"
            bias_txt = " and ".join(_bias_label(tf, d) for tf in m["bias"])
            card = {
                "id": f"{pair}-{key.upper()}-{dec.strftime('%Y%m%d%H%M')}-{side}", "strategy": key, "model": key,
                "model_label": STRATEGIES[key]["long"], "model_note": STRATEGIES[key]["evidence"],
                "pair": pair, "range_tf": m["tf"], "k": 0, "direction": side,
                "range_open": _ts(to[zf]), "range_close": dec.isoformat(),
                "range_high": None, "range_low": None, "range_mid": None, "sweep_extreme": None,
                "sweep_open": None, "sweep_close": None, "window_end": _ts(t_end),
                "smc": {"bias": bias_txt, "tf": m["tf"], "variant": s["variant"],
                        "zone": {"start": _ts(to[zf]), "end": _ts(to[zl]), "low": float(zlo), "high": float(zhi),
                                 "label": zone_label},
                        "line": {"start": _ts(to[lf]), "end": _ts(to[lt]), "price": float(lpx), "label": llab},
                        "origin": origin, "irl_erl": _ie_summary(mkt, t_dec, d)},
                "entry_status": {m["tf"]: "ok"}, "options": [option], "features": {}, "engine": ENGINE_VERSION,
                "state": "ready", "recommended": True, "best": oid, "decision_time": dec.isoformat(),
                "checks": [{"group": "Bias", "label": _bias_label(tf, d), "ok": True, "note": ""} for tf in m["bias"]]
                + [{"group": "Structure", "label": f"{m['tf']} {trig}", "ok": True, "note": s["variant"]},
                   {"group": "Entry", "label": f"{zone_label} at the zone edge", "ok": True, "note": ""},
                   {"group": "Info", "label": "London / New York session",
                    "ok": session != "", "note": session or "outside both sessions"}]
                + [{"group": "Info", "label": f"IRL/ERL {tf} points the same way (not a rule yet, spec v23)",
                    "ok": v["agrees"], "note": v["text"]} for tf, v in _ie_summary(mkt, t_dec, d).items()],
                "chart": {"range": _candles(F.iloc[max(0, zf - 40):], None, 160),
                          "entry": _candles(F.iloc[max(0, zf - 40):], None, 160),
                          "entry_tf": m["tf"], "tfs": all_tf_candles(mkt)},
            }
            out.append(card)
    return out


# ------------------------------------------------------------------ tracking status ("what it's waiting for")


def _leg_extreme(h, l, j, d):
    return (j + int(np.argmax(h[j:]))) if d == 1 else (j + int(np.argmin(l[j:])))


def watch_smc_pair(mkt: Market, pair: str) -> list[dict]:
    """One heads-up per strategy and pair: which step it is on. Never logged as a setup."""
    out = []
    M5 = mkt.frames["M5"]
    if M5.empty:
        return out
    price = float(M5["close"].iloc[-1])
    for key, m in MODELS.items():
        F = mkt.frames[m["tf"]]
        if len(F) < 60:
            continue
        o, h, l, c = _ohlc(F)
        n = len(c)
        tc = pd.DatetimeIndex(F["close_time_utc"]).as_unit("ns").asi8
        now = int(tc[-1])
        forming = M5[M5.index.as_unit("ns").asi8 >= now]
        biases = {tf: bias_value(mkt, tf, now) for tf in m["bias"]}
        bias_txt = " · ".join(_bias_label(tf, v) for tf, v in biases.items())
        ie = _ie_summary(mkt, now)
        w = {"pair": pair, "strategy": key, "price": price, "bias": bias_txt, "direction": None, "step": 1,
             "irl_erl": " · ".join(f"{tf} {v['text']}" for tf, v in ie.items()) if key in ("smc_ob", "irl_erl") else "",
             "steps": 3, "title": "Bias", "level": None, "beyond_now": False, "distance": None,
             "closes_at": _ts(next_closes(m["tf"], now, 1)[0])}
        vals = set(biases.values())
        if len(vals) != 1 or 0 in vals:
            w["text"] = (f"{' and '.join(m['bias'])} don't agree, so there is no trade direction." if len(m["bias"]) > 1
                         else "No clear D1 trend, so there is no trade direction.")
            out.append(w)
            continue
        d = vals.pop()
        w["direction"] = "long" if d == 1 else "short"
        ev = external_structure(o, h, l, c, m["mode"])
        last = ev[-1] if ev else None
        up, word = d == 1, ("above" if d == 1 else "below")
        brk = "close" if m["mode"] == "close" else "trade"
        if last is None:
            w["text"] = f"Not enough {m['tf']} structure yet."
        elif last["dir"] != d:
            p = last["protected"]
            lvl = float(h[p] if up else l[p])
            w.update(step=2, title=f"Waiting for the {m['tf']} MSS", level=lvl, distance=abs(price - lvl),
                     beyond_now=bool(len(forming)) and (price > lvl if up else price < lvl))
            w["text"] = (f"{m['tf']} is still moving against the bias. A {m['tf']} candle must {brk} {word} "
                         f"{lvl:.5f} (the swing that protects that move)." if pair == "GBPUSD" else
                         f"{m['tf']} is still moving against the bias. A {m['tf']} candle must {brk} {word} "
                         f"{lvl:,.2f} (the swing that protects that move).")
        else:
            x = _leg_extreme(h, l, last["j"], d)
            lvl = float(h[x] if up else l[x])
            if key == "toni" and n - 1 - last["j"] < LOOK:
                w.update(step=2, title="Waiting for the inducement", level=float(c[last["j"]]))
                w["text"] = (f"{m['tf']} {last['kind']} in the bias direction. Next: a pullback, then a candle "
                             f"closing {word} the structure candle's close; then the closest untouched breaker or "
                             f"order block becomes the entry.")
            elif key == "lingard" and last["kind"] == "MSS":
                w.update(step=2, title="Waiting for the first BOS", level=lvl, distance=abs(price - lvl))
                w["text"] = (f"{m['tf']} trend just turned with the bias. The first break {word} the new high/low "
                             f"marks the first pullback as liquidity; the order block beyond it is the entry.")
            else:
                w.update(step=2, title=f"Waiting for a pullback on {m['tf']}", level=lvl)
                w["text"] = (f"{m['tf']} is already moving with the bias. The setup needs a pullback against it "
                             f"and then a shift back.")
        out.append(w)
    return out

"""Live scan (spec v1.3): turn a Market into setup cards.

A card = one CRT (pair, range candle, sweep candle, direction).
  ready  - a lower-timeframe trigger has fired; entry options listed and ranked
  armed  - valid sweep closed back inside; waiting for the trigger until the window ends
  watch  - the range candle forming right now is trading beyond the previous candle
Everything here reads only closed candles from the Market, the same engine as the backtest.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from . import config as K
from .calendar import next_closes
from .setups import Market, find_orders, track_order

ENGINE_VERSION = "v1.9"   # v1.9: weekend quotes dropped from the live feed; v1.8: long stored D1 history (D1 trend matched the backtests only ~62% of days on GBP/USD); v1.7: Ore's model (HTF POI, spec v26); v1.4: C2 closes inside C1's body; v1.5: order-block strategy is a full strategy (25 Nov 2026)
STATS_FILE = Path(__file__).resolve().parent / "data" / "pattern_stats.json"
MGMTS = ("M1_T1", "M1_T2", "M1_T3", "M2_T2", "M2_T3")
LIVE_STOPS = ("S1p", "S1a", "S2")
S2_MAX_COST_SHARE = 0.15
SHRINK_K = 50            # trades worth of "pull towards the average" when ranking

ENTRY_LABEL = {"E1": "Market, at the trigger candle's close", "E2": "Limit at the FVG's near edge",
               "E3": "Limit at the FVG's middle", "E4": "Limit at the order block's open",
               "E5": "Limit at the order block's middle", "Z": "Limit at the zone's near edge"}
STOP_LABEL = {"S1": "Sweep extreme", "S1p": "Sweep extreme + 2 spreads", "S1a": "Sweep extreme + 0.1 ATR",
              "S2": "Tight: FVG / order-block edge", "SZ": "Beyond the zone + 2 spreads"}
MGMT_LABEL = {"M1_T1": "All out at the 50% level", "M1_T2": "All out at the opposite side",
              "M1_T3": "All out at the next swing beyond", "M2_T2": "Half at 50%, stop to entry, rest at opposite side",
              "M2_T3": "Half at 50%, stop to entry, rest at next swing", "T3R": "All out at 3R",
              "T5R": "All out at 5R", "TLIQ": "All out at the structure target (liquidity)"}
TRIGGER_LABEL = {"CISD": "CISD (close beyond the open of the run that made the sweep)",
                 "MSS": "MSS (close beyond the last swing before the sweep)",
                 "SMC": "Market structure (MSS / BOS on the main swings)"}


@lru_cache(maxsize=1)
def load_stats() -> dict:
    if not STATS_FILE.exists():
        return {}
    return json.loads(STATS_FILE.read_text())


def _prior(stats: dict) -> float:
    vals = [(v["n"], v["avg_R"]) for k, v in stats.items() if not k.startswith("_")]
    n = sum(a for a, _ in vals)
    return sum(a * b for a, b in vals) / n if n else 0.0


def option_stats(pair, range_tf, entry_tf, trigger, entry_type, stop_type, mgmt) -> dict | None:
    st = load_stats()
    v = st.get("|".join([pair, range_tf, entry_tf, trigger, entry_type, stop_type, mgmt]))
    if not v:
        return None
    prior = _prior_cached()
    out = dict(v)
    out["score"] = round((v["n"] * v["avg_R"] + SHRINK_K * prior) / (v["n"] + SHRINK_K), 3)
    out["enough"] = v["n"] >= 30
    return out


@lru_cache(maxsize=1)
def _prior_cached() -> float:
    return _prior(load_stats())


def ts(ns: int | None) -> str | None:
    return None if ns is None else pd.Timestamp(int(ns), tz="UTC").isoformat()


def setup_id(pair: str, range_tf: str, range_open_ns: int, k: int, mirrored: bool) -> str:
    t = pd.Timestamp(int(range_open_ns), tz="UTC").strftime("%Y%m%d%H%M")
    return f"{pair}-{range_tf}-{t}-k{k}-{'long' if mirrored else 'short'}"


def _real(x: float | None, mirrored: bool) -> float | None:
    return None if x is None else (-x if mirrored else x)


def _rules(f: dict) -> dict:
    """Ore's rules (spec v1.3) for one option's trigger."""
    session_ok = f["session"] in ("london", "newyork", "overlap") and not f["friday_late"]
    backed = bool(f["htf_fvg"] or f["htf_ob"])
    direction_ok = f["trend_struct"] == "with" or backed
    return {"session_ok": session_ok, "direction_ok": direction_ok, "backed": backed}


def _options(pair: str, range_tf: str, entry_tf: str, o: dict, mirrored: bool, spread: float) -> list[dict]:
    out = []
    if o["stop_type"] not in LIVE_STOPS:
        return out
    risk = o["stop"] - o["entry"]
    if risk <= 0:
        return out
    cost_share = spread / risk
    if o["stop_type"] == "S2" and cost_share > S2_MAX_COST_SHARE:
        return out
    rules = _rules(o)
    for m in MGMTS:
        tname = m.split("_")[1]
        tgt = o["targets"].get(tname)
        rr = o["rr"].get(tname)
        if tgt is None or rr is None or rr < K.MIN_RR:
            continue
        if m.startswith("M2") and not (o["targets"]["T1"] < o["entry"]):
            continue
        reward = o["entry"] - tgt
        if m.startswith("M2"):
            r1 = o["entry"] - o["targets"]["T1"]
            p_win = risk / (risk + r1)                    # half banked at 50% before the stop
            p_target = p_win * r1 / reward                # then the rest reaches target before entry
            breakeven = None                              # mixed outcome sizes: see expected R instead
        else:
            p_win = p_target = risk / (risk + reward)
            breakeven = (risk + spread) / (risk + reward)
        chance = p_win
        st = option_stats(pair, range_tf, entry_tf, o["trigger"], o["entry_type"], o["stop_type"], m)
        out.append({
            "id": f"{entry_tf}-{o['trigger']}-{o['entry_type']}-{o['stop_type']}-{m}",
            "entry_tf": entry_tf, "trigger": o["trigger"], "entry_type": o["entry_type"],
            "stop_type": o["stop_type"], "mgmt": m,
            "entry": _real(o["entry"], mirrored), "stop": _real(o["stop"], mirrored),
            "target": _real(tgt, mirrored), "t1": _real(o["targets"]["T1"], mirrored),
            "market": bool(o["market"]), "rr": round(float(rr), 2), "risk": float(risk),
            "cost_share": round(float(cost_share), 3), "chance": round(float(chance), 3),
            "p_target": round(float(p_target), 3),
            "breakeven": None if breakeven is None else round(float(breakeven), 3),
            "chance_avg_R": round(-float(cost_share), 3),
            "decision_time": o["decision_time"].isoformat(), "session": o["session"],
            "killzone": o["killzone"] or "", "friday_late": bool(o["friday_late"]),
            "recommended": bool(rules["session_ok"] and rules["direction_ok"]),
            "rules": rules, "stats": st,
            "order": {"t_dec": int(o["t_dec"]), "t_end": {"1": int(o["t_end"][1]), "2": int(o["t_end"][2])},
                      "entry": float(o["entry"]), "stop": float(o["stop"]), "market": bool(o["market"]),
                      "targets": {k2: (None if v is None else float(v)) for k2, v in o["targets"].items()}},
        })
    return out


def _rank_key(op: dict):
    """Recommended first; then options with enough history (30+ trades) by their shrunk average;
    options with too little history last, cheapest spread first."""
    s = op["stats"]
    enough = bool(s and s["enough"])
    score = s["score"] if enough else -9.0
    return (op["recommended"], enough, score, -op["cost_share"])


TF_BARS = {"D1": 120, "H4": 180, "H1": 240, "M15": 300, "M5": 300}


def compact_candles(df: pd.DataFrame, count: int) -> list:
    """Last `count` candles as [unix_seconds, o, h, l, c] (small, for interactive charts)."""
    x = df.tail(count)
    t = (x.index.as_unit("s").asi8).tolist()
    cols = [x[c].round(5).tolist() for c in ("open", "high", "low", "close")]
    return [[t[i], cols[0][i], cols[1][i], cols[2][i], cols[3][i]] for i in range(len(t))]


def all_tf_candles(mkt: Market) -> dict:
    return {tf: compact_candles(mkt.frames[tf], n) for tf, n in TF_BARS.items()}


def _candles(df: pd.DataFrame, start_ns: int | None = None, count: int = 60) -> list:
    x = df if start_ns is None else df[df.index.as_unit("ns").asi8 >= start_ns]
    x = x.tail(count)
    return [[t.isoformat(), round(float(r.open), 5), round(float(r.high), 5), round(float(r.low), 5),
             round(float(r.close), 5)] for t, r in x.iterrows()]


def scan_pair(mkt: Market, pair: str, spread: float) -> list[dict]:
    """All ready / armed cards for one pair at mkt.now_ns."""
    cards: dict[str, dict] = {}
    now_ns = mkt.now_ns
    for range_tf, entry_tfs in K.RANGE_TO_ENTRY.items():
        R0 = mkt.view[(range_tf, False)]
        last = len(R0.o) - 1
        for i in range(max(0, last - 3), last + 1):
            for k in (1, 2):
                if i + k > last:
                    continue
                for mirrored in (False, True):
                    for etf in entry_tfs:
                        info: dict = {}
                        orders, why = find_orders(mkt, range_tf, etf, i, k, mirrored, spread, info)
                        if why not in ("ok", "waiting", "invalidated", "rr_too_small"):
                            continue
                        if info.get("window_end_ns", 0) <= now_ns and why != "ok":
                            continue
                        sid = setup_id(pair, range_tf, R0.t_open[i], k, mirrored)
                        c = cards.setdefault(sid, _new_card(sid, pair, range_tf, R0, i, k, mirrored, info))
                        c["entry_status"][etf] = why
                        for o in orders:
                            c["options"].extend(_options(pair, range_tf, etf, o, mirrored, spread))
                            c["features"] = {key: (bool(o[key]) if isinstance(o[key], (bool, np.bool_)) else o[key])
                                             for key in ("htf_fvg", "htf_ob", "htf_mss", "msnr", "trend_struct",
                                                         "trend_ema", "has_fvg", "has_ob", "mtf_mss",
                                                         "other_trigger", "range_small")}
                            c["features"].update(sweep_ratio=round(float(o["sweep_ratio"]), 2),
                                                 sweep_depth_atr=(None if not np.isfinite(o["sweep_depth_atr"])
                                                                  else round(float(o["sweep_depth_atr"]), 2)),
                                                 close_pos=round(float(o["close_pos"]), 2))
    out = []
    for c in cards.values():
        _finish_card(mkt, c)
        if c["state"] in ("ready", "armed"):
            out.append(c)
    return out


def _new_card(sid, pair, range_tf, R0, i, k, mirrored, info) -> dict:
    sgn = -1 if mirrored else 1
    return {
        "id": sid, "strategy": "crt", "pair": pair, "range_tf": range_tf, "k": k,
        "direction": "long" if mirrored else "short",
        "range_open": ts(R0.t_open[i]), "range_close": ts(R0.t_close[i]),
        "range_high": float(R0.h[i]), "range_low": float(R0.l[i]), "range_mid": float((R0.h[i] + R0.l[i]) / 2),
        "sweep_open": ts(info.get("sweep_open_ns")), "sweep_close": ts(info.get("sweep_close_ns")),
        "sweep_extreme": float(sgn * info["sweep_extreme"]) if "sweep_extreme" in info else None,
        "window_end": ts(info.get("window_end_ns")),
        "entry_status": {}, "options": [], "features": {}, "engine": ENGINE_VERSION,
        "_i": i, "_mirrored": mirrored,
    }


def _finish_card(mkt: Market, c: dict) -> None:
    opts = c["options"]
    # one trigger per entry timeframe: keep the earliest decision (the other becomes a confluence)
    first_dec = {}
    for op in opts:
        first_dec.setdefault(op["entry_tf"], op["decision_time"])
        first_dec[op["entry_tf"]] = min(first_dec[op["entry_tf"]], op["decision_time"])
    opts = [op for op in opts if op["decision_time"] == first_dec[op["entry_tf"]]]
    seen, uniq = set(), []
    for op in opts:
        key = (op["entry_tf"], op["entry_type"], op["stop_type"], op["mgmt"])
        if key not in seen:
            seen.add(key)
            uniq.append(op)
    uniq.sort(key=_rank_key, reverse=True)
    c["options"] = uniq
    if uniq:
        c["state"] = "ready"
    elif any(v == "waiting" for v in c["entry_status"].values()):
        c["state"] = "armed"
    else:
        c["state"] = "none"
    c["recommended"] = any(op["recommended"] for op in uniq)
    best = uniq[0] if uniq else None
    c["best"] = best["id"] if best else None
    c["decision_time"] = best["decision_time"] if best else None
    c["checks"] = _checks(c, best)
    # chart: range timeframe around the setup, entry timeframe from before the sweep to now
    rdf = mkt.frames[c["range_tf"]]
    c["chart"] = {"range": _candles(rdf.iloc[max(0, c["_i"] - 12):], None, 24)}
    etf = best["entry_tf"] if best else K.RANGE_TO_ENTRY[c["range_tf"]][0]
    edf = mkt.frames[etf]
    sw = pd.Timestamp(c["sweep_open"]).value if c["sweep_open"] else None
    step = pd.Timedelta({"H1": "1h", "M15": "15min", "M5": "5min"}[etf]).value
    c["chart"]["entry"] = _candles(edf, (sw - 24 * step) if sw else None, 200)
    c["chart"]["entry_tf"] = etf
    c["chart"]["tfs"] = all_tf_candles(mkt)
    c.pop("_i", None)
    c.pop("_mirrored", None)


def _checks(c: dict, best: dict | None) -> list[dict]:
    f = c["features"]
    out = []

    def add(group, label, ok, note=""):
        out.append({"group": group, "label": label, "ok": ok, "note": note})

    add("CRT", f"Range candle {c['range_tf']} swept on candle +{c['k']}, closed back inside", True)
    if f:
        add("CRT", "Range candle is a full candle (not the short Sunday-evening one)", not f.get("range_small"),
            "short candle: the range may be too small to mean much" if f.get("range_small") else "")
        add("CRT", "Sweep candle no bigger than the range candle", f.get("sweep_ratio", 9) <= 1.0,
            f"sweep candle is {f.get('sweep_ratio')}x the range candle")
        if f.get("sweep_depth_atr") is not None:
            add("CRT", "Sweep went at least 0.1 ATR past the range", f["sweep_depth_atr"] >= 0.1,
                f"{f['sweep_depth_atr']} ATR")
        add("Ore", "With the daily direction (swing breaks)", f.get("trend_struct") == "with",
            f"daily direction is {f.get('trend_struct')} this trade")
        add("Ore", "HTF order block or FVG on the left at the sweep", bool(f.get("htf_ob") or f.get("htf_fvg")))
    if best:
        add("Ore", "Trigger in London / New York session", best["rules"]["session_ok"],
            best["session"] or "outside both sessions")
        add("ICT", "Killzone (London 07-10, NY 08:30-11 local)", bool(best["killzone"]), best["killzone"])
        add("ICT", "Fair value gap on the entry timeframe", bool(f.get("has_fvg")))
        add("ICT", "Valid order block on the entry timeframe", bool(f.get("has_ob")))
        add("ICT", "Both CISD and MSS", bool(f.get("other_trigger")))
        add("ICT", "Mid-timeframe MSS", bool(f.get("mtf_mss")))
        add("HTF", "HTF MSS on the sweep candle", bool(f.get("htf_mss")))
        add("MSnR", "Sweep at a fresh MSnR level (experimental)", bool(f.get("msnr")))
    return out


def watch_pair(mkt: Market, pair: str) -> list[dict]:
    """Range candles forming now that are trading beyond the previous candle."""
    out = []
    M5 = mkt.frames["M5"]
    if M5.empty:
        return out
    price = float(M5["close"].iloc[-1])
    for range_tf in K.RANGE_TO_ENTRY:
        R = mkt.frames[range_tf]
        if len(R) < 3:
            continue
        last_close = int(pd.DatetimeIndex(R["close_time_utc"]).as_unit("ns").asi8[-1])
        forming = M5[M5.index.as_unit("ns").asi8 >= last_close]
        if forming.empty:
            continue
        hi, lo = float(forming["high"].max()), float(forming["low"].min())
        closes_at = ts(next_closes(range_tf, last_close, 1)[0])
        for k, idx in ((1, -1), (2, -2)):
            prev = R.iloc[idx]
            if k == 2:
                mid = R.iloc[-1]
                if mid["high"] > prev["high"] or mid["low"] < prev["low"]:
                    continue
            body_lo, body_hi = sorted((float(prev["open"]), float(prev["close"])))
            in_body = body_lo < price < body_hi                    # Ore's rule: back inside C1's BODY
            if K.CRT_CLOSE == "range":
                in_body = float(prev["low"]) < price < float(prev["high"])
            for side, beyond, inside in (("short", hi > prev["high"], in_body),
                                         ("long", lo < prev["low"], in_body)):
                if beyond:
                    out.append({"pair": pair, "range_tf": range_tf, "k": k, "direction": side,
                                "range_open": prev.name.isoformat(), "range_high": float(prev["high"]),
                                "range_low": float(prev["low"]), "price": price, "back_inside": bool(inside),
                                "extreme": hi if side == "short" else lo, "closes_at": closes_at})
    return out


def scan(markets: dict[str, Market], spreads: dict[str, float]) -> dict:
    """Scan all pairs. Returns {'ready', 'armed', 'watch', 'smc_watch'} with ready cards
    ranked: recommended first, then by the best option's ranking score."""
    from .smc_live import scan_smc_pair, watch_smc_pair

    ready, armed, watch, smc_watch = [], [], [], []
    for pair, mkt in markets.items():
        for c in scan_pair(mkt, pair, spreads[pair]):
            (ready if c["state"] == "ready" else armed).append(c)
        watch += watch_pair(mkt, pair)
        ready += scan_smc_pair(mkt, pair, spreads[pair])      # SMC strategies (spec v22)
        smc_watch += watch_smc_pair(mkt, pair)          # one heads-up per SMC strategy

    def card_key(c):
        b = c["options"][0] if c["options"] else None
        sc = b["stats"]["score"] if b and b["stats"] else -9
        return (c["recommended"], sc)
    ready.sort(key=card_key, reverse=True)
    armed.sort(key=lambda c: c["window_end"] or "")
    return {"ready": ready, "armed": armed, "watch": watch, "smc_watch": smc_watch}


# Smart-money options exit all at their one target (order["targets"]["T2"]): the tracker reports that as "M1_T2".
# (Fixed 27 Nov 2026: looked up as "T3R"/"T5R"/"TLIQ", so filled SMC trades never showed target/stop/R.)
RESULT_KEY = {"T3R": "M1_T2", "T5R": "M1_T2", "TLIQ": "M1_T2"}


def track_card_options(mkt: Market, card: dict, spread: float) -> dict:
    """Live status of every option on a logged card: {option_id: track_order result}."""
    mirrored = card["direction"] == "long"
    out = {}
    for op in card["options"]:
        o = dict(op["order"])
        o["t_end"] = {1: o["t_end"]["1"], 2: o["t_end"]["2"]}
        st = track_order(mkt, o, card["range_tf"], mirrored, spread)
        mg = st.get("results", {}).get(RESULT_KEY.get(op["mgmt"], op["mgmt"]))
        out[op["id"]] = {"status": st["status"], "fill_time": ts(st.get("fill_time")),
                         "state": (mg or {}).get("state"), "R": (mg or {}).get("R"),
                         "exit_time": ts((mg or {}).get("exit_time")), "tf": st.get("tf")}
    return out

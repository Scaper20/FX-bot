"""Data for the interactive charts: candles per timeframe, levels, markers.

Practice setups keep their outcome candles ("after") hidden unless the viewer has answered."""
from __future__ import annotations

import gzip
import json
from functools import lru_cache
from pathlib import Path

import pandas as pd

TFS = ("M5", "M15", "H1", "H4", "D1")
CHART_DIR = Path(__file__).resolve().parent / "data" / "practice_charts"


def _sec(t) -> int:
    return int(pd.Timestamp(t).value // 1_000_000_000)


def _smc_levels(card: dict, op: dict | None) -> list[dict]:
    m = card["smc"]
    z, ln, og = m["zone"], m["line"], m["origin"]
    out = [{"price": z["high"], "title": f"{z['label']} top", "color": "#5B6577", "dashed": True, "from": _sec(z["start"])},
           {"price": z["low"], "title": f"{z['label']} bottom", "color": "#5B6577", "dashed": True, "from": _sec(z["start"])},
           {"price": ln["price"], "title": f"{ln['label']} level", "color": "#2F5D9E", "dashed": True,
            "from": _sec(ln["start"])},
           {"price": og["price"], "title": og["label"], "color": "#0F1B2D", "dashed": True, "from": _sec(og["time"])}]
    if op:
        t = _trigger_sec(op)
        out += [{"price": op["entry"], "title": "Entry (zone edge)", "color": "#D99A1E", "from": t},
                {"price": op["stop"], "title": "Stop", "color": "#C8473B", "from": t},
                {"price": op["target"], "title": "Target", "color": "#0B7A5A", "from": t}]
    return out


def levels(card: dict, op: dict | None) -> list[dict]:
    """Price levels, each drawn from the moment it exists ("from"), not across the whole chart."""
    if card.get("model"):
        return _smc_levels(card, op)
    r0 = _sec(card["range_open"])
    out = [{"price": card["range_high"], "title": "Range high", "color": "#0F1B2D", "dashed": True, "from": r0},
           {"price": card["range_low"], "title": "Range low", "color": "#0F1B2D", "dashed": True, "from": r0},
           {"price": card["range_mid"], "title": "50%", "color": "#5B6577", "dashed": True, "from": r0}]
    if card.get("sweep_extreme") is not None:
        out.append({"price": card["sweep_extreme"], "title": "Sweep", "color": "#2F5D9E", "dashed": True,
                    "from": _sec(card.get("sweep_open") or card["range_open"])})
    if op:
        t = _trigger_sec(op)
        out += [{"price": op["entry"], "title": "Entry", "color": "#D99A1E", "from": t},
                {"price": op["stop"], "title": "Stop", "color": "#C8473B", "from": t},
                {"price": op["target"], "title": "Target", "color": "#0B7A5A", "from": t}]
    return out


def _trigger_sec(op: dict) -> int:
    """Open time of the trigger candle. decision_time is its CLOSE, which is the next candle's open,
    so a marker placed at decision_time would sit one candle late."""
    step = {"M5": 300, "M15": 900, "H1": 3600, "H4": 14400, "D1": 86400}.get(op.get("entry_tf"), 60)
    return _sec(op["decision_time"]) - step


def markers(card: dict, op: dict | None) -> list[dict]:
    """R = range candle, S = where the sweep extreme was made (the chart finds that candle on each
    timeframe inside the sweep candle's time), T = the trigger candle."""
    if card.get("model"):
        m = card["smc"]
        out = [{"kind": "point", "time": _sec(m["line"]["start"]), "text": "S", "color": "#2F5D9E"},
               {"kind": "point", "time": _sec(m["line"]["end"]), "text": "B", "color": "#2F5D9E"},
               {"kind": "point", "time": _sec(m["zone"]["start"]), "text": "Z", "color": "#D99A1E"}]
        if op:
            out.append({"kind": "trigger", "time": _trigger_sec(op), "text": "E", "color": "#C8473B"})
        return out
    out = [{"kind": "range", "time": _sec(card["range_open"]), "text": "R", "color": "#D99A1E"}]
    if card.get("sweep_open"):
        out.append({"kind": "sweep", "time": _sec(card["sweep_open"]),
                    "end": _sec(card.get("sweep_close") or card["sweep_open"]), "text": "S", "color": "#2F5D9E"})
    if op:
        out.append({"kind": "trigger", "time": _trigger_sec(op), "text": "T", "color": "#0F1B2D"})
    return out


def merge(before: list, newer: list) -> list:
    """Snapshot candles plus newer ones (by time), without duplicates."""
    if not newer:
        return before
    last = before[-1][0] if before else 0
    return before + [c for c in newer if c[0] > last]


@lru_cache(maxsize=64)
def practice_chart(pid: str) -> dict | None:
    f = CHART_DIR / f"{pid}.json.gz"
    if not f.exists():
        return None
    with gzip.open(f, "rt") as fh:
        return json.load(fh)


def payload(card: dict, op: dict | None, before: dict, after: dict | None, tz_offset: int,
            reveal_from: str | None = None) -> dict:
    tfs = {tf: before.get(tf, []) for tf in TFS if before.get(tf)}
    out = {"pair": card["pair"], "precision": 5 if card["pair"] == "GBPUSD" else 2, "direction": card["direction"],
           "default_tf": (op or {}).get("entry_tf") or card.get("chart", {}).get("entry_tf") or "H1",
           "range_tf": card["range_tf"], "tz_offset": tz_offset, "tfs": tfs,
           "after": {tf: (after or {}).get(tf, []) for tf in tfs} if after else {},
           "levels": levels(card, op), "markers": markers(card, op),
           "marker_key": ("S swing that gets broken · B the break (MSS/BOS) · Z first candle of the zone · E candle that made the setup"
                          if card.get("model") else "R range candle · S sweep (where the extreme was made) · T trigger candle"), "focus": _sec((op or card)["decision_time"]
                                                                                 if (op or card).get("decision_time") else card["range_open"])}
    if reveal_from:
        out["reveal_from"] = _sec(reveal_from)
    return out

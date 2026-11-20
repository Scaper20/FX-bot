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


def levels(card: dict, op: dict | None) -> list[dict]:
    out = [{"price": card["range_high"], "title": "Range high", "color": "#0F1B2D", "dashed": True},
           {"price": card["range_low"], "title": "Range low", "color": "#0F1B2D", "dashed": True},
           {"price": card["range_mid"], "title": "50%", "color": "#5B6577", "dashed": True}]
    if card.get("sweep_extreme") is not None:
        out.append({"price": card["sweep_extreme"], "title": "Sweep", "color": "#2F5D9E", "dashed": True})
    if op:
        out += [{"price": op["entry"], "title": "Entry", "color": "#D99A1E"},
                {"price": op["stop"], "title": "Stop", "color": "#C8473B"},
                {"price": op["target"], "title": "Target", "color": "#0B7A5A"}]
    return out


def markers(card: dict, op: dict | None) -> list[dict]:
    out = [{"time": _sec(card["range_open"]), "text": f"range {card['range_tf']}", "color": "#D99A1E"}]
    if card.get("sweep_open"):
        out.append({"time": _sec(card["sweep_open"]), "text": "sweep", "color": "#2F5D9E"})
    if op:
        out.append({"time": _sec(op["decision_time"]), "text": "trigger", "color": "#0F1B2D"})
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
    out = {"pair": card["pair"], "precision": 5 if card["pair"] == "GBPUSD" else 2,
           "default_tf": (op or {}).get("entry_tf") or card.get("chart", {}).get("entry_tf") or "H1",
           "range_tf": card["range_tf"], "tz_offset": tz_offset, "tfs": tfs,
           "after": {tf: (after or {}).get(tf, []) for tf in tfs} if after else {},
           "levels": levels(card, op), "markers": markers(card, op), "focus": _sec((op or card)["decision_time"]
                                                                                 if (op or card).get("decision_time") else card["range_open"])}
    if reveal_from:
        out["reveal_from"] = _sec(reveal_from)
    return out

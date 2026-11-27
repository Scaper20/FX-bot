"""Zone trainer (Ore's request, 27 Nov 2026): Ore labels order blocks and breaker blocks at their first revisit,
before seeing what happened. His labels then show which zones he rates best and whether those work better.
Data: web/data/zone_training.json.gz (scripts/build_zone_training.py)."""
from __future__ import annotations

import gzip
import json
from functools import lru_cache
from pathlib import Path

from . import charts

FILE = Path(__file__).resolve().parent / "data" / "zone_training.json.gz"
LABELS = {"good": "Good zone, I'd trade it", "weak": "Weak, maybe", "invalid": "Not a valid zone"}
KINDS = {"ob_ore": "Order block (2/3-candle formation)", "ob_run": "Order block (run of candles)",
         "breaker": "Breaker block (failed order block)"}
TAGS = [
    ("clean_formation", "Clean engulfing / pin-bar formation"),
    ("took_liquidity", "Took liquidity before the move"),
    ("displacement", "Strong move away (displacement / FVG)"),
    ("with_trend", "With the higher-timeframe trend"),
    ("key_level", "At a key HTF level / zone"),
    ("discount_premium", "Buying in discount / selling in premium"),
    ("fresh", "Fresh, first return"),
    ("bad_formation", "Formation not right (wrong candles)"),
    ("too_big", "Zone too big"),
    ("too_small", "Zone too small / insignificant"),
    ("against_trend", "Against the trend"),
    ("choppy", "Choppy / ranging market"),
    ("liquidity_left", "Liquidity left in front of it"),
    ("other", "Other (see notes)"),
]
TAG_LABEL = dict(TAGS)


@lru_cache(maxsize=1)
def items() -> list[dict]:
    if not FILE.exists():
        return []
    with gzip.open(FILE, "rt") as fh:
        return json.load(fh)


def item(zid: str) -> dict | None:
    return next((z for z in items() if z["id"] == zid), None)


def labels_by_item(store) -> dict:
    return {r["item_id"]: r for r in store.list_zone_labels()}


def next_item(store) -> dict | None:
    done = labels_by_item(store)
    return next((z for z in items() if z["id"] not in done), None)


def progress(store) -> dict:
    done = labels_by_item(store)
    return {"done": sum(1 for z in items() if z["id"] in done), "total": len(items())}


def chart(z: dict, reveal: bool) -> str:
    sell = z["direction"] == "short"
    zone = z["zone"]
    col = charts.DOWN if sell else charts.UP
    boxes = [{"start": zone["start"], "end": None, "low": min(zone["near"], zone["far"]),
              "high": max(zone["near"], zone["far"]), "color": col, "label": KINDS[z["kind"]].split(" (")[0]}]
    ln = z["line"]
    segments = [{"start": ln["start"], "end": ln["end"], "price": ln["price"], "label": ln["label"],
                 "color": charts.AMBER if ln["label"] == "MSS" else charts.BLUE}]
    cs = z["candles"] + (z["after"] if reveal else [])
    levels = []
    if reveal:
        f = lambda v: charts._fmt(z["pair"], v)
        levels = [{"price": z["entry"], "label": f"Entry {f(z['entry'])}", "color": charts.INK},
                  {"price": z["stop"], "label": f"Stop {f(z['stop'])}", "color": charts.DOWN, "dash": True}]
        levels += [{"price": z["targets"][k], "label": k.replace("R", "") + "R", "color": charts.UP, "dash": True}
                   for k in ("R1", "R2", "R3")]
    shade = []
    if z["kind"] == "breaker":                      # the candle that closed through the old block
        shade = [{"start": z["made"], "end": z["made"], "color": charts.DOWN if not sell else charts.UP}]
        segments[0]["label"] = ln["label"] + " that made the old block"
    title = f"{z['pair']} {z['tf']} {KINDS[z['kind']]}"
    return charts.candles_svg(cs, levels=levels, boxes=boxes, segments=segments, shade=shade, pair=z["pair"],
                              title=title, after_from=z["touch"] if reveal else None, height=340)


def _group(rows: list[dict]) -> dict:
    out = {"n": len(rows)}
    for r in ("R1", "R2", "R3"):
        vals = [x["outcome"][r] for x in rows if x["outcome"].get(r) is not None]
        out[f"avg_{r}"] = sum(vals) / len(vals) if vals else None
        out[f"hit_{r}"] = sum(v > 0 for v in vals) / len(vals) if vals else None
    return out


def stats(store) -> dict:
    lab = labels_by_item(store)
    zs = items()
    done = [z for z in zs if z["id"] in lab]
    by_label = {k: _group([z for z in done if lab[z["id"]]["label"] == k]) for k in LABELS}
    by_kind = {}
    for kind in KINDS:
        by_kind[kind] = {"all": _group([z for z in zs if z["kind"] == kind]),
                         **{k: _group([z for z in done if z["kind"] == kind and lab[z["id"]]["label"] == k])
                            for k in LABELS}}
    tags = []
    for key, text in TAGS:
        rows = [z for z in done if key in (lab[z["id"]].get("tags") or [])]
        if rows:
            tags.append({"tag": text, **_group(rows),
                         "good_share": sum(lab[z["id"]]["label"] == "good" for z in rows) / len(rows)})
    feats = []
    for key, text in (("with_htf", "With D1 + H4 trend"), ("took_liquidity", "Took liquidity before the move"),
                      ("left_fvg", "Left an FVG (displacement)")):
        row = {"feature": text}
        for k in LABELS:
            rs = [z for z in done if lab[z["id"]]["label"] == k]
            row[k] = sum(bool(z["features"][key]) for z in rs) / len(rs) if rs else None
        feats.append(row)
    size = {k: (sum(z["features"]["size_atr"] for z in done if lab[z["id"]]["label"] == k) /
                max(1, sum(1 for z in done if lab[z["id"]]["label"] == k))) if any(lab[z["id"]]["label"] == k for z in done)
            else None for k in LABELS}
    return {"all": _group(zs), "done": len(done), "total": len(zs), "by_label": by_label, "by_kind": by_kind,
            "tags": tags, "features": feats, "size": size}

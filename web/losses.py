"""Losses to review (Ore's request, 27 Nov 2026): every losing trade from the corrected live-scanner replay of
2025 - 27 Nov 2026, shown in full (before and after), grouped by strategy and by what happened, with Ore's
feedback on each. Data: web/data/loss_review.json.gz + web/data/loss_charts/ (scripts/build_loss_review.py)."""
from __future__ import annotations

import gzip
import json
from collections import Counter
from functools import lru_cache
from pathlib import Path

import pandas as pd

from engine.strategies import STRATEGIES

DATA = Path(__file__).resolve().parent / "data"
FILE = DATA / "loss_review.json.gz"
CHARTS = DATA / "loss_charts"

CATS = {
    "A": "Went +1R or more our way, then reversed to the stop",
    "B": "Stopped out, then price went on to our target",
    "C": "Stopped within 30 minutes, never moved our way",
    "D": "Never really worked (under +0.5R)",
    "E": "Went +0.5R to +1R our way, then reversed",
}
VERDICTS = {
    "valid": "Valid setup, normal loss (nothing to change)",
    "managed": "Valid setup, but I'd have managed it differently",
    "invalid": "Not a valid setup: I would not have taken it",
    "unsure": "Not sure",
}
REASONS = [
    ("against_htf", "Against the higher-timeframe direction"),
    ("htf_level", "Ran into a higher-timeframe level or zone"),
    ("news", "News or a high-volatility candle"),
    ("stop_tight", "Stop too tight (inside normal noise)"),
    ("stop_place", "Stop in the wrong place (should be beyond another swing)"),
    ("entry_early", "Entered too early (no confirmation yet)"),
    ("entry_late", "Entered too late (move already done)"),
    ("zone_invalid", "Zone / POI not valid"),
    ("no_liquidity", "Liquidity not taken first"),
    ("structure", "Structure misread (no real MSS / BOS)"),
    ("target_far", "Target too far"),
    ("should_bank", "Should have taken profit or moved the stop"),
    ("session", "Wrong session / time of day"),
    ("choppy", "Choppy / ranging market"),
    ("costs", "Spread too big for the stop"),
    ("other", "Other (see notes)"),
]
REASON_LABEL = dict(REASONS)


@lru_cache(maxsize=1)
def items() -> list[dict]:
    if not FILE.exists():
        return []
    with gzip.open(FILE, "rt") as fh:
        return json.load(fh)


def item(lid: str) -> dict | None:
    return next((x for x in items() if x["id"] == lid), None)


@lru_cache(maxsize=64)
def chart(lid: str) -> dict | None:
    f = CHARTS / f"{lid}.json.gz"
    if not f.exists():
        return None
    with gzip.open(f, "rt") as fh:
        return json.load(fh)


def feedback(store) -> dict:
    return {r["item_id"]: r for r in store.list_loss_reviews()}


def filtered(fb: dict, strategy: str = "", cat: str = "", pair: str = "", status: str = "") -> list[dict]:
    out = []
    for x in items():
        if (strategy and x["strategy"] != strategy) or (cat and x["cat"] != cat) or (pair and x["pair"] != pair):
            continue
        if status == "todo" and x["id"] in fb or status == "done" and x["id"] not in fb:
            continue
        out.append(x)
    return out


def neighbours(lst: list[dict], lid: str, fb: dict) -> dict:
    ids = [x["id"] for x in lst]
    i = ids.index(lid) if lid in ids else -1
    nxt_todo = next((x["id"] for x in lst[i + 1:] + lst[:max(i, 0)] if x["id"] not in fb and x["id"] != lid), None)
    return {"prev": ids[i - 1] if i > 0 else None, "next": ids[i + 1] if 0 <= i < len(ids) - 1 else None,
            "next_todo": nxt_todo, "pos": i + 1, "count": len(ids)}


def story(x: dict) -> list[str]:
    """What happened, in plain words (GMT+0, the same as MT5)."""
    f = x["facts"]
    t = lambda s: pd.Timestamp(s).tz_convert("UTC").strftime("%a %d %b %Y %H:%M")
    dur = f["mins"]
    dur_txt = f"{dur} minutes" if dur < 120 else f"{dur / 60:.1f} hours" if dur < 2880 else f"{dur / 1440:.1f} days"
    lines = [
        f"Shown {t(x['shown'])}; the limit order filled {t(x['fill'])}"
        + (f", {f['wait_h']:.1f} hours after the setup formed." if f["wait_h"] >= 0.1 else ", straight away."),
        f"Best point after the fill: {'+' if f['mfe_R'] >= 0 else ''}{f['mfe_R']:.1f}R in our favour. "
        f"Stopped out {t(x['exit'])}, {dur_txt} after the fill.",
        ("After the stop, price went on to reach our target." if f["tp_after_stop"]
         else "After the stop, price did not reach our target."),
    ]
    if f.get("beyond_stop_R") is not None:
        lines.append(f"In the hour after the stop, price went {f['beyond_stop_R']:.1f}R past the stop level"
                     + (" (a quick poke, then back)." if f["beyond_stop_R"] < 0.3 else "."))
    if f.get("stop_atr") is not None:
        lines.append(f"Stop distance: {f['stop_atr']:.2f} × the average H1 candle range (ATR 14); the spread was "
                     f"{100 * f['spread_share']:.0f}% of the risk.")
    lines.append(f"Session at the fill: {f['session']}. D1 trend {'with' if f['d1_with'] else 'against'} the trade, "
                 f"H4 trend {'with' if f['h4_with'] else 'against'} it.")
    return lines


def overview(fb: dict) -> dict:
    """Counts per strategy x category, and progress."""
    grid = {}
    for x in items():
        g = grid.setdefault(x["strategy"], {"total": 0, "done": 0, **{c: 0 for c in CATS}})
        g["total"] += 1
        g[x["cat"]] += 1
        g["done"] += x["id"] in fb
    order = [s for s in STRATEGIES if s in grid]
    return {"grid": [(s, grid[s]) for s in order], "total": len(items()), "done": sum(1 for x in items() if x["id"] in fb),
            "cat_totals": Counter(x["cat"] for x in items())}


def stats(fb: dict) -> dict:
    """What Ore's feedback shows: verdicts and reasons by strategy and by category."""
    rows = [(x, fb[x["id"]]) for x in items() if x["id"] in fb]
    out = {"n": len(rows), "verdicts": Counter(r["verdict"] for _, r in rows), "by_strategy": {}, "by_cat": {},
           "reasons": Counter(t for _, r in rows for t in r.get("reasons") or [])}
    for key, fn in (("by_strategy", lambda x: x["strategy"]), ("by_cat", lambda x: x["cat"])):
        for x, r in rows:
            g = out[key].setdefault(fn(x), {"n": 0, "verdicts": Counter(), "reasons": Counter()})
            g["n"] += 1
            g["verdicts"][r["verdict"]] += 1
            g["reasons"].update(r.get("reasons") or [])
    out["invalid_R"] = round(sum(x["R"] for x, r in rows if r["verdict"] == "invalid"), 1)
    return out

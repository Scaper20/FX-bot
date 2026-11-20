"""Build the practice set: past setups shown exactly as the live scanner would have shown them.

    python scripts/build_practice.py --n 400

For each sampled setup (Nov 2021 - Dec 2024, Ore's rules applied in the backtest), the live scan
runs at the trigger time on replayed data, so the card contains only what was knowable then.
Outcomes are tracked afterwards on 1-minute data and stored separately (shown only after review).
2025-2026 is never read: data is cut at 2025-01-01 before anything else happens.
Writes web/data/practice.json.gz.
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.pattern_stats import ore_rules  # noqa: E402
from engine import config as K  # noqa: E402
from engine.candles import clean, load_m1_csv  # noqa: E402
from engine.feeds.replay import ReplayFeed  # noqa: E402
from engine.live import ENGINE_VERSION, TF_BARS, all_tf_candles, compact_candles, scan_pair, setup_id, track_card_options  # noqa: E402
from engine.setups import Market  # noqa: E402

CUTOFF = pd.Timestamp("2025-01-01", tz="UTC")
OUT = ROOT / "web" / "data" / "practice.json.gz"
CHARTS = ROOT / "web" / "data" / "practice_charts"
AFTER_BARS = {"D1": 10, "H4": 30, "H1": 72, "M15": 160, "M5": 300}


def candidates() -> pd.DataFrame:
    parts = []
    for per in ("design", "check"):
        d = pd.read_csv(ROOT / "backtest" / "out" / f"trades_{per}.csv", low_memory=False,
                        parse_dates=["decision_time", "range_open"])
        parts.append(d[ore_rules(d)])
    t = pd.concat(parts, ignore_index=True)
    t = t[t["decision_time"] < CUTOFF - pd.Timedelta("40D")]
    g = t.groupby(["pair", "range_tf", "range_open", "k", "direction"], as_index=False)["decision_time"].min()
    return g


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--seed", type=int, default=20)
    a = ap.parse_args()
    cand = candidates()
    rng = np.random.default_rng(a.seed)
    per_pair = a.n // len(K.PAIRS)
    picks = pd.concat([g.sample(min(len(g), per_pair + 40), random_state=a.seed) for _, g in cand.groupby("pair")])
    m1 = {}
    for p in K.PAIRS:
        d, _ = clean(load_m1_csv(ROOT / K.PAIRS[p]["file"]))
        m1[p] = d[d.index < CUTOFF]                       # nothing from 2025 onwards exists past this line
    feed = ReplayFeed(m1)
    items, t0 = {p: [] for p in K.PAIRS}, time.time()
    for _, r in picks.iterrows():
        pair = r["pair"]
        if len(items[pair]) >= per_pair:
            continue
        now = pd.Timestamp(r["decision_time"])
        mkt = Market.from_frames(feed.frames(pair, now), now)
        sid = setup_id(pair, r["range_tf"], pd.Timestamp(r["range_open"]).value, int(r["k"]), r["direction"] == "long")
        card = next((c for c in scan_pair(mkt, pair, K.PAIRS[pair]["spread"]) if c["id"] == sid), None)
        if not card or card["state"] != "ready" or not card["options"]:
            continue
        card["options"] = card["options"][:8]
        card["chart"].pop("tfs", None)
        for op in card["options"]:
            op["stats"] = None                              # blind: no history in practice
        part = m1[pair][(m1[pair].index >= now - pd.Timedelta("130D")) & (m1[pair].index < now + pd.Timedelta("45D"))]
        fut = Market(part, data_end=min(now + pd.Timedelta("45D"), CUTOFF))
        outcome = track_card_options(fut, card, K.PAIRS[pair]["spread"])
        before = all_tf_candles(mkt)                          # closed candles at the trigger, all timeframes
        after = {}
        for tf, n in AFTER_BARS.items():
            last = before[tf][-1][0] if before[tf] else 0
            df = fut.frames[tf]
            later = df[df.index.as_unit("s").asi8 > last]
            after[tf] = compact_candles(later.head(n), n)
        CHARTS.mkdir(parents=True, exist_ok=True)
        with gzip.open(CHARTS / f"P-{sid}.json.gz", "wt") as fh:
            json.dump({"before": before, "after": after}, fh, separators=(",", ":"))
        etf = card["chart"]["entry_tf"]
        edf = fut.frames[etf]
        after = edf[edf.index >= now].head(96)
        items[pair].append({
            "id": "P-" + sid, "engine": ENGINE_VERSION, "card": card, "outcome": outcome,
            "after": [[t.isoformat(), round(float(x.open), 5), round(float(x.high), 5), round(float(x.low), 5),
                       round(float(x.close), 5)] for t, x in after.iterrows()],
        })
        n = sum(len(v) for v in items.values())
        if n % 50 == 0:
            print(f"{n} items, {time.time() - t0:.0f}s")
    allitems = [it for v in items.values() for it in v]
    order = rng.permutation(len(allitems))
    allitems = [allitems[i] for i in order]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUT, "wt") as f:
        json.dump(allitems, f, separators=(",", ":"))
    filled = sum(1 for it in allitems for s in it["outcome"].values() if s["status"] == "filled")
    print(f"wrote {len(allitems)} practice setups ({filled} filled options) to {OUT.relative_to(ROOT)}, "
          f"{OUT.stat().st_size / 1e6:.1f} MB, {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

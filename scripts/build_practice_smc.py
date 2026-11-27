"""Practice setups for the smart-money strategies (order block, IRL/ERL, Toni, Lingard, Ore's model).

    python scripts/build_practice_smc.py --per 40      -> appended to web/data/practice.json.gz (+ chart files)

Same method as the CRT practice (scripts/build_practice.py): candidate decision times come from the shared rules
(engine/smc_live._setups on the full history), then the LIVE scanner (scan_smc_pair) runs at that moment on replayed
data, so the card holds only what was knowable then (bias, structure, zones). Cards the live scanner would not have
shown (e.g. bias disagrees) are skipped. Outcomes are tracked afterwards on 1-minute data and revealed only after a
review. History numbers are removed from the card (blind). Re-running replaces the SMC items, keeps the CRT ones.
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
from engine import config as K  # noqa: E402
from engine.candles import clean, load_m1_csv  # noqa: E402
from engine.feeds.replay import ReplayFeed  # noqa: E402
from engine.live import ENGINE_VERSION, all_tf_candles, compact_candles, track_card_options  # noqa: E402
from engine.setups import Market  # noqa: E402
from engine.smc_live import MODELS, _ohlc, _setups, scan_smc_pair  # noqa: E402

OUT = ROOT / "web" / "data" / "practice.json.gz"
CHARTS = ROOT / "web" / "data" / "practice_charts"
AFTER_BARS = {"D1": 10, "H4": 30, "H1": 72, "M15": 160, "M5": 300}
START = pd.Timestamp("2022-03-01", tz="UTC")       # room for the replay's look-back


def candidates(full: Market, key: str, end: pd.Timestamp) -> list[pd.Timestamp]:
    F = full.frames[MODELS[key]["tf"]]
    o, h, l, c = _ohlc(F)
    to = F.index.as_unit("ns").asi8
    tc = pd.DatetimeIndex(F["close_time_utc"])
    ss, _ = _setups(key, o, h, l, c, full, to)
    ts = sorted({tc[s["decision"]] for s in ss})
    return [t for t in ts if START <= t < end]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per", type=int, default=40, help="setups per strategy (split across the pairs)")
    ap.add_argument("--seed", type=int, default=26)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    m1 = {p: clean(load_m1_csv(ROOT / K.PAIRS[p]["file"]))[0] for p in K.PAIRS}
    feed = ReplayFeed(m1)
    items, t0 = [], time.time()
    for pair in K.PAIRS:
        end = m1[pair].index[-1] - pd.Timedelta("45D")
        full = Market(m1[pair], data_end=m1[pair].index[-1] + pd.Timedelta("1min"))
        sp = K.PAIRS[pair]["spread"]
        for key in MODELS:
            want, got, tried = a.per // len(K.PAIRS), 0, 0
            cand = candidates(full, key, end)
            for i in rng.permutation(len(cand)):
                if got >= want:
                    break
                now = cand[int(i)]
                tried += 1
                mkt = Market.from_frames(feed.frames(pair, now), now)
                card = next((c for c in scan_smc_pair(mkt, pair, sp, only=(key,))
                             if pd.Timestamp(c["decision_time"]) == now), None)
                if not card:
                    continue
                card["chart"].pop("tfs", None)
                for op in card["options"]:
                    op["stats"] = None                       # blind: no history in practice
                part = m1[pair][(m1[pair].index >= now - pd.Timedelta("130D")) & (m1[pair].index < now + pd.Timedelta("45D"))]
                fut = Market(part, data_end=now + pd.Timedelta("45D"))
                outcome = track_card_options(fut, card, sp)
                before = all_tf_candles(mkt)
                after = {}
                for tf, n in AFTER_BARS.items():
                    last = before[tf][-1][0] if before.get(tf) else 0
                    df = fut.frames[tf]
                    after[tf] = compact_candles(df[df.index.as_unit("s").asi8 > last].head(n), n)
                pid = "P-" + card["id"]
                CHARTS.mkdir(parents=True, exist_ok=True)
                with gzip.open(CHARTS / f"{pid}.json.gz", "wt") as fh:
                    json.dump({"before": before, "after": after}, fh, separators=(",", ":"))
                edf = fut.frames[card["chart"]["entry_tf"]]
                later = edf[edf.index >= now].head(96)
                items.append({"id": pid, "engine": ENGINE_VERSION, "strategy": key, "card": card, "outcome": outcome,
                              "after": [[t.isoformat(), round(float(x.open), 5), round(float(x.high), 5),
                                         round(float(x.low), 5), round(float(x.close), 5)] for t, x in later.iterrows()]})
                got += 1
            print(f"{pair} {key}: {got} items from {tried} tried ({len(cand)} candidates), {time.time() - t0:.0f}s",
                  flush=True)
    old = json.load(gzip.open(OUT, "rt")) if OUT.exists() else []
    keep = [it for it in old if (it.get("strategy") or it["card"].get("strategy") or "crt") == "crt"]
    order = rng.permutation(len(items))
    with gzip.open(OUT, "wt") as f:
        json.dump(keep + [items[i] for i in order], f, separators=(",", ":"))
    ids = {it["id"] for it in items}
    tags = tuple(f"-{k.upper()}-" for k in MODELS)
    for f in CHARTS.glob("P-*.json.gz"):                  # chart files of SMC items from earlier runs
        pid = f.name[:-len(".json.gz")]
        if any(t in pid for t in tags) and pid not in ids:
            f.unlink()
    filled = sum(1 for it in items for s in it["outcome"].values() if s["status"] == "filled")
    print(f"wrote {len(keep)} CRT + {len(items)} SMC practice setups ({filled} filled) to {OUT}, "
          f"{OUT.stat().st_size / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

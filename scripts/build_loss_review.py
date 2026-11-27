"""Losses to review (Ore's request, 27 Nov 2026): every losing trade from the corrected live-scanner replay of
2025 - 27 Nov 2026, with the card the scanner showed, measurements of what happened, and chart candles from
before the setup to after the exit.

    python scripts/build_loss_review.py --src <replay dir>

<replay dir> holds the replay outputs (as made on 27 Nov 2026): trades2.json (scored setups), out2/*.json (cards at
first show), {PAIR}_{H1,M15,M5}.pkl (candles, weekend quotes dropped) and {PAIR}_D1long.pkl (daily history).
Writes web/data/loss_review.json.gz and web/data/loss_charts/<id>.json.gz.
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine import config as K  # noqa: E402
from engine.candles import resample_from  # noqa: E402
from engine.live import TF_BARS, compact_candles  # noqa: E402
from engine.smc_structure import external_structure  # noqa: E402

OUT = ROOT / "web" / "data" / "loss_review.json.gz"
CHARTS = ROOT / "web" / "data" / "loss_charts"
AFTER = {"M5": ("8h", 700), "M15": ("1D", 500), "H1": ("3D", 300), "H4": ("8D", 120), "D1": ("15D", 30)}
HOLD = {"crt": "3D", "smc_ob": "5D", "irl_erl": "5D", "toni": "5D", "lingard": "10D", "ore_poi": "5D"}
CATS = {
    "A": "Went +1R or more our way, then reversed to the stop",
    "B": "Stopped out, then price went on to our target",
    "C": "Stopped within 30 minutes, never moved our way",
    "D": "Never really worked (under +0.5R), slower loss",
    "E": "Went +0.5R to +1R our way, then reversed",
}


def trend_fn(df: pd.DataFrame):
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    tr, cur, k = np.zeros(len(c), int), 0, 0
    ev = external_structure(o, h, l, c, "close")
    for i in range(len(c)):
        while k < len(ev) and ev[k]["j"] <= i:
            cur, k = ev[k]["dir"], k + 1
        tr[i] = cur
    step = df.index.to_series().diff().median()
    close = (df.index + step).as_unit("ns").asi8
    return lambda t: int(tr[max(0, int(np.searchsorted(close, t, side="right")) - 1)])


def session(t: pd.Timestamp) -> str:
    lt, nt = t.tz_convert("Europe/London"), t.tz_convert("America/New_York")
    ldn, ny = 7 <= lt.hour < 16, 8 <= nt.hour < 17
    return "London + New York overlap" if ldn and ny else "London" if ldn else "New York" if ny else "Asian session / late"


def category(mfe: float, tp_after: bool, mins: float) -> str:
    if mfe >= 1.0:
        return "A"
    if tp_after:
        return "B"
    if mins <= 30 and mfe < 0.3:
        return "C"
    return "D" if mfe < 0.5 else "E"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    src = Path(ap.parse_args().src)
    d = pd.read_json(src / "trades2.json")
    losses = d[d.rules & d.actionable & (d.status == "filled") & (d.state != "open") & (d.R < -0.05)]
    cards = {}
    for f in sorted(glob.glob(str(src / "out2" / "*.json"))):
        for v in json.load(open(f)):
            c = v["card"]
            if c["id"] not in cards or v["first_seen"] < cards[c["id"]][0]:
                cards[c["id"]] = (v["first_seen"], c)
    CHARTS.mkdir(parents=True, exist_ok=True)
    for old in CHARTS.glob("*.json.gz"):
        old.unlink()
    items = []
    for pair, g in losses.groupby("pair"):
        sp = K.PAIRS[pair]["spread"]
        raw = {tf: pd.read_pickle(src / f"{pair}_{tf}.pkl") for tf in ("H1", "M15", "M5")}
        raw["H4"] = resample_from(raw["H1"], "H4", K.DAY_CLOSE)[["open", "high", "low", "close"]]
        raw["D1"] = pd.read_pickle(src / f"{pair}_D1long.pkl")
        m5 = raw["M5"]
        t5 = m5.index.as_unit("ns").asi8
        H, L = m5["high"].to_numpy(float), m5["low"].to_numpy(float)
        h1 = raw["H1"]
        tr = np.maximum(h1["high"] - h1["low"], np.maximum((h1["high"] - h1["close"].shift()).abs(),
                                                           (h1["low"] - h1["close"].shift()).abs()))
        atr, atr_t = tr.rolling(14).mean().to_numpy(), h1.index.as_unit("ns").asi8
        d1t, h4t = trend_fn(raw["D1"]), trend_fn(raw["H4"])
        for r in g.itertuples():
            seen, card = cards[r.id]
            seen = pd.Timestamp(seen)
            op = next(o for o in card["options"] if o["id"] == r.option)
            s = 1 if r.direction == "long" else -1
            e, st, tp = float(op["entry"]), float(op["stop"]), float(op["target"])
            risk = abs(e - st)
            fill, ex, dec = pd.Timestamp(r.fill), pd.Timestamp(r.exit), pd.Timestamp(r.decision)
            a = int(np.searchsorted(t5, fill.value - 5 * 60 * 10**9))
            b = int(np.searchsorted(t5, ex.value, side="right"))
            mfe = float(((H[a:b].max() - e) if s == 1 else (e - L[a:b].min())) / risk) if b > a else 0.0
            hold_end = int(np.searchsorted(t5, (fill + pd.Timedelta(HOLD[r.strategy])).value))
            tp_after = bool(((H[b:hold_end] >= tp) if s == 1 else (L[b:hold_end] <= tp)).any())
            nh = int(np.searchsorted(t5, (ex + pd.Timedelta("1h")).value))
            beyond = float(((st - L[b:nh].min()) if s == 1 else (H[b:nh].max() - st)) / risk) if nh > b else None
            k = max(0, int(np.searchsorted(atr_t, fill.value)) - 1)
            mins = (ex - fill).total_seconds() / 60
            cat = category(mfe, tp_after, mins)
            lid = "L-" + card["id"]
            for o in card["options"]:
                o["stats"] = None
            before, after = {}, {}
            for tf, n in TF_BARS.items():
                df = raw[tf]
                step = df.index.to_series().diff().median()
                closed = df[df.index + step <= seen]
                before[tf] = compact_candles(closed, n)
                last = closed.index[-1] if len(closed) else seen
                span, cap = AFTER[tf]
                later = df[(df.index > last) & (df.index < ex + pd.Timedelta(span))]
                after[tf] = compact_candles(later.head(cap), cap)
            with gzip.open(CHARTS / f"{lid}.json.gz", "wt") as fh:
                json.dump({"before": before, "after": after}, fh, separators=(",", ":"))
            items.append({
                "id": lid, "pair": pair, "strategy": r.strategy, "direction": r.direction, "tf": r.tf,
                "shown": seen.isoformat(), "decision": dec.isoformat(), "fill": fill.isoformat(), "exit": ex.isoformat(),
                "entry": e, "stop": st, "target": tp, "rr": float(op["rr"]), "R": round(float(r.R), 2), "option": op["id"],
                "cat": cat, "facts": {
                    "mfe_R": round(mfe, 2), "mins": round(mins), "wait_h": round((fill - dec).total_seconds() / 3600, 1),
                    "stop_atr": round(float(risk / atr[k]), 2) if atr[k] and not np.isnan(atr[k]) else None,
                    "spread_share": round(sp / risk, 3), "session": session(fill),
                    "d1_with": d1t(dec.value) == s, "h4_with": h4t(dec.value) == s,
                    "tp_after_stop": tp_after, "beyond_stop_R": None if beyond is None else round(beyond, 2)},
                "card": card})
    items.sort(key=lambda x: x["shown"])
    with gzip.open(OUT, "wt") as fh:
        json.dump(items, fh, separators=(",", ":"))
    by = pd.Series([i["strategy"] for i in items]).value_counts().to_dict()
    print(f"{len(items)} losses -> {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1e6:.1f} MB), charts "
          f"{sum(f.stat().st_size for f in CHARTS.glob('*')) / 1e6:.1f} MB; by strategy {by}; "
          f"by category {pd.Series([i['cat'] for i in items]).value_counts().sort_index().to_dict()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

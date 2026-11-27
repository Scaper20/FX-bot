"""Replay the LIVE scanner over a past period, as if it had been running (Ore's request, 27 Nov 2026).

Every 15 minutes while the forex market is open, the live scanner (engine.live.scan_pair for CRT and
engine.smc_live.scan_smc_pair for the smart-money strategies) runs on only the candles that existed at that moment,
in the amounts the live feed returns (last 2,500 H1, 1,500 M15 and 2,500 M5 candles), with the long D1 history the
live scanner keeps. Each setup is recorded the first time it shows; then it is scored with the live 5-minute tracker.

    python -m backtest.replay_live --start 2025-01-01 --end 2026-11-18
    python -m backtest.replay_live --start 2026-11-23 --end 2026-11-28 --twelvedata   # recent days (needs the key)

Data: Dukascopy 1-minute files in data/ (to 18 Nov 2026). --twelvedata appends the live feed's candles after that
(TWELVEDATA_API_KEY in the environment; ~6 credits). Writes backtest/out/replay_setups.csv and prints totals by
year/strategy, month and week. "Orders" = setups matching the rules while the limit could still be placed; "trades"
= orders that filled. R is after Ore's spreads.
"""
from __future__ import annotations

import argparse
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine import config as K  # noqa: E402
from engine.calendar import market_open, open_mask  # noqa: E402
from engine.candles import clean, load_m1_csv, resample  # noqa: E402
from engine.live import scan_pair, track_card_options  # noqa: E402
from engine.setups import Market  # noqa: E402
from engine.smc_live import scan_smc_pair  # noqa: E402
from engine.strategies import strategy_of  # noqa: E402
from web.service import actionable  # noqa: E402
from backtest.patterns import EXTRA, MARKETS  # noqa: E402

MKT = {**MARKETS, **EXTRA, **K.PAIRS}                 # data file and spread per pair (EUR/USD and silver from the fresh set)

OUT = ROOT / "backtest" / "out" / "replay_setups.csv"
LIVE_N = {"H1": 2500, "M15": 1500, "M5": 2500}
_DATA: dict = {}


def load(pair: str, start: pd.Timestamp, twelvedata: bool) -> dict:
    m1 = clean(load_m1_csv(ROOT / MKT[pair]["file"]))[0]
    cut = m1.index[-1].floor("1h")
    frames = {tf: resample(m1[(m1.index >= start - pd.Timedelta("200D")) & (m1.index < cut)], tf, "utc0")
              [["open", "high", "low", "close"]] for tf in LIVE_N}
    d1 = resample(m1[m1.index < cut.floor("1D")], "D1", "utc0")[["open", "high", "low", "close"]]
    if twelvedata:
        from engine.feeds.twelvedata import fetch
        for tf in LIVE_N:
            b = fetch(pair, tf, outputsize=5000)
            frames[tf] = pd.concat([frames[tf], b[b.index >= cut]]).sort_index()
    for tf, df in frames.items():
        frames[tf] = df[~df.index.duplicated(keep="first") & open_mask(df.index)]
    return {"frames": frames, "d1": d1}


def _init(data):
    _DATA.update(data)


def _chunk(args):
    pair, a, b, only = args
    raw, d1 = _DATA[pair]["frames"], _DATA[pair]["d1"]
    idx = {tf: df.index.as_unit("ns").asi8 for tf, df in raw.items()}
    end = raw["M5"].index[-1] + pd.Timedelta("5min")
    sp = MKT[pair]["spread"]
    seen = {}
    for t in pd.date_range(a, min(b, end), freq="15min", inclusive="left"):
        if not market_open(t):
            continue
        fr = {}
        for tf, df in raw.items():
            k = int(np.searchsorted(idx[tf], t.value, side="left"))
            fr[tf] = df.iloc[max(0, k - LIVE_N[tf]):k]
        mkt = Market.from_frames({**fr, "D1_hist": d1}, t)
        crt = [] if only and "crt" not in only else [c for c in scan_pair(mkt, pair, sp) if c["state"] == "ready"]
        for c in crt + scan_smc_pair(mkt, pair, sp, only=tuple(x for x in only if x != "crt") or None if only else None):
            if c["id"] in seen:
                continue
            st = track_card_options(mkt, c, sp)
            acts = [op["id"] for op in c["options"] if actionable(op, st.get(op["id"], {}), t)]
            c.pop("chart", None)
            seen[c["id"]] = {"first_seen": t, "card": c, "actionable": acts}
    return pair, list(seen.values())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--twelvedata", action="store_true", help="append the live feed's candles after the Dukascopy data")
    ap.add_argument("--pairs", default="GBPUSD,XAUUSD", help="comma list; EURUSD and XAGUSD use the fresh-market data")
    ap.add_argument("--only", default="", help="comma list of strategies to scan (default all)")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    start, end = pd.Timestamp(a.start, tz="UTC"), pd.Timestamp(a.end, tz="UTC")
    pairs = [x for x in a.pairs.split(",") if x]
    only = tuple(x for x in a.only.split(",") if x)
    data = {p: load(p, start, a.twelvedata) for p in pairs}
    months = list(pd.date_range(start.floor("D"), end, freq="MS")) or [start]
    edges = sorted({start, *[m for m in months if m > start], end})
    jobs = [(p, x, y, only) for p in pairs for x, y in zip(edges[:-1], edges[1:])]
    with Pool(a.jobs, initializer=_init, initargs=(data,)) as pool:
        found = pool.map(_chunk, jobs)
    rows = []
    for pair in pairs:
        seen = {}
        for p, vals in found:
            if p == pair:
                for v in vals:
                    if v["card"]["id"] not in seen or v["first_seen"] < seen[v["card"]["id"]]["first_seen"]:
                        seen[v["card"]["id"]] = v
        raw = data[pair]["frames"]
        final = Market.from_frames(raw, raw["M5"].index[-1] + pd.Timedelta("5min"))
        sp = MKT[pair]["spread"]
        for v in seen.values():
            c = v["card"]
            out = track_card_options(final, c, sp)
            pick = c["best"] if c["best"] in v["actionable"] else (v["actionable"][0] if v["actionable"] else c["best"])
            op, o = next(x for x in c["options"] if x["id"] == pick), out[pick]
            rows.append({"first_seen": v["first_seen"], "pair": pair, "strategy": strategy_of(c), "tf": c.get("range_tf"),
                         "direction": c["direction"], "matches_rules": bool(c["recommended"]),
                         "order_placed": bool(c["recommended"] and v["actionable"]), "option": pick,
                         "entry": op["entry"], "stop": op["stop"], "target": op["target"], "rr": op["rr"],
                         "status": o["status"], "state": o["state"], "R": o["R"], "fill_time": o["fill_time"],
                         "exit_time": o["exit_time"], "id": c["id"]})
    d = pd.DataFrame(rows).sort_values("first_seen")
    out_path = Path(a.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    d.to_csv(out_path, index=False)
    o = d[d["order_placed"]].copy()
    o["filled"] = o["status"] == "filled"
    t = pd.to_datetime(o["first_seen"], utc=True)
    o["year"], o["month"] = t.dt.year, t.dt.strftime("%Y-%m")
    o["week"] = (t.dt.tz_localize(None).dt.normalize() - pd.to_timedelta(t.dt.dayofweek, unit="D")).dt.strftime("%Y-%m-%d")
    f = o[o["filled"]]

    def table(by):
        g = o.groupby(by).size().rename("orders").to_frame()
        g["trades"] = f.groupby(by).size()
        g["won"] = f[f["R"] > 0.05].groupby(by).size()
        g["lost"] = f[f["R"] < -0.05].groupby(by).size()
        g["net_R"] = f.groupby(by)["R"].sum().round(1)
        return g.fillna(0)
    print(f"{len(d)} setups shown, {len(o)} orders placed, {len(f)} trades -> {out_path}\n")
    print(table(["year", "strategy"]).to_string(), "\n")
    print(table("month").to_string(), "\n")
    print(table("week").to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

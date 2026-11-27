"""Spec v25 example charts: random trades from the top rows, with the HTF POI that was tapped first.

    python -m backtest.chart_v25      -> docs/smc_review/v25_*.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.ob_v21 import ohlc  # noqa: E402
from backtest.ore_v25 import OUT, TAP_WINDOW, TF_SEC, entry_rows, poi_mask  # noqa: E402
from engine.smc_poi import first_touch, htf_zones  # noqa: E402
from backtest.patterns import MAIN, MARKETS  # noqa: E402
from backtest.smc_draw import AMBER, CORAL, GREEN, draw, structure_layers  # noqa: E402
from engine.candles import clean, load_m1_csv, resample  # noqa: E402
from engine.smc_structure import external_structure  # noqa: E402

DOCS = ROOT / "docs" / "smc_review"


def main() -> int:
    grid = pd.read_csv(OUT / "v25_grid.csv")
    top = grid[(grid["poi"] != "no POI") & (grid["n"] >= 30)].sort_values("t", ascending=False).head(3)
    d = pd.concat([pd.read_csv(OUT / f"v25_{p}.csv") for p in MAIN], ignore_index=True)
    cache = {}
    rng = np.random.default_rng(25)
    for rank, row in enumerate(top.itertuples(), 1):
        x = entry_rows(d, row.entry)
        x = x[(x["tf"] == row.tf) & (x["mode"] == row.mode) & (x["target"] == row.target)]
        x = x[x["d1"]] if row.bias == "D1 trend" else x
        x = x[poi_mask(x, row.htf, row.poi)]
        for k in rng.choice(len(x), min(2, len(x)), replace=False):
            r = x.iloc[int(k)]
            pair, tf = r["pair"], r["tf"]
            if pair not in cache:
                m1, _ = clean(load_m1_csv(ROOT / MARKETS[pair]["file"]))
                F = {t: resample(m1, t, "utc0") for t in ("D1", "H4", "H1", "M15", "M5")}
                Z = pd.concat([htf_zones(F["H4"], "H4"), htf_zones(F["D1"], "D1")], ignore_index=True)
                Z["touch"] = first_touch(Z, F["H1"])
                cache[pair] = (F, Z)
            F, Z = cache[pair]
            E = F[tf]
            o, h, l, c = ohlc(E)
            pos = {t: i for i, t in enumerate(E.index.as_unit("ns").asi8)}
            ev = external_structure(o, h, l, c, r["mode"])
            dec, topi = pos[int(r["dec_open"])], pos[int(r["top_open"])]
            sell = r["side"] == "short"
            px = h[topi] if sell else l[topi]
            win = TAP_WINDOW * TF_SEC[tf] * 10**9
            hs = ("H4", "D1") if row.htf == "either" else (row.htf,)
            ts = ("OB", "BB", "FVG") if row.poi == "any" else (row.poi,)
            zm = Z[(Z["dir"] == (-1 if sell else 1)) & (Z["created"] <= r["top_open"]) & (Z["lo"] <= px) & (px <= Z["hi"])
                   & (Z["touch"] >= r["top_open"] - win) & (Z["touch"] <= r["top_open"]) & Z["htf"].isin(hs) & Z["type"].isin(ts)]
            z = r["zone"].split(";")
            lq = r["liq"].split(";")
            zf, li = pos[int(z[0])], pos[int(lq[0])]
            a, b = max(0, min(zf - 25, topi - 40, dec - 90)), dec + 50
            lines, pts = structure_layers(E, ev, a, b)
            lines.append((li, dec + 8, float(lq[1]), "Liq", "#8A94A6"))
            boxes = [(zf, dec + 18, float(z[2]), float(z[3]), "LTF " + r["variant"], CORAL if sell else GREEN)]
            for zz in zm.head(1).itertuples():
                t0 = int(np.searchsorted(E.index.as_unit("ns").asi8, zz.created))
                boxes.append((max(a, t0), b - 1, zz.lo, zz.hi, f"{zz.htf} {zz.type} (HTF POI, first tap)", AMBER))
            draw(E, a, b, DOCS / f"v25_top{rank}_{len(list(DOCS.glob(f'v25_top{rank}_*.png'))) + 1}.png",
                 f"v25 top row {rank}: {row.htf} {row.poi} · {tf} {row.mode} · entry {row.entry} · {row.target} · "
                 f"{pair} {'sell' if sell else 'buy'} · R {r['R']:+.2f}",
                 lines=lines, boxes=boxes, points=pts, decision=dec,
                 levels={"entry": r["e"], "stop": r["stop"], "target": r["tgt"]},
                 note="Random pick from this row. Amber = HTF POI tapped first; then MSS, BOS, Liq taken, entry. GMT+0.")
    print("charts ->", DOCS.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

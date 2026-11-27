"""Spec v22 audit + example charts (random picks) -> docs/smc_review/v22_*.png

    python -m backtest.chart_v22
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.ob_v21 import ohlc  # noqa: E402
from backtest.patterns import MARKETS  # noqa: E402
from backtest.smc_draw import CORAL, GREEN, draw, structure_layers  # noqa: E402
from backtest.smc_v22 import OUT  # noqa: E402
from engine.candles import clean, load_m1_csv, resample  # noqa: E402
from engine.smc_structure import external_structure  # noqa: E402

DOCS = ROOT / "docs" / "smc_review"
NAMES = {"smc_ob": "Order block", "toni": "Toni Iyke", "lingard": "Lingard"}


def audit(d, frames) -> dict:
    probs: dict[str, int] = {}

    def bad(k):
        probs[k] = probs.get(k, 0) + 1
    for (pair, tf), g in d.groupby(["pair", "tf"]):
        E = frames[(pair, tf)]
        o, h, l, c = ohlc(E)
        pos = {t: i for i, t in enumerate(E.index.as_unit("ns").asi8)}
        for r in g.itertuples():
            dec = pos[r.dec_open]
            z = r.zone.split(";")
            ln = r.line.split(";")
            zl, zj = pos[int(z[1])], pos[int(ln[1])]
            buy = r.side == "long"
            if zl > dec or zj > dec:
                bad("zone or structure finished after the decision (look-ahead)")
            if (buy and not (r.stop < r.e < r.tgt)) or (not buy and not (r.stop > r.e > r.tgt)):
                bad("levels on the wrong side")
            if r.model == "toni":
                if (buy and not c[dec] > c[zj]) or (not buy and not c[dec] < c[zj]):
                    bad("toni: inducement close not beyond the structure candle's close")
                zf = pos[int(z[0])]
                body = (max(o[zf], c[zf]) if buy else min(o[zf], c[zf]))
                leg = l[zj + 1:dec + 1].min() if buy else h[zj + 1:dec + 1].max()
                if (buy and leg <= body) or (not buy and leg >= body):
                    bad("toni: POI body reached by the inducement leg (mitigated)")
    return probs


def main() -> int:
    d = pd.concat([pd.read_csv(OUT / f"v22_{p}.csv") for p in MARKETS], ignore_index=True)
    frames = {}
    for pair in MARKETS:
        m1, _ = clean(load_m1_csv(ROOT / MARKETS[pair]["file"]))
        for tf in d.loc[d["pair"] == pair, "tf"].unique():
            frames[(pair, tf)] = resample(m1, tf, "utc0")
    print(f"Audit: {len(d):,} trades. Problems: {audit(d, frames) or 'none'}")
    rng = np.random.default_rng(22)
    picks = [("smc_ob", "H1", "3R", None), ("toni", "H1", "liq", "mss"), ("toni", "H1", "liq", "dbos"),
             ("lingard", "H4", "5R", None)]
    for model, tf, tg, st in picks:
        for pair in ("GBPUSD", "XAUUSD"):
            g = d[(d["model"] == model) & (d["tf"] == tf) & (d["target"] == tg) & (d["pair"] == pair)]
            if st:
                g = g[g["struct"] == st]
            if not len(g):
                continue
            r = g.iloc[int(rng.integers(len(g)))]
            E = frames[(pair, tf)]
            o, h, l, c = ohlc(E)
            pos = {t: i for i, t in enumerate(E.index.as_unit("ns").asi8)}
            ev = external_structure(o, h, l, c, "wick" if model == "lingard" else "close")
            z = r["zone"].split(";")
            zf = pos[int(z[0])]
            dec = pos[int(r["dec_open"])]
            a, b = max(0, min(zf - 15, dec - 80)), dec + 40
            lines, pts = structure_layers(E, ev, a, b)
            buy = r["side"] == "long"
            label = r["variant"] if model == "toni" else ("Order block" if model == "smc_ob" else "Order block (POI)")
            boxes = [(zf, dec + 12, float(z[2]), float(z[3]), label, GREEN if buy else CORAL)]
            draw(E, a, b, DOCS / f"v22_{model}{'_' + st if st else ''}_{pair}.png",
                 f"v22 {NAMES[model]} · {pair} {tf} · {'buy' if buy else 'sell'} · {r['variant']} · R {r['R']:+.2f}",
                 lines=lines, boxes=boxes, points=pts, decision=dec,
                 levels={"entry": r["e"], "stop": r["stop"], "target": r["tgt"]},
                 note="Random pick (not chosen). Box from the zone's first candle. GMT+0; dotted = decision candle.")
    print("charts ->", DOCS.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

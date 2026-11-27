"""Spec v24 audit + example charts (random picks) -> docs/smc_review/v24_*.png

    python -m backtest.chart_v24
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.ob_v21 import ohlc  # noqa: E402
from backtest.ore_v24 import OUT  # noqa: E402
from backtest.patterns import MARKETS  # noqa: E402
from backtest.smc_draw import BLUE, CORAL, GREEN, draw, structure_layers  # noqa: E402
from engine.candles import clean, load_m1_csv, resample  # noqa: E402
from engine.smc_structure import external_structure  # noqa: E402

DOCS = ROOT / "docs" / "smc_review"


def audit(d, frames) -> dict:
    probs: dict[str, int] = {}

    def bad(k):
        probs[k] = probs.get(k, 0) + 1
    for (pair, tf), g in d.groupby(["pair", "tf"]):
        E = frames[(pair, tf)]
        o, h, l, c = ohlc(E)
        pos = {t: i for i, t in enumerate(E.index.as_unit("ns").asi8)}
        for r in g.drop_duplicates(["model", "variant", "dec_open", "side"]).itertuples():
            dec = pos[r.dec_open]
            z, ln, lq = r.zone.split(";"), r.line.split(";"), r.liq.split(";")
            sell = r.side == "short"
            if pos[int(z[1])] > dec or pos[int(ln[1])] > dec or pos[int(lq[0])] > dec:
                bad("zone / structure / Liq finished after the order (look-ahead)")
            liq = float(lq[1])
            if (sell and not r.e > liq) or (not sell and not r.e < liq):
                bad("entry not beyond the Liq (no fake move needed)")
            if (sell and not (r.stop > r.e > r.tgt)) or (not sell and not (r.stop < r.e < r.tgt)):
                bad("levels on the wrong side")
            if (sell and not c[dec] < r.e) or (not sell and not c[dec] > r.e):
                bad("price already past the entry when the order was placed")
            if r.model == "ore_rev":
                b, m = pos[int(ln[0])], pos[int(ln[1])]
                lvl = float(ln[2])
                if (sell and not c[m] < lvl) or (not sell and not c[m] > lvl) or not b < m < dec:
                    bad("reversal: MSS candle not a close beyond the protected swing, or out of order")
    return probs


def main() -> int:
    d = pd.concat([pd.read_csv(OUT / f"v24_{p}.csv") for p in MARKETS], ignore_index=True)
    frames = {}
    for pair in MARKETS:
        m1, _ = clean(load_m1_csv(ROOT / MARKETS[pair]["file"]))
        for tf in d.loc[d["pair"] == pair, "tf"].unique():
            frames[(pair, tf)] = resample(m1, tf, "utc0")
    print(f"Audit: {len(d):,} trades. Problems: {audit(d, frames) or 'none'}")
    rng = np.random.default_rng(24)
    picks = [("ore_rev", "OB", "H1"), ("ore_rev", "OB", "M15"), ("ore_rev", "BB", "H1"), ("ore_rev", "BB", "M15"),
             ("ore_cont", "BB", "H1"), ("ore_cont", "BB", "M15")]
    for model, var, tf in picks:
        g = d[(d["model"] == model) & (d["variant"] == var) & (d["tf"] == tf) & (d["target"] == "5R") & d["d1"]
              & d["pair"].isin(["GBPUSD", "XAUUSD"])]
        if not len(g):
            continue
        r = g.iloc[int(rng.integers(len(g)))]
        E = frames[(r["pair"], tf)]
        o, h, l, c = ohlc(E)
        pos = {t: i for i, t in enumerate(E.index.as_unit("ns").asi8)}
        ev = external_structure(o, h, l, c, "close")
        z = r["zone"].split(";")
        lq = r["liq"].split(";")
        zf, dec, li = pos[int(z[0])], pos[int(r["dec_open"])], pos[int(lq[0])]
        a, b = max(0, min(zf - 20, dec - 90)), dec + 50
        lines, pts = structure_layers(E, ev, a, b)
        sell = r["side"] == "short"
        lines.append((li, dec + 8, float(lq[1]), "Liq", "#8A94A6"))
        boxes = [(zf, dec + 18, float(z[2]), float(z[3]), var + (" (" + r["shape"] + ")" if r["shape"] else ""),
                  CORAL if sell else GREEN)]
        name = "Reversal" if model == "ore_rev" else "Continuation"
        draw(E, a, b, DOCS / f"v24_{model}_{var}_{tf}.png",
             f"v24 {name} · {var} · {r['pair']} {tf} · {'sell' if sell else 'buy'} · R {r['R']:+.2f} (5R target)",
             lines=lines, boxes=boxes, points=pts, decision=dec,
             levels={"entry": r["e"], "stop": r["stop"], "target": r["tgt"]},
             note="Random pick. Order placed at the dotted candle (the BOS); price must take Liq and tap the box. GMT+0.")
    print("charts ->", DOCS.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

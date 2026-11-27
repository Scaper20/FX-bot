"""Spec v21 audit + example charts.

    python -m backtest.chart_ob_v21      -> audit summary + docs/smc_review/v21_*.png

Audit, written separately from the finder, on each trade's own candles:
- MSS: the decision candle closes beyond the broken level, and no candle between the broken swing and it did.
- Origin: nothing went beyond the top (sell) / bottom (buy) of the move between it and the MSS candle.
- Test B: the 2-candle (opposite candle, then a candle closing beyond its body) or 3-candle (candle, pin bar,
  candle closing beyond both bodies) rule holds, contains the origin, and is complete by the decision candle.
- Entry, stop and target on the right sides; stop beyond the origin.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.ob_v21 import OUT, ohlc  # noqa: E402
from backtest.patterns import MARKETS  # noqa: E402
from backtest.smc_draw import BLUE, CORAL, GREEN, draw, structure_layers  # noqa: E402
from engine.candles import clean, load_m1_csv, resample  # noqa: E402
from engine.smc_structure import external_structure  # noqa: E402

DOCS = ROOT / "docs" / "smc_review"


def audit(d: pd.DataFrame, frames: dict) -> dict:
    probs: dict[str, int] = {}

    def bad(k):
        probs[k] = probs.get(k, 0) + 1

    for (pair, tf), g in d.groupby(["pair", "tf"]):
        E = frames[(pair, tf)]
        o, h, l, c = ohlc(E)
        pos = {t: i for i, t in enumerate(E.index.as_unit("ns").asi8)}
        for r in g.itertuples():
            j, p, br = pos[r.j], pos[r.origin], pos[r.broken]
            sell = r.side == "short"
            beyond = (lambda x: x < r.level) if sell else (lambda x: x > r.level)
            if not beyond(c[j]) or any(beyond(c[k]) for k in range(br + 1, j)):
                bad("MSS candle is not the first close beyond the level")
            ext = h[p] if sell else l[p]
            if (sell and h[p:j + 1].max() > ext) or (not sell and l[p:j + 1].min() < ext):
                bad("something went beyond the origin before the MSS")
            if (sell and not (r.stop > r.e > r.tgt)) or (not sell and not (r.stop < r.e < r.tgt)):
                bad("levels on the wrong side")
            if (sell and r.stop <= ext) or (not sell and r.stop >= ext):
                bad("stop not beyond the origin")
            if r.test == "B":
                parts = r.box.split(";")
                f0, last, kind = pos[int(parts[0])], pos[int(parts[1])], parts[4]
                if not (f0 <= p <= last <= j):
                    bad("formation does not contain the origin or ends after the decision")
                up = (lambda k: c[k] > o[k]) if sell else (lambda k: c[k] < o[k])
                dn = (lambda k: c[k] < o[k]) if sell else (lambda k: c[k] > o[k])
                if kind == "2-candle":
                    ok = last == f0 + 1 and up(f0) and dn(last) and ((c[last] < o[f0]) if sell else (c[last] > o[f0]))
                else:
                    pb = f0 + 1
                    body = abs(c[pb] - o[pb])
                    wick = (h[pb] - max(o[pb], c[pb])) if sell else (min(o[pb], c[pb]) - l[pb])
                    lo_b = min(o[f0], c[f0], o[pb], c[pb]) if sell else max(o[f0], c[f0], o[pb], c[pb])
                    ok = (last == f0 + 2 and dn(last) and wick >= 2 * body and wick >= 0.5 * (h[pb] - l[pb])
                          and ((c[last] < lo_b) if sell else (c[last] > lo_b)))
                if not ok:
                    bad(f"{kind} rule not met")
    return probs


def main() -> int:
    d = pd.concat([pd.read_csv(OUT / f"ob21_{p}.csv", keep_default_na=False, na_values=[""]) for p in MARKETS],
                  ignore_index=True)
    d["box"] = d["box"].fillna("")
    frames = {}
    for pair in MARKETS:
        m1, _ = clean(load_m1_csv(ROOT / MARKETS[pair]["file"]))
        for tf in d.loc[d["pair"] == pair, "tf"].unique():
            frames[(pair, tf)] = resample(m1, tf, "utc0")
    probs = audit(d, frames)
    print(f"Audit: {len(d):,} trades checked. Problems: {probs or 'none'}")
    DOCS.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(21)
    for pair in ("GBPUSD", "XAUUSD"):
        E = frames[(pair, "H1")]
        o, h, l, c = ohlc(E)
        ev = external_structure(o, h, l, c, "close")
        pos = {t: i for i, t in enumerate(E.index.as_unit("ns").asi8)}
        for test, entry in (("A", "OB"), ("B", "edge")):
            g = d[(d["pair"] == pair) & (d["tf"] == "H1") & (d["test"] == test) & (d["entry"] == entry) & d["bias"]]
            for i, k in enumerate(rng.choice(len(g), min(2, len(g)), replace=False)):
                r = g.iloc[k]
                j, p = pos[int(r["j"])], pos[int(r["origin"])]
                parts = r["box"].split(";")
                f0 = pos[int(parts[0])]
                lo, hi = float(parts[2]), float(parts[3])
                sell = r["side"] == "short"
                label = "Order block" if test == "A" else f"Order block ({parts[4]})"
                a, b = max(p - 55, 0), j + 40
                lines, pts = structure_layers(E, ev, a, b)
                boxes = [(f0, j + 15, lo, hi, label, CORAL if sell else GREEN)]
                for x in range(p, j - 1):
                    if sell and h[x + 2] < l[x]:
                        boxes.append((x + 1, x + 5, h[x + 2], l[x], "FVG", BLUE))
                    if not sell and l[x + 2] > h[x]:
                        boxes.append((x + 1, x + 5, h[x], l[x + 2], "FVG", BLUE))
                name = "A (draft order block)" if test == "A" else "B (Ore's 2/3-candle order block)"
                draw(E, a, b, DOCS / f"v21_{test}_{pair}_{i + 1}.png",
                     f"v21 test {name} · {pair} H1 · {'sell' if sell else 'buy'} · R {r['R']:+.2f}",
                     lines=lines, boxes=boxes, points=pts, decision=j,
                     levels={"entry": r["e"], "stop": r["stop"], "target": r["tgt"]},
                     note="Random pick (not chosen). Box drawn from the first candle. GMT+0; dotted = MSS candle.")
    print("charts ->", DOCS.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Spec v20 audit + example charts.

    python -m backtest.chart_toni_lingard     -> audit summary + docs/toni_lingard_examples/*.png

Audit (written separately from the finder): for every trade, on its own candles,
- Toni: the structure candle comes before the decision candle; the decision candle body-closes beyond the structure
  candle's close; the POI body was not reached between them (unmitigated) and sits beyond the inducement extreme;
  the target is the extreme between them; stop beyond entry by more than 2 spreads.
- Lingard: the liquidity point is a real 5-bar swing, known by the decision candle; the BOS candle's wick went
  beyond an earlier swing; the order block's near edge is beyond the liquidity and within 1.5 ATR of it; the
  decision is in London/NY hours.
Charts: one example per model/variant on GBP/USD, GMT+0.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.patterns import MARKETS, atr  # noqa: E402
from backtest.romeo import arrays  # noqa: E402
from backtest.toni_lingard import OUT  # noqa: E402
from engine.candles import clean, load_m1_csv, resample  # noqa: E402

DOCS = ROOT / "docs" / "toni_lingard_examples"


def _swing_hi(h, i):
    return 2 <= i < len(h) - 2 and h[i] > max(h[i - 2], h[i - 1], h[i + 1], h[i + 2])


def audit(d: pd.DataFrame, frames: dict) -> dict:
    probs: dict[str, int] = {}

    def bad(k):
        probs[k] = probs.get(k, 0) + 1

    for (pair, tf, side), g in d.groupby(["pair", "tf", "side"]):
        E = frames[(pair, tf)]
        Eo = E.index.as_unit("ns").asi8
        Ec = pd.DatetimeIndex(E["close_time_utc"]).as_unit("ns").asi8
        o, h, l, c = arrays(E, side == "long")
        A = atr(h, l, c)
        pos = {t: i for i, t in enumerate(Eo)}
        sp = MARKETS[pair]["spread"]
        sg = -1.0 if side == "long" else 1.0
        for r in g.drop_duplicates(["model", "struct", "rule", "t_dec", "e"]).itertuples():
            p = [pos[int(x)] for x in r.pts.split(";")]
            dec = int(np.searchsorted(Ec, r.t_dec))
            e, stop, tgt = sg * r.e, sg * r.stop, sg * r.tgt
            if not stop - e > 2 * sp - 1e-9:
                bad("stop not beyond entry + 2 spreads")
            if r.model == "toni":
                top, j, v, poi = p
                if not (top <= j < v == dec):
                    bad("toni: order of top / structure / decision")
                if not c[v] < c[j]:
                    bad("toni: decision candle not a body close beyond the structure close")
                body_lo = min(o[poi], c[poi])
                if h[j + 1:v + 1].max() >= body_lo:
                    bad("toni: POI body mitigated before the order")
                if r.target == "liq" and abs(tgt - l[j:v + 1].min()) > 1e-9:
                    bad("toni: target is not the extreme between structure and decision")
            else:
                ph, bos, t, ob = p
                if not (_swing_hi(h, ph) and ph + 2 <= t and bos <= t == dec):
                    bad("lingard: liquidity is not a known swing")
                if not (e > h[ph] and e - h[ph] <= 1.5 * A[t] + 1e-9):
                    bad("lingard: order block not beyond / near the liquidity")
                if not (l[ob] >= e - 1e-9 and ob < max(ph, bos)):
                    bad("lingard: entry is not the order block's near edge")
                if not r.session:
                    bad("lingard: outside London/NY")
    return probs


def draw(E, r, path, title):
    Eo = E.index.as_unit("ns").asi8
    Ec = pd.DatetimeIndex(E["close_time_utc"]).as_unit("ns").asi8
    pos = {t: i for i, t in enumerate(Eo)}
    p = [pos[int(x)] for x in r["pts"].split(";")]
    dec = int(np.searchsorted(Ec, r["t_dec"]))
    a, b = max(0, min(p) - 15), min(len(E), dec + 45)
    w = E.iloc[a:b]
    fig, ax = plt.subplots(figsize=(11, 5.2))
    for k, (_, row) in enumerate(w.iterrows()):
        x = a + k
        col = "#0B7A5A" if row["close"] >= row["open"] else "#C8473B"
        ax.vlines(x, row["low"], row["high"], color=col, lw=0.8)
        ax.add_patch(plt.Rectangle((x - 0.3, min(row["open"], row["close"])), 0.6,
                                   max(abs(row["close"] - row["open"]), 1e-9), color=col))
    short = r["side"] == "short"
    hh, ll = E["high"].to_numpy(), E["low"].to_numpy()
    far = (lambda i: hh[i]) if short else (lambda i: ll[i])
    near = (lambda i: ll[i]) if short else (lambda i: hh[i])
    if r["model"] == "toni":
        top, j, v, poi = p
        labels = [(top, far(top), "Top of leg" if short else "Bottom of leg"),
                  (j, near(j), "MSS" if r["struct"] == "mss" else "Multiple BOS"),
                  (v, near(v), "Inducement confirmed"), (poi, far(poi), "POI (" + r["poi"] + ")")]
    else:
        ph, bos, t, ob = p
        labels = [(ph, far(ph), "Liquidity (first pullback)"), (bos, near(bos), "BOS"),
                  (ob, far(ob), "Order block")]
    for x, y, t in labels:
        ax.annotate(t, (x, y), textcoords="offset points", xytext=(0, 10 if (y == far(x)) else -16),
                    ha="center", fontsize=8, color="#0F1B2D", arrowprops=None)
        ax.plot([x], [y], marker="o", ms=4, color="#D99A1E")
    ax.axvline(dec, color="#0F1B2D", lw=0.8, ls=":")
    for y, t, col in ((r["e"], "Entry (limit)", "#0F1B2D"), (r["stop"], "Stop", "#C8473B"), (r["tgt"], "Target", "#0B7A5A")):
        ax.hlines(y, dec, b - 1, color=col, lw=1, ls="--")
        ax.text(b - 1, y, f" {t}", va="center", fontsize=8, color=col)
    ticks = list(range(a, b, max(1, (b - a) // 8)))
    ax.set_xticks(ticks)
    ax.set_xticklabels([E.index[i].strftime("%d %b %H:%M") for i in ticks], fontsize=7)
    ax.set_title(f"{title} · {'sell' if short else 'buy'} · R {r['R']:+.2f} (GMT+0; dotted = decision candle)", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def main() -> int:
    d = pd.concat([pd.read_csv(OUT / f"tl_{p}.csv") for p in MARKETS], ignore_index=True)
    frames = {}
    for pair in MARKETS:
        m1, _ = clean(load_m1_csv(ROOT / MARKETS[pair]["file"]))
        for tf in d.loc[d["pair"] == pair, "tf"].unique():
            frames[(pair, tf)] = resample(m1, tf, "utc0")
    probs = audit(d, frames)
    print(f"Audit: {len(d):,} trades checked. Problems: {probs or 'none'}")
    DOCS.mkdir(parents=True, exist_ok=True)
    ex = d[(d["pair"] == "GBPUSD") & d["bias"]]
    picks = [("toni", "mss", "H1", "liq", "Toni Iyke · H1 MSS → inducement → POI"),
             ("toni", "dbos", "H1", "liq", "Toni Iyke · H1 multiple BOS → inducement → POI"),
             ("lingard", "A", "H1", "5R", "Lingard · H1 pattern A (pullback before BOS)"),
             ("lingard", "B", "H4", "5R", "Lingard · H4 pattern B (pullback after BOS)")]
    for model, st, tf, tg, title in picks:
        g = ex[(ex["model"] == model) & (ex["struct"] == st) & (ex["tf"] == tf) & (ex["target"] == tg)]
        if model == "toni":
            g = g[g["rule"] == "closest"]
        if len(g):
            r = g.iloc[len(g) // 2]
            draw(frames[("GBPUSD", tf)], r, DOCS / f"{model}_{st}_{tf}.png", f"GBPUSD {tf} · {title}")
    print("charts ->", DOCS.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

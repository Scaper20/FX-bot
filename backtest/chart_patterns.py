"""Spec v19 audit + example charts.

    python -m backtest.chart_patterns      -> audit summary + docs/pattern_examples/*.png

Audit (independent of the finder code): every key point is a real swing on its own candles; the decision candle
closes at least 3 candles after the last swing; the stop is beyond every key point; entry, stop and target sit on
the right sides. Charts: two examples per pattern (GBP/USD H1 / H4), candles in GMT+0 with the key points and the
broken line drawn.
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
from backtest.patterns import MARKETS, NAMES, OUT  # noqa: E402
from engine.candles import clean, load_m1_csv, resample  # noqa: E402

DOCS = ROOT / "docs" / "pattern_examples"


def is_swing(h, l, i, high: bool) -> bool:
    if i < 3 or i + 3 >= len(h):
        return False
    if high:
        return h[i] == max(h[i - 3:i + 4])
    return l[i] == min(l[i - 3:i + 4])


def audit(d: pd.DataFrame, frames: dict) -> dict:
    probs = {}
    for (pair, tf), g in d.groupby(["pair", "tf"]):
        E = frames[(pair, tf)]
        Eo = E.index.as_unit("ns").asi8
        Ec = pd.DatetimeIndex(E["close_time_utc"]).as_unit("ns").asi8
        h, l = E["high"].to_numpy(), E["low"].to_numpy()
        pos = {t: i for i, t in enumerate(Eo)}
        for r in g.drop_duplicates(["side", "pattern", "t_dec", "pts"]).itertuples():
            pts = [pos[int(x)] for x in r.pts.split(";")]
            short = r.side == "short"
            if r.pattern == "dtop":
                kinds = [short, not short, short]          # top, neck (lowest low, not always a swing), top
                check = [0, 2]
            elif r.pattern == "hs":
                kinds, check = [short, not short, short, not short, short], [0, 2, 4]
            elif r.pattern == "flag":
                kinds, check = [short, not short, None], [1]
            else:
                kinds, check = [short, not short, short, not short], [0, 1, 2, 3]
            dpos = int(np.searchsorted(Ec, r.t_dec))
            swing_pts = [pts[k] for k in check]
            if not all(is_swing(h, l, pts[k], kinds[k]) for k in check):
                probs.setdefault("not a swing", []).append(r.Index)
            if dpos < max(swing_pts) + 3:
                probs.setdefault("decided before the swing was known", []).append(r.Index)
            ext = max(h[p] for p in pts) if short else min(l[p] for p in pts)
            if (short and r.stop <= ext) or (not short and r.stop >= ext):
                probs.setdefault("stop not beyond the pattern", []).append(r.Index)
    rows = d.itertuples()
    for r in rows:
        if (r.side == "short" and not (r.stop > r.e > r.tgt)) or (r.side == "long" and not (r.stop < r.e < r.tgt)):
            probs.setdefault("levels on the wrong side", []).append(r.Index)
    return {k: len(v) for k, v in probs.items()}


def draw(E, r, path, pair, tf):
    Eo = E.index.as_unit("ns").asi8
    pos = {t: i for i, t in enumerate(Eo)}
    pts = [pos[int(x)] for x in r["pts"].split(";")]
    Ec = pd.DatetimeIndex(E["close_time_utc"]).as_unit("ns").asi8
    dpos = int(np.searchsorted(Ec, r["t_dec"]))
    a, b = max(0, min(pts) - 25), min(len(E), dpos + 40)
    w = E.iloc[a:b]
    fig, ax = plt.subplots(figsize=(11, 5.2))
    for k, (_, row) in enumerate(w.iterrows()):
        x = a + k
        up = row["close"] >= row["open"]
        col = "#0B7A5A" if up else "#C8473B"
        ax.vlines(x, row["low"], row["high"], color=col, lw=0.8)
        ax.add_patch(plt.Rectangle((x - 0.3, min(row["open"], row["close"])), 0.6,
                                   max(abs(row["close"] - row["open"]), 1e-9), color=col))
    hh, ll = E["high"].to_numpy(), E["low"].to_numpy()
    short = r["side"] == "short"
    tops = (lambda i: hh[i]) if short else (lambda i: ll[i])
    bots = (lambda i: ll[i]) if short else (lambda i: hh[i])
    pat = r["pattern"]
    if pat == "dtop":
        lab = [(pts[0], tops(pts[0]), "Top 1"), (pts[2], tops(pts[2]), "Top 2"), (pts[1], bots(pts[1]), "Neckline")]
        ax.hlines(bots(pts[1]), pts[0], dpos, color="#D99A1E", lw=1.5)
    elif pat == "hs":
        lab = [(pts[0], tops(pts[0]), "LS"), (pts[2], tops(pts[2]), "Head"), (pts[4], tops(pts[4]), "RS")]
        s = (bots(pts[3]) - bots(pts[1])) / (pts[3] - pts[1])
        ax.plot([pts[1], dpos], [bots(pts[1]), bots(pts[1]) + s * (dpos - pts[1])], color="#D99A1E", lw=1.5)
    elif pat == "flag":
        lab = [(pts[0], tops(pts[0]), "Pole start"), (pts[1], bots(pts[1]), "Pole end")]
        ax.axvspan(pts[1] + 0.5, pts[2] - 0.5, color="#D99A1E", alpha=0.15)
    else:
        lab = [(pts[0], tops(pts[0]), "H1"), (pts[2], tops(pts[2]), "H2"), (pts[1], bots(pts[1]), "L1"),
               (pts[3], bots(pts[3]), "L2")]
        for p0, p1, fn in ((pts[0], pts[2], tops), (pts[1], pts[3], bots)):
            s = (fn(p1) - fn(p0)) / (p1 - p0)
            ax.plot([p0, dpos], [fn(p0), fn(p0) + s * (dpos - p0)], color="#D99A1E", lw=1.5)
    for x, y, t in lab:
        ax.annotate(t, (x, y), textcoords="offset points", xytext=(0, 8 if (y == tops(x)) == short else -14),
                    ha="center", fontsize=8, color="#0F1B2D")
    ax.axvline(dpos, color="#0F1B2D", lw=0.8, ls=":")
    for y, t, col in ((r["e"], "Entry", "#0F1B2D"), (r["stop"], "Stop", "#C8473B"), (r["tgt"], "Target", "#0B7A5A")):
        ax.hlines(y, dpos, b - 1, color=col, lw=1, ls="--")
        ax.text(b - 1, y, f" {t}", va="center", fontsize=8, color=col)
    ticks = list(range(a, b, max(1, (b - a) // 8)))
    ax.set_xticks(ticks)
    ax.set_xticklabels([E.index[i].strftime("%d %b %H:%M") for i in ticks], fontsize=7)
    ax.set_title(f"{pair} {tf} · {NAMES[pat]} · {'sell' if short else 'buy'} · {r['entry']} {r['target']} · "
                 f"R {r['R']:+.2f} (times GMT+0; dotted line = decision candle)", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def main() -> int:
    d = pd.concat([pd.read_csv(OUT / f"pat_{p}.csv") for p in MARKETS], ignore_index=True)
    frames = {}
    for pair in MARKETS:
        m1, _ = clean(load_m1_csv(ROOT / MARKETS[pair]["file"]))
        for tf in d.loc[d["pair"] == pair, "tf"].unique():
            frames[(pair, tf)] = resample(m1, tf, "utc0")
    probs = audit(d, frames)
    n = d.drop_duplicates(["pair", "tf", "side", "pattern", "t_dec", "pts"]).shape[0]
    print(f"Audit: {n:,} patterns, {len(d):,} trades checked. Problems: {probs or 'none'}")
    DOCS.mkdir(parents=True, exist_ok=True)
    ex = d[(d["pair"] == "GBPUSD") & (d["entry"] == "E1") & (d["target"] == "MM")]
    for pat in NAMES:
        for tf in ("H1", "H4"):
            g = ex[(ex["pattern"] == pat) & (ex["tf"] == tf)]
            if len(g):
                r = g.iloc[len(g) // 2]
                draw(frames[("GBPUSD", tf)], r, DOCS / f"{pat}_{tf}.png", "GBPUSD", tf)
    print("charts ->", DOCS.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

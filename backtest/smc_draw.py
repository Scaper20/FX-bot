"""Chart drawing for SMC reviews: zones as boxes, BOS/MSS as lines from the broken swing to the breaking candle,
swing labels, entry/stop/target from the decision candle. Times in GMT+0 (Exness MT5)."""
from __future__ import annotations

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

INK, GREEN, AMBER, CORAL, BLUE, GREY = "#0F1B2D", "#0B7A5A", "#D99A1E", "#C8473B", "#2B6CB0", "#8A94A6"


def draw(E: pd.DataFrame, a: int, b: int, path, title: str, *, lines=(), boxes=(), points=(), levels=None,
         decision=None, note: str = ""):
    """lines: (x0, x1, y, label, colour); boxes: (x0, x1, y0, y1, label, colour); points: (x, y, label, above);
    levels: dict(entry, stop, target) drawn from `decision` to the right edge."""
    a, b = max(0, a), min(len(E), b)
    w = E.iloc[a:b]
    fig, ax = plt.subplots(figsize=(12, 5.6))
    for k, (_, r) in enumerate(w.iterrows()):
        x = a + k
        col = GREEN if r["close"] >= r["open"] else CORAL
        ax.vlines(x, r["low"], r["high"], color=col, lw=0.8, zorder=2)
        ax.add_patch(Rectangle((x - 0.32, min(r["open"], r["close"])), 0.64,
                               max(abs(r["close"] - r["open"]), 1e-9), color=col, zorder=3))
    rng = w["high"].max() - w["low"].min()
    for x0, x1, y0, y1, label, col in boxes:
        x1 = min(x1, b - 1)
        ax.add_patch(Rectangle((x0 - 0.45, min(y0, y1)), x1 - x0 + 0.9, abs(y1 - y0), facecolor=col, alpha=0.18,
                               edgecolor=col, lw=1.0, zorder=1))
        ax.text(x0 - 0.4, max(y0, y1), label, fontsize=7.5, color=col, va="bottom", ha="left", zorder=5)
    for x0, x1, y, label, col in lines:
        ax.hlines(y, x0, x1, color=col, lw=1.1, zorder=4)
        ax.text((x0 + x1) / 2, y, label, fontsize=7.5, color=col, ha="center", va="bottom", zorder=5,
                bbox=dict(facecolor="white", edgecolor="none", pad=0.5, alpha=0.8))
    for x, y, label, above in points:
        ax.annotate(label, (x, y), textcoords="offset points", xytext=(0, 7 if above else -12), ha="center",
                    fontsize=7, color=INK, zorder=6)
    if decision is not None:
        ax.axvline(decision, color=INK, lw=0.8, ls=":", zorder=1)
        for key, col in (("entry", INK), ("stop", CORAL), ("target", GREEN)):
            if levels and levels.get(key) is not None:
                ax.hlines(levels[key], decision, b - 1, color=col, lw=1, ls="--", zorder=4)
                ax.text(b - 0.5, levels[key], f" {key.capitalize()}", va="center", fontsize=8, color=col)
    lo_y, hi_y = w["low"].min(), w["high"].max()
    for v in (levels or {}).values():
        if v is not None:
            lo_y, hi_y = min(lo_y, v), max(hi_y, v)
    rng = hi_y - lo_y
    ax.set_ylim(lo_y - 0.05 * rng, hi_y + 0.07 * rng)
    ax.set_xlim(a - 1, b + 3)
    ticks = list(range(a, b, max(1, (b - a) // 9)))
    ax.set_xticks(ticks)
    ax.set_xticklabels([E.index[i].strftime("%d %b %H:%M") for i in ticks], fontsize=7)
    ax.set_title(title, fontsize=10)
    if note:
        ax.text(0.01, 0.01, note, transform=ax.transAxes, fontsize=7.5, color=GREY, va="bottom")
    ax.grid(alpha=0.15)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def structure_layers(E: pd.DataFrame, events: list[dict], a: int, b: int):
    """BOS/MSS lines and HH/HL/LH/LL labels for events inside [a, b)."""
    h, l = E["high"].to_numpy(), E["low"].to_numpy()
    lines, points = [], []
    for ev in events:
        if ev["j"] < a:
            continue
        if ev["j"] >= b:
            break
        col = BLUE if ev["kind"] == "BOS" else AMBER
        lines.append((max(ev["broken"], a), ev["j"], ev["level"], ev["kind"], col))   # clipped at the left edge
        p = ev["protected"]
        if ev["dir"] == 1:                       # BOS: launched from a higher low; MSS: from the downtrend's low
            points.append((p, l[p], "HL" if ev["kind"] == "BOS" else "LL", False))
        else:
            points.append((p, h[p], "LH" if ev["kind"] == "BOS" else "HH", True))
    return lines, points


def idx_of(E: pd.DataFrame, t_ns: int) -> int:
    return int(np.searchsorted(E.index.as_unit("ns").asi8, t_ns))

"""Example charts of Inter Equity setups found by backtest/liquidity_ie.py, drawn from the real candles of
the setup's own timeframe (GMT+0, as on Exness MT5), labelled like his diagrams, so Ore can check the
candle formation by eye.

    python -m backtest.chart_liquidity            -> docs/liquidity_examples/*.png
"""
from __future__ import annotations

import random
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from engine import config as K  # noqa: E402
from engine.candles import clean, load_m1_csv, resample  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "backtest" / "out"
DEST = ROOT / "docs" / "liquidity_examples"
UP, DOWN, INK, MUTED = "#0B7A5A", "#C8473B", "#0F1B2D", "#5B6577"
BLUE, AMBER = "#2F5D9E", "#D99A1E"


def draw_candles(ax, E, a, b):
    for x, k in enumerate(range(a, b)):
        o, h, l, c = E.iloc[k][["open", "high", "low", "close"]]
        col = UP if c >= o else DOWN
        ax.plot([x, x], [l, h], color=col, lw=1)
        ax.add_patch(plt.Rectangle((x - 0.32, min(o, c)), 0.64, max(abs(c - o), 1e-9), color=col))
    ticks = list(range(0, b - a, max(1, (b - a) // 8)))
    ax.set_xticks(ticks)
    ax.set_xticklabels([E.index[a + t].strftime("%d %b %H:%M") for t in ticks], fontsize=7, rotation=0)
    ax.set_xlim(-1, b - a)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def hline(ax, y, x0, x1, color, text, dashed=False, above=True):
    ax.plot([x0, x1], [y, y], color=color, lw=1.2, ls="--" if dashed else "-")
    ax.annotate(text, (x1, y), xytext=(4, 3 if above else -9), textcoords="offset points", fontsize=7.5,
                color=color, va="bottom")


def outcome_text(trades, s):
    t = trades[(trades["family"] == "pure") & (trades["place_ns"] == s["place_ns"]) & (trades["model"] == s["model"])
               & (trades["entry_kind"] == s["entry_kind"]) & (trades["mgmt"] == "A") & (trades["pair"] == s["pair"])
               & (trades["tf"] == s["tf"])]
    if t.empty:
        return "order not filled"
    r = t.iloc[0]["R"]
    return "result: " + ("not filled" if pd.isna(r) else f"{r:+.2f}R after spread")


def chart_sniper(E, s, title, path, trades):
    i = s["idx"]
    a, b = max(0, i["c1"] - 14), min(len(E), i["c4"] + 22)
    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=130)
    draw_candles(ax, E, a, b)
    buy = s["mir"]
    lo, hi = E["low"].iloc[a:b].min(), E["high"].iloc[a:b].max()
    pad = (hi - lo) * 0.06
    for name in ("c1", "c2", "c3", "c4"):
        x = i[name] - a
        y = (E["low"].iloc[i[name]] - pad) if buy else (E["high"].iloc[i[name]] + pad)
        ax.text(x, y, name.upper(), ha="center", va="top" if buy else "bottom", fontsize=8.5, color=INK,
                fontweight="bold")
    c1x, c4x = i["c1"] - a, i["c4"] - a
    c1_ext = E["low"].iloc[i["c1"]] if buy else E["high"].iloc[i["c1"]]
    ax.plot([c1x - 0.4, c4x + 0.5], [c1_ext, c1_ext], color=MUTED, lw=1.2, ls="--")
    ax.annotate("C1 low (swept by C2)" if buy else "C1 high (swept by C2)", (c1x - 0.4, c1_ext), xytext=(-4, 0),
                textcoords="offset points", fontsize=7.5, color=MUTED, ha="right", va="center")
    c2_ext = E["low"].iloc[i["c2"]] if buy else E["high"].iloc[i["c2"]]
    zone_lo, zone_hi = sorted((s["e_real"] if s["entry_kind"] == "edge" else
                               (E["low"].iloc[i["c3"]] if buy else E["high"].iloc[i["c3"]]), c2_ext))
    ax.add_patch(plt.Rectangle((c4x - 0.45, zone_lo), 0.9, zone_hi - zone_lo, color=BLUE, alpha=0.18))
    end = b - a - 1
    hline(ax, s["e_real"], c4x - 0.5, end, AMBER, f"Entry ({'C3 low' if buy else 'C3 high'})" if s["entry_kind"] == "edge"
          else "Entry (zone middle)")
    hline(ax, s["stop_real"], i["c2"] - a - 0.5, end, DOWN,
          f"Stop: {'below' if buy else 'above'} C2 {'low' if buy else 'high'} (liquidity block)", above=not buy)
    tx = s["target_idx"] - a
    hline(ax, s["target_real"], max(tx, 0) - 0.5, end, UP, "Target: intact swing " + ("high" if buy else "low"))
    if tx >= 0:
        ax.plot([tx], [s["target_real"]], "o", color=UP, ms=4)
    ax.set_title(f"{title}\n{outcome_text(trades, s)}", fontsize=9.5, color=INK, loc="left")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def chart_core(E, s, title, path, trades):
    i = s["idx"]
    a = max(0, min(i["lb"], i["broken_low"]) - 6)
    b = min(len(E), i["place"] + 30)
    if b - a > 220:                                  # keep it readable: start nearer if the LB is very far left
        a = max(0, i["broken_low"] - 8)
    fig, ax = plt.subplots(figsize=(11, 5.4), dpi=130)
    draw_candles(ax, E, a, b)
    buy = s["mir"]
    end = b - a - 1
    bx, lx, hx, lbx = (i[k] - a for k in ("broken_low", "leg_low", "retail_high", "lb"))
    brk = E["high"].iloc[i["broken_low"]] if buy else E["low"].iloc[i["broken_low"]]
    hline(ax, brk, bx - 0.4, lx + 0.5, MUTED, ("high taken → buyers induced" if buy else "low taken → sellers induced"),
          dashed=True, above=buy)
    leg = E["high"].iloc[i["leg_low"]] if buy else E["low"].iloc[i["leg_low"]]
    ax.plot([lx], [leg], "v" if buy else "^", color=MUTED, ms=6)
    ax.plot([hx], [s["e_real"]], "^" if buy else "v", color=AMBER, ms=7)
    hline(ax, s["e_real"], hx - 0.5, end, AMBER,
          "retail low taken → buyers trapped → BUY" if buy else "retail high taken → sellers trapped → SELL")
    if lbx >= 0:
        lb_px = E["low"].iloc[i["lb"]] if buy else E["high"].iloc[i["lb"]]
        ax.plot([lbx], [lb_px], "o", mfc="none", mec=DOWN, ms=9)
    hline(ax, s["stop_real"], max(lbx, 0) - 0.5, end, DOWN, "Stop beyond the liquidity block (swing from the left)",
          above=not buy)
    hline(ax, s["target_real"], max(lx, 0) - 0.5, end, UP, "Target: liquidity left intact", above=buy)
    ax.set_title(f"{title}\n{outcome_text(trades, s)}", fontsize=9.5, color=INK, loc="left")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main() -> int:
    setups = pd.read_pickle(OUT / "liquidity_ie_setups.pkl")
    trades = pd.read_csv(OUT / "liquidity_ie_trades.csv")
    DEST.mkdir(parents=True, exist_ok=True)
    rng = random.Random(14)
    f = trades[(trades["family"] == "pure") & (trades["mgmt"] == "A") & trades["R"].notna()]
    filled = set(zip(f["pair"], f["tf"], f["model"], f["place_ns"]))      # show trades that actually filled
    frames = {}
    picks = []
    for model, tf, mir in (("sniper", "H4", True), ("sniper", "H4", False), ("sniper", "M15", True),
                           ("sniper", "M15", False), ("core", "H1", False), ("core", "H1", True),
                           ("core", "M15", False), ("core", "M15", True)):
        pool = [s for s in setups if s["model"] == model and s["tf"] == tf and s["mir"] == mir
                and s["entry_kind"] in ("edge", "trap") and (s["pair"], s["tf"], s["model"], s["place_ns"]) in filled]
        picks.append(rng.choice(pool))
    for n, s in enumerate(picks, 1):
        key = (s["pair"], s["tf"])
        if key not in frames:
            m1, _ = clean(load_m1_csv(ROOT / K.PAIRS[s["pair"]]["file"]))
            frames[key] = resample(m1, s["tf"], "utc0")
        E = frames[key]
        side = "BUY" if s["mir"] else "SELL"
        when = pd.Timestamp(s["place_ns"], tz="UTC").strftime("%a %d %b %Y %H:%M GMT+0")
        name = "4-candle sniper entry" if s["model"] == "sniper" else "induce → trap → trade"
        title = f"{s['pair']} {s['tf']} · {name} · {side} · order placed {when}"
        path = DEST / f"{n:02d}_{s['model']}_{s['pair']}_{s['tf']}_{side.lower()}.png"
        (chart_sniper if s["model"] == "sniper" else chart_core)(E, s, title, path, trades)
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

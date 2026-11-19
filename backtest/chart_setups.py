"""Draw example setups so Ore can say "yes, that's a CRT I'd take" or "no".

    python -m backtest.chart_setups --period design --n 6 --seed 3

Left panel: range timeframe (range candle, sweep candle, then what followed).
Right panel: entry timeframe from the sweep candle to the trade exit.
Writes PNGs to backtest/reports/examples/ plus a text description for each.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.stats import load  # noqa: E402
from engine import config as K  # noqa: E402
from engine.candles import clean, load_m1_csv, resample  # noqa: E402

INK, BG, UP, DOWN, AMBER = "#0F1B2D", "#F2F4F7", "#0B7A5A", "#C8473B", "#D99A1E"
TF_TD = {"D1": "1D", "H4": "4h", "H1": "1h", "M15": "15min", "M5": "5min"}


def candles(ax, df, width):
    for t, r in df.iterrows():
        col = UP if r.close >= r.open else DOWN
        ax.vlines(t, r.low, r.high, color=col, lw=0.8)
        ax.bar(t, abs(r.close - r.open) or (r.high - r.low) * 0.02, bottom=min(r.open, r.close),
               width=width, color=col, edgecolor=col)


def draw(r, frames, out: Path):
    rtf, etf = r.range_tf, r.entry_tf
    R, E = frames[rtf], frames[etf]
    ro = pd.Timestamp(r.range_open)
    step = pd.Timedelta(TF_TD[rtf])
    left = R.loc[ro - 8 * step: ro + (int(r.k) + 3) * step]
    sweep_open = R.index[R.index.get_loc(ro) + int(r.k)]
    exit_t = pd.Timestamp(r.exit_time)
    right = E.loc[sweep_open: exit_t + 3 * pd.Timedelta(TF_TD[etf])]
    if len(right) > 260:
        right = right.iloc[:260]

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5.2), gridspec_kw={"width_ratios": [1, 2]})
    fig.patch.set_facecolor(BG)
    for ax in (a1, a2):
        ax.set_facecolor("white")
        ax.tick_params(colors=INK, labelsize=8)
        for s in ax.spines.values():
            s.set_color("#C9CFD8")
    candles(a1, left, step * 0.7)
    candles(a2, right, pd.Timedelta(TF_TD[etf]) * 0.7)
    rh, rl = R.loc[ro, "high"], R.loc[ro, "low"]
    for ax in (a1, a2):
        ax.axhline(rh, color=INK, lw=0.8, ls="--")
        ax.axhline(rl, color=INK, lw=0.8, ls="--")
        ax.axhline((rh + rl) / 2, color=INK, lw=0.6, ls=":")
    a1.axvspan(ro - step * 0.45, ro + step * 0.45, color=AMBER, alpha=0.15)
    a1.axvspan(sweep_open - step * 0.45, sweep_open + step * 0.45, color="#7A8699", alpha=0.15)
    a1.set_title(f"{r.pair} {rtf}: range candle (amber), sweep candle (grey)", color=INK, fontsize=10, loc="left")
    a2.axhline(r.entry, color=AMBER, lw=1.2, label=f"entry {r.entry_type} {r.entry:.5g}")
    a2.axhline(r.stop, color=DOWN, lw=1.2, label=f"stop {r.stop_type} {r.stop:.5g}")
    tgt = r[f"{r.mgmt.split('_')[1]}_px"]
    a2.axhline(tgt, color=UP, lw=1.2, label=f"target {r.mgmt} {tgt:.5g}")
    a2.axvline(pd.Timestamp(r.decision_time), color=INK, lw=0.8, ls="-.", label="trigger/decision")
    a2.axvline(exit_t, color="#7A8699", lw=0.8, label=f"exit: {r.exit_reason} ({r.R:+.2f}R)")
    a2.legend(fontsize=8, loc="best", frameon=False)
    a2.set_title(f"{etf} entry: {r.direction}, trigger {r.trigger}", color=INK, fontsize=10, loc="left")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out, dpi=110)
    plt.close(fig)


def describe(r) -> str:
    conf = [c for c in ("has_fvg", "has_ob", "htf_fvg", "htf_ob", "htf_mss", "mtf_mss", "msnr", "other_trigger") if r[c]]
    if r.kz:
        conf.append(f"killzone {r.killzone}")
    return (f"{r.pair} {r.direction} | range {r.range_tf} candle opened {pd.Timestamp(r.range_open):%a %d %b %Y %H:%M} UTC, "
            f"sweep on candle +{int(r.k)} | trigger {r.trigger} on {r.entry_tf} at {pd.Timestamp(r.decision_time):%a %d %b %H:%M} UTC | "
            f"entry {r.entry_type} {r.entry:.5g}, stop {r.stop_type} {r.stop:.5g}, target {r.mgmt} | "
            f"result {r.exit_reason} {r.R:+.2f}R | confluences: {', '.join(conf) or 'none'}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--period", default="design")
    ap.add_argument("--n", type=int, default=6)
    ap.add_argument("--seed", type=int, default=3)
    a = ap.parse_args()
    d = load(ROOT / "backtest" / "out" / f"trades_{a.period}.csv")
    pick = d[d.trade & (d.expiry == 2) & (d.entry_type == "E1") & (d.stop_type == "S1") & (d.mgmt == "M1_T2")]
    pick = pick.groupby(["pair", "range_tf"]).sample(n=max(1, a.n // 4), random_state=a.seed)
    out = ROOT / "backtest" / "reports" / "examples"
    out.mkdir(parents=True, exist_ok=True)
    end = pd.Timestamp(K.PERIODS[a.period][1], tz="UTC")
    lines = []
    for pair in pick.pair.unique():
        m1, _ = clean(load_m1_csv(ROOT / K.PAIRS[pair]["file"]))
        m1 = m1[m1.index < end]
        frames = {tf: resample(m1, tf, K.DAY_CLOSE) for tf in ("D1", "H4", "H1", "M15", "M5")}
        for n, (_, r) in enumerate(pick[pick.pair == pair].iterrows(), 1):
            name = f"{pair}_{r.range_tf}_{r.entry_tf}_{n}.png"
            draw(r, frames, out / name)
            lines.append(f"- {name}: {describe(r)}")
    (out / "README.md").write_text("# Example setups (random sample)\n\n" + "\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

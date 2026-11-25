"""Spec v15 (docs/spec-v15-support-resistance.md): simple support/resistance, bounce and breakout,
each trade scored with no costs and with Ore's spreads.

    python -m backtest.sr_simple PAIR      (one pair -> backtest/out/sr_PAIR.csv)
    python -m backtest.sr_simple           (report from both files)
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.advanced import START, Outcome  # noqa: E402
from engine import config as K  # noqa: E402
from engine.candles import clean, load_m1_csv, resample  # noqa: E402

OUT = ROOT / "backtest" / "out"
REPORT = ROOT / "backtest" / "reports" / "sr_v15.md"
STOP_ADR = 0.25
TARGETS = (1, 2, 3)
ROUND = {"GBPUSD": 0.0050, "XAUUSD": 10.0}
YEARS = range(2022, 2027)
HOLD = int(pd.Timedelta("3D").value)


def ns(idx) -> np.ndarray:
    return pd.DatetimeIndex(idx).as_unit("ns").asi8


def swing_levels(F: pd.DataFrame, active_candles: int, kind: str) -> list[tuple]:
    """(price, t_on, t_off, kind) for 5-bar fractal highs/lows; known when candle k+2 closes."""
    H, L = F["high"].to_numpy(), F["low"].to_numpy()
    tc = ns(F["close_time_utc"])
    out = []
    for k in range(2, len(F) - 2 - 1):
        on = k + 2
        off = min(on + active_candles, len(F) - 1)
        if H[k] > max(H[k - 2], H[k - 1], H[k + 1], H[k + 2]):
            out.append((H[k], tc[on], tc[off], kind))
        if L[k] < min(L[k - 2], L[k - 1], L[k + 1], L[k + 2]):
            out.append((L[k], tc[on], tc[off], kind))
    return out


def day_levels(D: pd.DataFrame, pair: str) -> list[tuple]:
    out = []
    to, tc = ns(D.index), ns(D["close_time_utc"])
    H, L, C = D["high"].to_numpy(), D["low"].to_numpy(), D["close"].to_numpy()
    step = ROUND[pair]
    for j in range(1, len(D)):
        out.append((H[j - 1], to[j], tc[j], "yesterday high/low"))
        out.append((L[j - 1], to[j], tc[j], "yesterday high/low"))
        x = C[j - 1]
        up, dn = math.ceil(x / step) * step, math.floor(x / step) * step
        for p in {up, dn}:
            if abs(p - x) > 1e-12:
                out.append((p, to[j], tc[j], "round number"))
    return out


def run_pair(pair: str) -> pd.DataFrame:
    sp = K.PAIRS[pair]["spread"]
    m1, _ = clean(load_m1_csv(ROOT / K.PAIRS[pair]["file"]))
    m1 = m1[m1.index >= START - pd.Timedelta("120D")]
    D, H4, M = (resample(m1, tf, "utc0") for tf in ("D1", "H4", "M15"))
    adr = (D["high"] - D["low"]).rolling(14).mean().to_numpy()
    d_close = ns(D["close_time_utc"])
    Mo, Mc = ns(M.index), ns(M["close_time_utc"])
    MH, ML, MC = M["high"].to_numpy(), M["low"].to_numpy(), M["close"].to_numpy()
    scorers = {"no costs": Outcome(m1, 0.0, "D1"), "after spread": Outcome(m1, sp, "D1")}
    for o in scorers.values():
        o.hold = HOLD
    levels = (swing_levels(D, 20, "daily swing") + swing_levels(H4, 30, "4-hour swing") + day_levels(D, pair))
    rows = []
    for p, t_on, t_off, kind in levels:
        if t_on < START.value:
            continue
        di = int(np.searchsorted(d_close, t_on, side="right")) - 1          # last finished day
        if di < 14 or not np.isfinite(adr[di]):
            continue
        sd = STOP_ADR * adr[di]
        a, b = int(np.searchsorted(Mo, t_on)), int(np.searchsorted(Mo, t_off))
        if b <= a or a == 0:
            continue
        support = MC[a - 1] > p                                             # side when the level becomes active
        touch = np.flatnonzero(ML[a:b] <= p) if support else np.flatnonzero(MH[a:b] >= p)
        brk = np.flatnonzero(MC[a:b] < p) if support else np.flatnonzero(MC[a:b] > p)
        events = []
        if len(touch):
            j = a + touch[0]
            side = "long" if support else "short"
            stop = p - sd if support else p + sd
            events.append(("bounce", side, p, stop, None, (int(Mo[j]), int(Mc[j]))))
        if len(brk):
            j = a + brk[0]
            side = "short" if support else "long"
            e = MC[j]
            stop = p + sd if support else p - sd
            if (side == "long" and e > stop) or (side == "short" and e < stop):
                events.append(("breakout", side, e, stop, int(Mc[j]), None))
        for trade, side, e, stop, t_ns, window in events:
            risk = abs(e - stop)
            for n in TARGETS:
                tgt = e + n * risk if side == "long" else e - n * risk
                rec = {"pair": pair, "level": kind, "trade": trade, "target": f"{n}R", "side": side}
                for cost, sc in scorers.items():
                    res = sc(side, e, stop, None, tgt, t_ns, window)
                    if res:
                        rec[f"R {cost}"] = res["R"]
                        rec["hit"], rec["chance"], rec["time"] = res["hit_T2"], res["p_T2"], res["time"]
                if "R after spread" in rec:
                    rows.append(rec)
    return pd.DataFrame(rows)


def fmt(v, p="+.3f"):
    return "—" if v != v else format(v, p)


def report() -> int:
    d = pd.concat([pd.read_csv(OUT / f"sr_{p}.csv") for p in K.PAIRS], ignore_index=True)
    d["year"] = pd.to_datetime(d["time"], unit="ns", utc=True).dt.year
    lines = ["# Spec v15 result: simple support and resistance, before and after costs", "",
             "Spec: `docs/spec-v15-support-resistance.md` (committed before the run). GBP/USD + gold, Nov 2021 – Nov 2026. "
             "Stop = 0.25 × average daily range beyond the level; target 1R / 2R / 3R. Win = target before stop "
             "(trades closed at the 3-day time limit count as not won).", "",
             "| Level | Trade | Target | Trades | Win rate | Chance | Avg R, no costs | **Avg R, after spread** | Cost per trade | Years + (after spread) | Works? |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    rows = []
    for (lvl, tr, tg), g in d.groupby(["level", "trade", "target"], sort=False):
        y = g[g["hit"].notna()]
        win, ch = y["hit"].mean() * 100, y["chance"].mean() * 100
        r0, r1 = g["R no costs"].mean(), g["R after spread"].mean()
        yr = g.groupby("year")["R after spread"].mean()
        pos = int(sum(1 for k in YEARS if yr.get(k, -1) > 0))
        works = len(g) >= 100 and r1 > 0 and pos >= 4 and win > ch
        rows.append((lvl, tr, tg, len(g), win, ch, r0, r1, pos, works))
        lines.append(f"| {lvl} | {tr} | {tg} | {len(g)} | {win:.1f}% | {ch:.1f}% | {fmt(r0)} | **{fmt(r1)}** | "
                     f"{fmt(r1 - r0)} | {pos} of 5 | {'YES' if works else 'no'} |")
    t = pd.DataFrame(rows, columns=["level", "trade", "target", "n", "win", "chance", "r0", "r1", "pos", "works"])
    lines += ["", f"**Rows that work: {int(t['works'].sum())} of {len(t)}.** Across all rows: average R with no costs "
              f"{fmt(t['r0'].mean())}, after spread {fmt(t['r1'].mean())}; win rate minus chance "
              f"{fmt((t['win'] - t['chance']).mean(), '+.1f')} points on average.", ""]
    by_pair = d.groupby("pair")[["R no costs", "R after spread"]].mean()
    lines += ["| Pair | Avg R, no costs | Avg R, after spread |", "|---|---|---|"]
    for p, r in by_pair.iterrows():
        lines.append(f"| {p} | {fmt(r['R no costs'])} | {fmt(r['R after spread'])} |")
    REPORT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


def main() -> int:
    if len(sys.argv) == 2:
        df = run_pair(sys.argv[1])
        df.to_csv(OUT / f"sr_{sys.argv[1]}.csv", index=False)
        print(sys.argv[1], len(df), "trade rows")
        return 0
    return report()


if __name__ == "__main__":
    raise SystemExit(main())

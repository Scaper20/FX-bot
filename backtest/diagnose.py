"""Where does the strategy lose? Design data only (Nov 2021 - Dec 2023).

For every valid CRT (sweep candle closed back inside), from the sweep candle's
close, with the stop at the sweep extreme and NO costs, measure on 1-minute
data whether price reaches each target before the stop, within the next 1 and
5 range candles. Compare with two "no edge" benchmarks:
  analytic: on a random path, P(target before stop) = risk / (risk + reward)
  empirical: same geometry, same direction, started at a random other candle close
If real hit rates ~= benchmarks, the CRT premise itself has no edge.

    python -m backtest.diagnose          -> backtest/out/diag_design.csv + printed tables
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine import config as K  # noqa: E402
from engine import structure as S  # noqa: E402
from engine.candles import clean, load_m1_csv  # noqa: E402
from engine.sessions import session_flags  # noqa: E402
from engine.setups import Market, _idx_closed_by  # noqa: E402

OUT = ROOT / "backtest" / "out"
LEVELS = ("T1", "T2", "R1", "R2", "R3")


def first_passage(h, l, a, b, stop, levels):
    """Short space. For each level: 1 if low <= level strictly before high >= stop
    (same candle counts as stop), 0 if stop first, nan if neither before b."""
    seg_h, seg_l = h[a:b], l[a:b]
    st = S.first_true(seg_h >= stop)
    out = {}
    for name, lv in levels.items():
        t = S.first_true(seg_l <= lv)
        if t < 0 and st < 0:
            out[name] = np.nan
        elif t >= 0 and (st < 0 or t < st):
            out[name] = 1.0
        else:
            out[name] = 0.0
    return out


def candidates(mkt: Market, pair: str, start: pd.Timestamp, rng: np.random.Generator):
    rows = []
    for range_tf in ("D1", "H4"):
        for mirrored in (False, True):
            R = mkt.view[(range_tf, mirrored)]
            M = mkt.view[("M1", mirrored)]
            D = mkt.view[("D1", mirrored)]
            n = len(R.o)
            for i in range(n - 7):
                if R.t_open[i] < start.value:
                    continue
                for k in (1, 2):
                    s = i + k
                    rh, rl = R.h[i], R.l[i]
                    if rh <= rl:
                        continue
                    if k == 2 and (R.h[i + 1] > rh or R.l[i + 1] < rl):
                        continue
                    if not (R.h[s] > rh and S.crt_inside(R.o, R.h, R.l, R.c, i, R.c[s])) or R.l[s] < rl:
                        continue
                    e, stop = R.c[s], R.h[s]
                    risk = stop - e
                    if risk <= 0:
                        continue
                    lv = {"T1": (rh + rl) / 2, "T2": rl, "R1": e - risk, "R2": e - 2 * risk, "R3": e - 3 * risk}
                    a = int(np.searchsorted(M.t_open, R.t_close[s], side="left"))
                    b1 = int(np.searchsorted(M.t_open, R.t_close[s + 1], side="left"))
                    b5 = int(np.searchsorted(M.t_open, R.t_close[min(s + 5, n - 1)], side="left"))
                    fp1 = first_passage(M.h, M.l, a, b1, stop, lv)
                    fp5 = first_passage(M.h, M.l, a, b5, stop, lv)
                    # empirical null: same geometry from a random other close of the same TF
                    j = int(rng.integers(20, n - 7))
                    e2 = R.c[j]
                    lv2 = {kk: e2 - (e - v) for kk, v in lv.items()}
                    a2 = int(np.searchsorted(M.t_open, R.t_close[j], side="left"))
                    b52 = int(np.searchsorted(M.t_open, R.t_close[min(j + 5, n - 1)], side="left"))
                    fpn = first_passage(M.h, M.l, a2, b52, e2 + risk, lv2)
                    di = _idx_closed_by(D, R.t_open[s])
                    sign = 1 if mirrored else -1
                    st = int(mkt.d1_struct[di]) if di >= 0 else 0
                    em = int(mkt.d1_ema[di]) if di >= 0 else 0
                    atr_r = mkt.atr[range_tf][s - 1]
                    row = dict(pair=pair, range_tf=range_tf, direction="long" if mirrored else "short", k=k,
                               range_open=pd.Timestamp(R.t_open[i], tz="UTC"),
                               close_pos=(rh - R.c[s]) / (rh - rl),
                               depth_atr=(R.h[s] - rh) / atr_r if atr_r > 0 else np.nan,
                               sweep_ratio=(R.h[s] - R.l[s]) / (rh - rl),
                               risk_over_range=risk / (rh - rl),
                               rr_T2=(e - rl) / risk, rr_T1=(e - lv["T1"]) / risk,
                               session=session_flags(pd.Timestamp(R.t_close[s], tz="UTC")) or "off",
                               trend=("with" if st == sign else "against" if st == -sign else "none"),
                               trend_ema=("with" if em == sign else "against" if em == -sign else "none"))
                    for name in LEVELS:
                        rew = e - lv[name]
                        row[f"p0_{name}"] = risk / (risk + rew) if rew > 0 else np.nan
                        row[f"hit1_{name}"] = fp1[name] if rew > 0 else np.nan
                        row[f"hit5_{name}"] = fp5[name] if rew > 0 else np.nan
                        row[f"null5_{name}"] = fpn[name] if rew > 0 else np.nan
                    rows.append(row)
    return rows


def summarize(df: pd.DataFrame, by: list[str], level: str, horizon: str = "5") -> pd.DataFrame:
    h, p, nl = f"hit{horizon}_{level}", f"p0_{level}", f"null5_{level}"
    x = df[df[h].notna()]
    g = x.groupby(by, dropna=False)
    out = pd.DataFrame({
        "n": g.size(),
        "hit%": g[h].mean() * 100,
        "chance% (formula)": g[p].mean() * 100,
        "chance% (random entries)": g[nl].mean() * 100,
    })
    out["edge pts"] = out["hit%"] - out["chance% (formula)"]
    # z-score of excess hits vs formula, treating outcomes as independent Bernoulli(p0)
    var = g[p].apply(lambda s: (s * (1 - s)).sum())
    out["z"] = (g[h].sum() - g[p].sum()) / np.sqrt(var)
    return out.round(2)


def main() -> int:
    start, end = (pd.Timestamp(x, tz="UTC") for x in K.PERIODS["design"])
    rng = np.random.default_rng(11)
    rows = []
    for pair in K.PAIRS:
        m1, _ = clean(load_m1_csv(ROOT / K.PAIRS[pair]["file"]))
        mkt = Market(m1, data_end=end)
        rows += candidates(mkt, pair, start, rng)
    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "diag_design.csv", index=False)
    pd.set_option("display.width", 220)
    print(f"{len(df)} CRT candidates (design, both pairs, D1+H4, k=1,2, both directions)\n")
    for lvl in LEVELS:
        print(f"--- reach {lvl} before the sweep extreme, within 5 range candles, no costs")
        print(summarize(df, ["pair", "range_tf"], lvl).to_string(), "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


def in_candle_entries(mkt: Market, pair: str, start: pd.Timestamp, range_tf: str, entry_tf: str):
    """'Turtle soup' timing: enter DURING the sweep candle, at the first lower-timeframe CISD
    that closes back inside the range after price traded above it. Stop = highest high so far.
    Uses only candles closed at the entry time (the sweep candle's own close is unknown)."""
    rows = []
    for mirrored in (False, True):
        R = mkt.view[(range_tf, mirrored)]
        E = mkt.view[(entry_tf, mirrored)]
        M = mkt.view[("M1", mirrored)]
        n = len(R.o)
        for i in range(n - 7):
            if R.t_open[i] < start.value:
                continue
            s = i + 1
            rh, rl = R.h[i], R.l[i]
            if rh <= rl:
                continue
            e0 = int(np.searchsorted(E.t_open, R.t_open[s], side="left"))
            e1 = int(np.searchsorted(E.t_close, R.t_close[s], side="right"))      # candles inside S
            hmax, top, lvl, entered = -np.inf, -1, None, None
            swept = False
            for j in range(e0, e1):
                if E.l[j] < rl:            # swept the other side first: not this setup
                    break
                if E.h[j] > rh:
                    swept = True
                if not swept:
                    continue
                if E.h[j] > hmax:
                    hmax, top = E.h[j], j
                    got = S.cisd_level(E.o, E.c, top)
                    lvl = got[0] if got else None
                if lvl is not None and E.c[j] < lvl and E.c[j] < rh:
                    entered = j
                    break
            if entered is None:
                continue
            e, stop = E.c[entered], hmax
            risk = stop - e
            if risk <= 0:
                continue
            lv = {"T1": (rh + rl) / 2, "T2": rl, "R1": e - risk, "R2": e - 2 * risk, "R3": e - 3 * risk}
            a = int(np.searchsorted(M.t_open, E.t_close[entered], side="left"))
            b5 = int(np.searchsorted(M.t_open, R.t_close[min(s + 5, n - 1)], side="left"))
            fp = first_passage(M.h, M.l, a, b5, stop, lv)
            row = dict(pair=pair, range_tf=range_tf, entry_tf=entry_tf, direction="long" if mirrored else "short",
                       session=session_flags(pd.Timestamp(int(E.t_close[entered]), tz="UTC")) or "off",
                       risk=risk, spread=K.PAIRS[pair]["spread"],
                       sweep_closed_inside=bool(rl < R.c[s] < rh))
            for name in LEVELS:
                rew = e - lv[name]
                row[f"p0_{name}"] = risk / (risk + rew) if rew > 0 else np.nan
                row[f"hit5_{name}"] = fp[name] if rew > 0 else np.nan
                row[f"null5_{name}"] = np.nan
            rows.append(row)
    return rows

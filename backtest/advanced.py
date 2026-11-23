"""Spec v4 (docs/spec-v4-advanced.md): RTM1, OTE/failure swing, Kiss of Death, fake MSS, rejection block,
full MSnR, and mixing. All years Nov 2021 - Nov 2026 (Ore's decision), reported year by year.

    python -m backtest.advanced
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.romeo import arrays, first_passage, ny_daily, ny_h4, ny_weekly  # noqa: E402
from engine import config as K  # noqa: E402
from engine import structure as S  # noqa: E402
from engine.candles import clean, load_m1_csv, resample  # noqa: E402
from engine.simulate import simulate  # noqa: E402

NY = "America/New_York"
OUT = ROOT / "backtest" / "out"
START = pd.Timestamp("2021-11-01", tz="UTC")
MODELS = ["control C2 close", "M1", "RTM1", "OTE", "KOD", "fake MSS fade", "rejection block", "MSnR full"]
AGREE = {"M1", "RTM1", "OTE", "KOD", "MSnR full"}        # same-direction models used for "2+ agree"


def thick(o, h, l, c, body, j):
    r = h[j] - l[j]
    med = np.median(body[max(0, j - 20):j]) if j > 0 else 0
    return c[j] > o[j] and r > 0 and body[j] >= 0.5 * r and body[j] >= med


class Outcome:
    """Scores a trade on 1-minute data in REAL prices (spread included)."""

    def __init__(self, m1, spread, tf):
        self.t = m1.index.as_unit("ns").asi8
        self.H, self.L, self.C = (m1[k].to_numpy(float) for k in ("high", "low", "close"))
        self.sp = spread
        self.hold = pd.Timedelta("3D" if tf == "D1" else "20h").value

    def __call__(self, real_dir, e, stop, t1, t2, t_ns, limit_window=None):
        if real_dir == "short":
            h, l, c, sg, fs, xs = self.H, self.L, self.C, 1.0, 0.0, self.sp
        else:
            h, l, c, sg, fs, xs = -self.L, -self.H, -self.C, -1.0, self.sp, 0.0
        e, stop, t2 = sg * e, sg * stop, sg * t2
        t1 = sg * t1 if t1 is not None else None
        if stop <= e or t2 >= e:
            return None
        if limit_window is not None:                                    # exact minute the limit fills
            a = int(np.searchsorted(self.t, limit_window[0], side="left"))
            b = int(np.searchsorted(self.t, limit_window[1], side="left"))
            hit = np.where(h[a:b] >= e)[0]
            if not len(hit):
                return None
            ia = a + hit[0]
        else:
            ia = int(np.searchsorted(self.t, t_ns, side="left"))
        ib = int(np.searchsorted(self.t, self.t[min(ia, len(self.t) - 1)] + self.hold, side="left"))
        if ia >= len(self.t) - 1 or ib <= ia:
            return None
        risk = stop - e
        valid_t1 = t1 is not None and t2 < t1 < e
        lv = {"T2": t2, **({"T1": t1} if valid_t1 else {})}
        fp = first_passage(h, l, ia, ib, stop, lv)
        sim = simulate(h, l, c, ia, ia + 1, lambda f: ib, entry=e, market=True, stop=stop, targets={"T2": t2},
                       t1=t1 if valid_t1 else e + 1e9, fill_shift=fs, exit_shift=xs)
        res = sim.get("results", {}) if sim["status"] == "filled" else {}
        r = (res.get("M2_T2") if valid_t1 else res.get("M1_T2")) or {}
        return {"hit_T1": fp.get("T1", np.nan), "p_T1": risk / (risk + e - t1) if valid_t1 else np.nan,
                "hit_T2": fp["T2"], "p_T2": risk / (risk + e - t2), "R": r.get("R"), "time": self.t[ia]}


def ad_levels(o, c, end, lookback):
    """A-levels (up close then down close) and V-levels (mirror), from closes, up to candle `end`."""
    A, V = [], []
    for t in range(max(0, end - lookback), end):
        if c[t] > o[t] and c[t + 1] < o[t + 1]:
            A.append((t, c[t]))
        if c[t] < o[t] and c[t + 1] > o[t + 1]:
            V.append((t, c[t]))
    return A, V


def storyline_bearish(o, c, end, lookback=60):
    """Direction of the most recent close-break of an A- or V-level (bearish space): True if the last
    break was a close below a V-level."""
    A, V = ad_levels(o, c, end, lookback)
    last = None
    for t, lvl in A:
        k = next((j for j in range(t + 2, end + 1) if c[j] > lvl), None)
        if k is not None and (last is None or k > last[0]):
            last = (k, "bull")
    for t, lvl in V:
        k = next((j for j in range(t + 2, end + 1) if c[j] < lvl), None)
        if k is not None and (last is None or k > last[0]):
            last = (k, "bear")
    return last is not None and last[1] == "bear"


def fresh_levels(o, h, l, c, end, lookback, atr):
    """Fresh A-levels and gap levels (resistance in bearish space) and fresh V-levels (support)."""
    res = S.fresh_a_levels(o, h, l, c, end, lookback)
    for t in range(max(0, end - lookback), end):                          # gap levels: close-to-open gaps
        if o[t + 1] - c[t] > 0.1 * atr:
            lvl, fresh = c[t], True
            for j in range(t + 2, end + 1):
                if min(o[j], c[j]) < lvl < max(o[j], c[j]):
                    fresh = True
                elif l[j] <= lvl <= h[j]:
                    fresh = False
            if fresh:
                res.append(float(lvl))
    sup = [-x for x in S.fresh_a_levels(-o, -l, -h, -c, end, lookback)]  # V-levels via the mirror
    return res, sup


def run_pair(pair):
    spread = K.PAIRS[pair]["spread"]
    m1, _ = clean(load_m1_csv(ROOT / K.PAIRS[pair]["file"]))
    m1 = m1[m1.index >= START - pd.Timedelta("150D")]
    d1, h4 = ny_daily(m1), ny_h4(m1)
    w1 = ny_weekly(d1)
    entry = {"D1": resample(m1, "M15", "utc0"), "H4": resample(m1, "M5", "utc0")}
    rows = []
    for tf, R in (("D1", d1), ("H4", h4)):
        out = Outcome(m1, spread, tf)
        E = entry[tf]
        Eo_t = E.index.as_unit("ns").asi8
        Ec_t = pd.DatetimeIndex(E["close_time_utc"]).as_unit("ns").asi8
        Ro = pd.DatetimeIndex(R["t_open"]).as_unit("ns").asi8
        Rc = pd.DatetimeIndex(R["t_close"]).as_unit("ns").asi8
        H = w1 if tf == "D1" else d1
        Hc = pd.DatetimeIndex(H["t_close"]).as_unit("ns").asi8
        for mir in (False, True):
            sg = -1.0 if mir else 1.0
            sdir, odir = ("long", "short") if mir else ("short", "long")
            o, h, l, c = arrays(R, mir)
            eo, eh, el, ec = arrays(E, mir)
            ho, hh, hl, hc = arrays(H, mir)
            body = np.abs(ec - eo)
            for i in range(61, len(R) - 3):
                if Ro[i] < START.value:
                    continue
                s, c3 = i + 1, i + 2
                atr = np.mean(h[i - 14:i] - l[i - 14:i])
                events = []

                def add(model, direction, e, stop, t1, t2, t_ns, window=None):
                    rd = sdir if direction == "setup" else odir
                    res = out(rd, sg * e, sg * stop, None if t1 is None else sg * t1, sg * t2, t_ns, window)
                    if res:
                        res.update(model=model, pair=pair, tf=tf, direction=rd)
                        events.append(res)

                # ---- rejection block: turtle soup of C1's body (not its wick)
                bt, bb = max(o[i], c[i]), min(o[i], c[i])
                if bt > bb and h[s] > bt and h[s] <= h[i] and bb < c[s] < bt:
                    add("rejection block", "setup", c[s], h[s], (bt + bb) / 2, bb, Rc[s])
                # ---- the wick CRT
                if not (h[s] > h[i] and S.crt_inside(o, h, l, c, i, c[s]) and l[s] >= l[i]):
                    rows += events
                    continue
                mid, far = (h[i] + l[i]) / 2, l[i]
                add("control C2 close", "setup", c[s], h[s], mid, far, Rc[s])
                # ---- MSnR full: storyline + fresh level at the sweep + next fresh support as target
                hj = int(np.searchsorted(Hc, Rc[s], side="right")) - 1
                if hj > 10 and storyline_bearish(ho, hc, hj):
                    resist, support = fresh_levels(o, h, l, c, i, 60, atr)
                    tol = 0.1 * atr
                    if any(h[i] - tol <= lv <= h[s] + tol for lv in resist):
                        below = [x for x in support if x < c[s]]
                        tgt = max(below) if below else far
                        add("MSnR full", "setup", c[s], h[s], mid if tgt < mid < c[s] else None, tgt, Rc[s])
                # ---- lower-timeframe models, candle by candle
                s0 = int(np.searchsorted(Eo_t, Ro[s], side="left"))
                a = int(np.searchsorted(Eo_t, Ro[c3], side="left"))
                b = int(np.searchsorted(Ec_t, Rc[c3], side="right"))
                lb = max(4, s0 - 30)
                top, m1i, trig, rtm, mss, legL, ote = -np.inf, None, None, False, None, None, False
                sl_last, sl_before_top, sh_last = None, None, None
                t1i, kod_m1, kod_hi, kod_done, fm_done = None, None, None, False, False
                for j in range(lb, b):
                    k = j - 2                                                       # swing confirmed at j
                    if k - 2 >= 0:
                        if el[k] < el[k - 2:k].min() and el[k] < el[k + 1:j + 1].min():
                            sl_last = el[k]
                        if eh[k] > eh[k - 2:k].max() and eh[k] > eh[k + 1:j + 1].max() and t1i is not None and k > t1i:
                            sh_last = eh[k]
                    if j < s0:
                        continue
                    can = j >= a
                    if eh[j] > top:                                                 # new high: reset the shift
                        top, sl_before_top = eh[j], sl_last
                        m1i = j if thick(eo, eh, el, ec, body, j) else None
                        trig, rtm, mss, legL, ote = None, False, None, None, False
                    else:
                        if m1i is not None and trig is None and ec[j] < eo[m1i]:
                            trig = j
                            if can:
                                add("M1", "setup", ec[j], top, mid, far, Ec_t[j])
                        elif trig is not None and not rtm and j > trig and eh[j] >= eo[m1i] and can:
                            rtm = True
                            add("RTM1", "setup", eo[m1i], eh[m1i], mid, far, None, (Eo_t[j], Ec_t[j]))
                        if mss is None and sl_before_top is not None and ec[j] < sl_before_top:
                            mss, legL = j, el[j]
                        elif mss is not None and not ote:
                            if el[j] < legL:
                                legL = el[j]
                            else:
                                lvl = legL + 0.5 * (top - legL)
                                if eh[j] >= lvl and can:
                                    ote = True
                                    add("OTE", "setup", lvl, top, mid, far, None, (Eo_t[j], Ec_t[j]))
                    # Kiss of Death and fake MSS need price to have reached 50% first
                    if t1i is None and el[j] <= mid:
                        t1i = j
                        continue
                    if t1i is not None and not kod_done:
                        if sh_last is not None and eh[j] > sh_last and (kod_hi is None or eh[j] > kod_hi):
                            kod_hi = eh[j]
                            kod_m1 = j if thick(eo, eh, el, ec, body, j) else kod_m1
                        elif kod_m1 is not None and ec[j] < eo[kod_m1] and can:
                            kod_done = True
                            add("KOD", "setup", ec[j], kod_hi, None, far, Ec_t[j])
                    if t1i is not None and not fm_done and can and sl_last is not None:
                        if ec[j] < sl_last and ec[j] < far + 0.25 * (h[i] - far):
                            fm_done = True
                            lo5 = el[max(0, j - 4):j + 1].min()
                            # fade: opposite direction; in bearish space the "up" trade is stop below, target above
                            res = out(odir, sg * ec[j], sg * lo5, None, sg * mid, Ec_t[j])
                            if res:
                                res.update(model="fake MSS fade", pair=pair, tf=tf, direction=odir)
                                events.append(res)
                # ---- mixing: 2+ different same-direction models; enter when the second one fires
                agree = sorted((e for e in events if e["model"] in AGREE), key=lambda e: e["time"])
                seen, second = set(), None
                for e in agree:
                    seen.add(e["model"])
                    if len(seen) >= 2:
                        second = e
                        break
                if second:
                    events.append(dict(second, model="MIX 2+ agree"))
                rows += events
    return rows


def yearly(df):
    df = df.copy()
    df["year"] = pd.to_datetime(df["time"], utc=True).dt.year
    out = []
    groups = list(df.groupby(["model", "tf"])) + [((m, "both"), g) for m, g in df.groupby("model")]
    portfolio = df[~df["model"].isin(["MIX 2+ agree", "control C2 close"])]
    groups += [(("PORTFOLIO (all models)", "both"), portfolio)]
    for (model, tf), g in groups:
        row = {"model": model, "tf": tf, "trades": len(g)}
        for y in range(2021, 2027):
            r = g.loc[g["year"] == y, "R"].dropna()
            row[str(y)] = r.mean() if len(r) else np.nan
        r = g["R"].dropna()
        row["avg R"] = r.mean()
        row["total R"] = r.sum()
        x = g[g["hit_T2"].notna()]
        p = x["p_T2"]
        row["T2 hit%"] = x["hit_T2"].mean() * 100
        row["T2 chance%"] = p.mean() * 100
        row["z T2"] = (x["hit_T2"].sum() - p.sum()) / np.sqrt((p * (1 - p)).sum()) if len(x) else np.nan
        yrs = [row[str(y)] for y in range(2022, 2027)]
        row["years positive (of 5)"] = int(sum(1 for v in yrs if v == v and v > 0))
        row["consistent"] = row["years positive (of 5)"] >= 4 and row["avg R"] > 0
        out.append(row)
    return pd.DataFrame(out)


def main() -> int:
    rows = []
    for pair in K.PAIRS:
        rows += run_pair(pair)
        print(pair, "done", len(rows), flush=True)
    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "advanced_trades.csv", index=False)
    t = yearly(df)
    t.to_csv(OUT / "advanced_yearly.csv", index=False)
    pd.set_option("display.width", 260)
    pd.set_option("display.max_columns", 30)
    print(t.round(3).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

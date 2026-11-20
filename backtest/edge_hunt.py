"""Edge hunt v3 (docs/spec-v3-edge-hunt.md). Seven strategy families, four markets.

    python -m backtest.edge_hunt

Results for 2025-2026 are computed only for variants that already passed Design and Check.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.romeo import ny_daily, ny_h4  # noqa: E402
from engine.candles import clean, load_m1_csv, resample  # noqa: E402

MARKETS = {
    "GBPUSD": ("data/gbpusd-m1-bid-2021-11-01-2026-11-19.csv", 0.00010),
    "XAUUSD": ("data/xauusd-m1-bid-2021-11-01-2026-11-19.csv", 0.35),
    "EURUSD": ("data/eurusd-m1-bid-2021-11-01-2026-11-19.zip", 0.00008),
    "XAGUSD": ("data/xagusd-m1-bid-2021-11-01-2026-11-19.zip", 0.03),
}
PERIODS = {"design": ("2021-11-01", "2024-01-01"), "check": ("2024-01-01", "2025-01-01"),
           "final": ("2025-01-01", "2026-11-20")}
REPORT = ROOT / "backtest" / "reports" / "edge_hunt_v3.md"


def ts(x):
    return pd.Timestamp(x, tz="UTC")


def atr_series(d1: pd.DataFrame) -> pd.Series:
    pc = d1["close"].shift()
    tr = np.maximum(d1["high"] - d1["low"], np.maximum((d1["high"] - pc).abs(), (d1["low"] - pc).abs()))
    return tr.rolling(14).mean()


def trade(rows, fam, var, mkt, t, gross, cost, atr):
    if atr and np.isfinite(atr) and atr > 0 and np.isfinite(gross):
        rows.append((fam, var, mkt, t, gross / atr, cost / atr))


# ------------------------------------------------------------------ families

def fam_A(rows, mkt, d1, atr, cost):
    c, t = d1["close"].to_numpy(), pd.DatetimeIndex(d1["close_time_utc"])
    for N in (5, 10, 20, 60):
        for H in (1, 5):
            for k in range(N, len(c) - H, H):
                sig = np.sign(c[k] - c[k - N])
                if sig:
                    trade(rows, "A", f"trend N={N} hold={H}d", mkt, t[k], sig * (c[k + H] - c[k]), cost, atr[k])


def fam_B(rows, mkt, h1, atr_by_day, cost):
    o, c = h1["open"].to_numpy(), h1["close"].to_numpy()
    t = h1.index
    hours, wd, tn = t.hour.to_numpy(), t.weekday.to_numpy(), t.as_unit("ns").asi8
    day = t.normalize()
    a = atr_by_day.reindex(day, method="ffill").to_numpy()
    for L in (1, 3, 6):
        ok = np.zeros(len(t), bool)
        ok[: len(t) - L + 1] = (tn[L - 1:] - tn[: len(t) - L + 1]) == (L - 1) * 3_600_000_000_000
        for k in np.where(ok & (wd < 5))[0]:
            g = c[k + L - 1] - o[k]
            h = hours[k]
            trade(rows, "B", f"long {h:02d}:00 UTC for {L}h", mkt, t[k], g, cost, a[k])
            trade(rows, "B", f"short {h:02d}:00 UTC for {L}h", mkt, t[k], -g, cost, a[k])


def fam_C(rows, mkt, h1, atr_by_day, cost):
    for day, g in h1.groupby(h1.index.normalize()):
        if day.weekday() >= 5:
            continue
        asia = g[g.index.hour < 7]
        rest = g[(g.index.hour >= 7) & (g.index.hour < 20)]
        if len(asia) < 5 or rest.empty:
            continue
        hi, lo = asia["high"].max(), asia["low"].min()
        mid = (hi + lo) / 2
        a = atr_by_day.asof(day)
        brk = rest[(rest.index.hour < 16) & ((rest["close"] > hi) | (rest["close"] < lo))]
        if brk.empty:
            continue
        t0 = brk.index[0]
        e = brk["close"].iloc[0]
        d = 1 if e > hi else -1
        after = rest[rest.index > t0]
        for mode in ("break", "fade"):
            s = d if mode == "break" else -d
            for stop_kind in ("middle", "far side"):
                dist = abs(e - mid) if stop_kind == "middle" else (e - lo if d == 1 else hi - e)
                if dist <= 0:
                    continue
                stop = e - s * dist
                for ex in ("1R", "2R", "20:00 UTC"):
                    tgt = e + s * dist * (1 if ex == "1R" else 2) if ex != "20:00 UTC" else None
                    res = None
                    for _, b in after.iterrows():
                        if (s == 1 and b["low"] <= stop) or (s == -1 and b["high"] >= stop):
                            res = stop - e if s == 1 else e - stop
                            break
                        if tgt is not None and ((s == 1 and b["high"] >= tgt) or (s == -1 and b["low"] <= tgt)):
                            res = dist * (1 if ex == "1R" else 2)
                            break
                    if res is None:
                        last = after["close"].iloc[-1] if len(after) else e
                        res = s * (last - e)
                    trade(rows, "C", f"Asia range {mode}, stop {stop_kind}, exit {ex}", mkt, t0, res, cost, a)


def fam_D(rows, mkt, m1, atr_by_day, cost):
    M_t = m1.index.as_unit("ns").asi8
    for tf, R in (("D1", ny_daily(m1)), ("H4", ny_h4(m1))):
        Ro = pd.DatetimeIndex(R["t_open"]).as_unit("ns").asi8
        Rc = pd.DatetimeIndex(R["t_close"]).as_unit("ns").asi8
        for mir in (False, True):
            sg = -1 if mir else 1
            o, h, l, c = (sg * R[k].to_numpy(float) for k in ("open", "high", "low", "close"))
            if mir:
                h, l = l, h
            Mh = sg * (m1["low"] if mir else m1["high"]).to_numpy(float)
            Ml = sg * (m1["high"] if mir else m1["low"]).to_numpy(float)
            Mc = sg * m1["close"].to_numpy(float)
            for i in range(1, len(R) - 3):
                s, c3 = i + 1, i + 2
                if not (h[s] > h[i] and l[i] < c[s] < h[i] and l[s] >= l[i]):
                    continue
                lvl, mid = h[s], (h[i] + l[i]) / 2
                ia = int(np.searchsorted(M_t, Ro[c3]))
                ib = int(np.searchsorted(M_t, Rc[c3]))
                if ib <= ia:
                    continue
                hit = np.where(Mh[ia:ib] > lvl)[0]
                if not len(hit):
                    continue
                k0 = ia + hit[0]
                dist = lvl - mid
                if dist <= 0:
                    continue
                a = atr_by_day.asof(pd.Timestamp(Ro[c3], tz="UTC").normalize())
                end = int(np.searchsorted(M_t, Rc[c3] + (Rc[c3] - Ro[c3])))
                for ex in ("1R", "2R", "C3 close"):
                    stop = mid
                    tgt = lvl + dist * (1 if ex == "1R" else 2) if ex != "C3 close" else None
                    last = ib if ex == "C3 close" else end
                    seg_l, seg_h = Ml[k0:last], Mh[k0:last]
                    st = np.argmax(seg_l <= stop) if (seg_l <= stop).any() else -1
                    tg = (np.argmax(seg_h >= tgt) if (seg_h >= tgt).any() else -1) if tgt is not None else -1
                    if st >= 0 and (tg < 0 or st <= tg):
                        res = stop - lvl
                    elif tg >= 0:
                        res = tgt - lvl
                    else:
                        res = Mc[last - 1] - lvl
                    trade(rows, "D", f"CRT continuation {tf}, exit {ex}", mkt, pd.Timestamp(M_t[k0], tz="UTC"), res, cost, a)


def fam_E(rows, mkt, d1, atr, cost):
    o, h, l, c = (d1[k].to_numpy() for k in ("open", "high", "low", "close"))
    t = pd.DatetimeIndex(d1["close_time_utc"])
    for k in (1.5, 2.0):
        for i in range(15, len(c) - 1):
            if h[i] - l[i] >= k * atr[i - 1]:
                d = np.sign(c[i] - o[i])
                if d:
                    g = d * (c[i + 1] - c[i])
                    trade(rows, "E", f"big day >= {k} ATR, continue", mkt, t[i], g, cost, atr[i])
                    trade(rows, "E", f"big day >= {k} ATR, reverse", mkt, t[i], -g, cost, atr[i])


def fam_F(rows, mkt, d1, atr, cost):
    c = d1["close"].to_numpy()
    t = pd.DatetimeIndex(d1["close_time_utc"])
    names = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    for i in range(15, len(c)):
        wd = (t[i] - pd.Timedelta("1h")).tz_convert("America/New_York").weekday()
        if wd > 4:
            continue
        g = c[i] - c[i - 1]
        trade(rows, "F", f"long {names[wd]}", mkt, t[i - 1], g, cost, atr[i - 1])
        trade(rows, "F", f"short {names[wd]}", mkt, t[i - 1], -g, cost, atr[i - 1])


def fam_G(rows, mkt, d1, atr, cost):
    h, l, c = (d1[k].to_numpy() for k in ("high", "low", "close"))
    t = pd.DatetimeIndex(d1["close_time_utc"])
    for N in (20, 55):
        for ex in ("10 days", "N/2 break"):
            i = N
            while i < len(c) - 1:
                d = 1 if c[i] > h[i - N:i].max() else (-1 if c[i] < l[i - N:i].min() else 0)
                if not d:
                    i += 1
                    continue
                j = i + 1
                while j < len(c) - 1:
                    if ex == "10 days" and j - i >= 10:
                        break
                    if ex == "N/2 break":
                        n2 = N // 2
                        if (d == 1 and c[j] < l[j - n2:j].min()) or (d == -1 and c[j] > h[j - n2:j].max()):
                            break
                    j += 1
                trade(rows, "G", f"Donchian {N}, exit {ex}", mkt, t[i], d * (c[j] - c[i]), cost, atr[i])
                i = j + 1


# ------------------------------------------------------------------ evaluation

def tstat(x):
    x = np.asarray(x, float)
    if len(x) < 2 or x.std(ddof=1) == 0:
        return np.nan
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


def design_pass(g, fam):
    net = g["gross"] - g["cost"]
    yrs = g["time"].dt.year
    pos_years = all(net[yrs == y].mean() > 0 for y in (2022, 2023) if (yrs == y).any())
    if fam == "B":
        return net.mean() > 0 and tstat(net) >= 3.5 and pos_years
    pos_mkts = sum(net[g["mkt"] == m].mean() > 0 for m in g["mkt"].unique())
    return net.mean() > 0 and tstat(net) >= 3.0 and pos_mkts >= 3 and pos_years


def groups(df):
    keys = ["fam", "var"]
    for (fam, var), g in df.groupby(keys):
        if fam == "B":
            for m, gm in g.groupby("mkt"):
                yield fam, f"{var} [{m}]", gm
        else:
            yield fam, var, g


def summarize(df, per):
    lo, hi = (ts(x) for x in PERIODS[per])
    return df[(df["time"] >= lo) & (df["time"] < hi)]


def main() -> int:
    rows = []
    for mkt, (path, cost) in MARKETS.items():
        m1, _ = clean(load_m1_csv(ROOT / path))
        d1 = resample(m1, "D1", "ny17")
        atr = atr_series(d1).to_numpy()
        atr_by_day = pd.Series(atr, index=pd.DatetimeIndex(d1["close_time_utc"]).normalize()).groupby(level=0).last()
        h1 = resample(m1, "H1", "utc0")
        fam_A(rows, mkt, d1, atr, cost)
        fam_B(rows, mkt, h1, atr_by_day, cost)
        fam_C(rows, mkt, h1, atr_by_day, cost)
        fam_D(rows, mkt, m1, atr_by_day, cost)
        fam_E(rows, mkt, d1, atr, cost)
        fam_F(rows, mkt, d1, atr, cost)
        fam_G(rows, mkt, d1, atr, cost)
        print(f"{mkt}: {len(rows)} trades so far", flush=True)
    df = pd.DataFrame(rows, columns=["fam", "var", "mkt", "time", "gross", "cost"])
    df["time"] = pd.to_datetime(df["time"], utc=True)
    design = summarize(df, "design")

    # stage 1: design
    passed, tested = [], 0
    for fam, var, g in groups(design):
        tested += 1
        if design_pass(g, fam):
            net = g["gross"] - g["cost"]
            passed.append((fam, var, len(g), net.mean(), tstat(net)))
    # luck test: sign-flip gross returns, keep costs
    rng = np.random.default_rng(3)
    luck = []
    for _ in range(30):
        d = design.copy()
        d["gross"] = d["gross"] * rng.choice([-1.0, 1.0], len(d))
        luck.append(sum(1 for fam, var, g in groups(d) if design_pass(g, fam)))
    print(f"\nvariants tested: {tested}; design passed: {len(passed)}; luck test: {np.mean(luck):.1f} on average (max {max(luck)})")

    # stage 2 and 3, only for survivors
    lines = []
    check = summarize(df, "check")
    final_df = None
    for fam, var, n, mean, t in passed:
        base_var = var.split(" [")[0]
        mk = var.split("[")[1].rstrip("]") if "[" in var else None
        sel = (check["fam"] == fam) & (check["var"] == base_var) & ((check["mkt"] == mk) if mk else True)
        net = (check.loc[sel, "gross"] - check.loc[sel, "cost"])
        ok2 = len(net) > 1 and net.mean() > 0 and tstat(net) >= 2.0
        row = f"{fam} | {var} | design n={n} mean={mean:+.3f} ATR t={t:.1f} | 2024 n={len(net)} mean={net.mean():+.3f} t={tstat(net):.1f} -> {'PASS' if ok2 else 'fail'}"
        if ok2:
            if final_df is None:
                final_df = summarize(df, "final")
            self_ = (final_df["fam"] == fam) & (final_df["var"] == base_var) & ((final_df["mkt"] == mk) if mk else True)
            netf = final_df.loc[self_, "gross"] - final_df.loc[self_, "cost"]
            ok3 = len(netf) > 1 and netf.mean() > 0 and tstat(netf) >= 2.0
            row += f" | FINAL 2025-26 n={len(netf)} mean={netf.mean():+.3f} t={tstat(netf):.1f} -> {'PASS' if ok3 else 'fail'}"
        lines.append(row)
    print("\n".join(lines) if lines else "(no design survivors)")
    df.to_csv(ROOT / "backtest" / "out" / "edge_hunt_trades.csv.gz", index=False)
    (ROOT / "backtest" / "out" / "edge_hunt_summary.txt").write_text(
        f"tested {tested}, design passed {len(passed)}, luck avg {np.mean(luck):.1f} max {max(luck)}\n" + "\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

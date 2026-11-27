"""Spec v20 (docs/spec-v20-toni-lingard.md): Toni Iyke and Lingard SMC models.

    python -m backtest.toni_lingard PAIR     (one market -> backtest/out/tl_PAIR.csv)
    python -m backtest.toni_lingard          (report -> backtest/reports/toni_lingard_v20.md)

Coded in bearish form on prices that may be mirrored (bullish = mirror). Swings: engine 5-bar fractal, known
2 candles after the swing candle.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.advanced import START, Outcome  # noqa: E402
from backtest.patterns import FRESH, MAIN, MARKETS, atr  # noqa: E402
from backtest.romeo import arrays  # noqa: E402
from engine import config as K  # noqa: E402
from engine import structure as S  # noqa: E402
from engine.candles import clean, load_m1_csv, resample  # noqa: E402
from engine.sessions import session_flags  # noqa: E402

OUT = ROOT / "backtest" / "out"
REPORT = ROOT / "backtest" / "reports" / "toni_lingard_v20.md"
HOLD = {"H4": "10D", "H1": "5D", "M15": "2D"}
TFS = {"toni": ("H1", "M15"), "lingard": ("H4", "H1")}
VALID = 20          # candles a limit stays valid
LOOK = 30           # candles to wait for the inducement / pattern B second break
YEARS = range(2022, 2027)


# ------------------------------------------------------------------ Toni Iyke


def toni_events(o, h, l, c):
    """(kind, j, leg_top, broken swing lows) for MSS and multiple-BOS candles (bearish space)."""
    sh, sl = S.swing_flags(h, l)
    d = S.structure_direction(h, l, c, K.SWING_N)
    n = len(c)
    out = []
    active, leg_top, count, fired, legbroken = [], None, 0, False, []
    last_sl = None
    for j in range(5, n):
        k = j - 2
        if sh[k]:
            leg_top, count, fired, legbroken = k, 0, False, []
        if sl[k]:
            active.append(k)
            last_sl = k
        broken = [s for s in active if c[j] < l[s]]
        if broken:
            active = [s for s in active if s not in broken]
        if leg_top is not None and broken:
            count += len(broken)
            legbroken += broken
            if count >= 2 and not fired:
                out.append(("dbos", j, leg_top, list(legbroken)))
                fired = True
        if d[j] == -1 and d[j - 1] == 1 and last_sl is not None:
            s = max((x for x in (broken or [last_sl]) if x + 2 <= j), default=None)
            if s is not None:
                top = s + 1 + int(np.argmax(h[s + 1:j + 1])) if j > s else s
                out.append(("mss", j, top, [s]))
    return out


def toni_setups(o, h, l, c, kind, j, top, broken):
    """Inducement + the 4 POI rules. Returns list of (rule, entry, stop, v, target_swing, poi_idx)."""
    n = len(c)
    p = next((m for m in range(j + 1, min(j + LOOK, n)) if h[m] > h[m - 1]), None)
    if p is None:
        return []
    v = next((m for m in range(p + 1, min(j + LOOK, n)) if c[m] < c[j]), None)
    if v is None or v + 1 >= n:
        return []
    ind = h[j + 1:v + 1].max()
    cands = []
    for s in broken:
        lo = min(o[s], c[s])
        cands.append(("breaker", lo, lo, h[s], s))
    for m in range(max(top - 1, 0), j):
        if c[m] > o[m] and c[m + 1] < o[m + 1] and c[m + 1] <= o[m] and o[m + 1] >= c[m]:
            wick, body = o[m] - l[m], c[m] - o[m]
            entry = l[m] if wick < body else o[m]
            cands.append(("ob", o[m], entry, max(h[m], h[m + 1]), m))
            break
    valid = [x for x in cands if x[1] > ind and x[2] > c[v] and x[3] > x[2]]
    if not valid:
        return []
    tgt = l[j:v + 1].min()
    out = []
    closest = min(valid, key=lambda x: x[2])
    brk = [x for x in valid if x[0] == "breaker"]
    first = min(brk, key=lambda x: x[2]) if brk else closest
    for rule, x in (("closest", closest), ("breaker_first", first)):
        out.append((rule, x[0], x[2], x[3], v, tgt, x[4]))
    return out


# ------------------------------------------------------------------ Lingard


def ob_zones(o, h, l, c, a, b):
    """Runs of bullish candles in [a, b) followed by a bearish candle: (zone low, zone high, first idx)."""
    zs, m = [], max(a, 0)
    while m < b:
        if c[m] > o[m]:
            s = m
            while m + 1 < b and c[m + 1] > o[m + 1]:
                m += 1
            if m + 1 < len(c) and c[m + 1] < o[m + 1]:
                zs.append((l[s:m + 1].min(), h[s:m + 1].max(), s))
        m += 1
    return zs


def lingard_setups(o, h, l, c, A):
    """(pattern, t, PH, entry, stop, target_liq, ob_idx, bos)"""
    sh, sl = S.swing_flags(h, l)
    n = len(c)
    highs, out = [], []
    last_sl, broken = None, True
    for j in range(5, n):
        k = j - 2
        if sh[k]:
            highs.append(k)
        if sl[k]:
            last_sl, broken = k, False
        if last_sl is None or broken or l[j] >= l[last_sl]:
            continue
        broken = True
        h0 = max((x for x in highs if x < last_sl), default=None)
        if h0 is None:
            continue
        pulls = [x for x in highs if last_sl < x < j and x + 2 <= j]
        if pulls:
            pat, ph, t, seg = "A", pulls[0], j, (h0 - 2, j)
        else:
            ph = next((x for x in range(j + 1, min(j + LOOK, n - 2))
                       if sh[x] and x + 2 < n), None)
            if ph is None:
                continue
            low_after = l[j:ph + 1].min()
            t = next((m for m in range(ph + 2, min(j + LOOK, n)) if l[m] < low_after), None)
            if t is None:
                continue
            pat, seg = "B", (h0 - 2, ph)
        if np.isnan(A[t]):
            continue
        zs = [z for z in ob_zones(o, h, l, c, *seg) if z[0] > h[ph] and z[0] - h[ph] <= 1.5 * A[t]]
        if not zs:
            continue
        zl, zh, zi = min(zs, key=lambda z: z[0])
        if zl <= c[t]:
            continue
        out.append((pat, t, ph, zl, zh, l[j:t + 1].min(), zi, j))
    return out


# ------------------------------------------------------------------ run


def run_pair(pair: str) -> pd.DataFrame:
    mk = MARKETS[pair]
    sp = mk["spread"]
    m1, _ = clean(load_m1_csv(ROOT / mk["file"]))
    m1 = m1[m1.index >= START - pd.Timedelta("400D")]
    D = resample(m1, "D1", "utc0")
    Dc = pd.DatetimeIndex(D["close_time_utc"]).as_unit("ns").asi8
    rows = []
    for tf in sorted(set(TFS["toni"]) | set(TFS["lingard"])):
        E = resample(m1, tf, "utc0")
        Eo, Ec = E.index.as_unit("ns").asi8, pd.DatetimeIndex(E["close_time_utc"]).as_unit("ns").asi8
        after, free = Outcome(m1, sp, tf), Outcome(m1, 0.0, tf)
        after.hold = free.hold = pd.Timedelta(HOLD[tf]).value
        for mir in (False, True):
            sg = -1.0 if mir else 1.0
            side = "long" if mir else "short"
            o, h, l, c = arrays(E, mir)
            n = len(c)
            do, dh, dl, dc = arrays(D, mir)
            dd = S.structure_direction(dh, dl, dc, K.SWING_N)

            def bias_ok(t_ns):
                i = int(np.searchsorted(Dc, t_ns, side="right")) - 1
                return bool(i >= 0 and dd[i] == -1)

            def score(rec, e, stop, tgt_liq, t_idx):
                t_ns = int(Ec[t_idx])
                if t_ns < START.value or t_idx + 1 >= n:
                    return
                stop = stop + 2 * sp
                win = (int(Eo[t_idx + 1]), int(Ec[min(t_idx + VALID, n - 1)]))
                for tg, tgt in (("liq", tgt_liq), ("5R", e - 5 * (stop - e))):
                    if not (stop > e > tgt):
                        continue
                    rr = (e - tgt) / (stop - e)
                    res = after(side, sg * e, sg * stop, None, sg * tgt, None, win)
                    if not res or res["R"] is None:
                        continue
                    r0 = free(side, sg * e, sg * stop, None, sg * tgt, None, win)
                    rows.append({**rec, "pair": pair, "tf": tf, "side": side, "target": tg, "t_dec": t_ns,
                                 "bias": bias_ok(t_ns), "session": session_flags(pd.Timestamp(t_ns, tz="UTC")) != "",
                                 "time": res["time"], "R": res["R"], "R_free": r0["R"] if r0 else np.nan,
                                 "hit": res["hit_T2"], "chance": res["p_T2"], "rr": rr,
                                 "e": sg * e, "stop": sg * stop, "tgt": sg * tgt})

            if tf in TFS["toni"]:
                seen = set()
                for kind, j, top, broken in toni_events(o, h, l, c):
                    for rule, ptype, e, stop, v, tgt, pi in toni_setups(o, h, l, c, kind, j, top, broken):
                        key = (kind, rule, v, round(e, 6))
                        if key in seen:
                            continue
                        seen.add(key)
                        score({"model": "toni", "struct": kind, "rule": rule, "poi": ptype,
                               "pts": f"{Eo[top]};{Eo[j]};{Eo[v]};{Eo[pi]}"}, e, stop, tgt, v)
            if tf in TFS["lingard"]:
                A = atr(h, l, c)
                for pat, t, ph, zl, zh, tl, zi, bos in lingard_setups(o, h, l, c, A):
                    score({"model": "lingard", "struct": pat, "rule": "-", "poi": "ob",
                           "pts": f"{Eo[ph]};{Eo[bos]};{Eo[t]};{Eo[zi]}"}, zl, zh, tl, t)
        print(pair, tf, "done", sum(r["tf"] == tf for r in rows), flush=True)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ report


def stats(g: pd.DataFrame) -> dict:
    yr = g.groupby("year")["R"].mean()
    pos = int(sum(1 for y in YEARS if yr.get(y, -1) > 0))
    n = len(g)
    avg = g["R"].mean() if n else np.nan
    hit, ch = (g["hit"].mean() * 100, g["chance"].mean() * 100) if n else (np.nan, np.nan)
    return {"n": n, "avg": avg, "free": g["R_free"].mean() if n else np.nan, "pos": pos, "hit": hit, "ch": ch,
            "yr": yr, "ok": bool(n >= 30 and avg > 0 and pos >= 4 and hit >= ch),
            "t": avg / (g["R"].std() / np.sqrt(n)) if n > 1 and g["R"].std() > 0 else np.nan}


def f(v, p="+.3f"):
    return "—" if v is None or v != v else format(v, p)


def rowsets(d: pd.DataFrame) -> dict:
    """Pre-registered rows: name -> mask."""
    out = {}
    for model, keys in (("toni", ["struct", "tf", "rule", "target"]), ("lingard", ["struct", "tf", "target"])):
        x = d[d["model"] == model]
        if model == "lingard":
            x = x[x["session"] & ((x["target"] == "5R") | (x["rr"] >= 5))]
        for vals, g in x.groupby(keys):
            for b in (True, False):
                gg = g[g["bias"]] if b else g
                out[(model, *vals, "bias" if b else "no bias")] = gg.index
    return out


def report() -> int:
    from backtest.walkforward import verdict, walk
    d = pd.concat([pd.read_csv(OUT / f"tl_{p}.csv") for p in MARKETS], ignore_index=True)
    d["year"] = pd.to_datetime(d["t_dec"], unit="ns", utc=True).dt.year
    main_mask = d["pair"].isin(MAIN)
    L = ["# Spec v20 result: Toni Iyke and Lingard SMC models", "",
         "Spec: `docs/spec-v20-toni-lingard.md` (committed before the run). Main test GBP/USD + gold, fresh check "
         "EUR/USD + silver, Nov 2021 – Nov 2026, Ore's spreads, 1-minute scoring.", ""]
    sets = rowsets(d)
    summary = []
    for model, title in (("toni", "Toni Iyke"), ("lingard", "Lingard")):
        keys = [k for k in sets if k[0] == model]
        hdr = "| Structure | TF | POI rule | Target | Bias |" if model == "toni" else "| Pattern | TF | Target | Bias |"
        sep = "|---|---|---|---|---|" if model == "toni" else "|---|---|---|---|"
        L += [f"## {title}", "", hdr + " Trades | No costs | **After spread** | t | Hit vs chance | "
              + " | ".join(map(str, YEARS)) + " | Yrs + | Consistent | Fresh mkts (trades · avg · yrs+ · hit vs ch) | Verdict |",
              sep + "---|---|---|---|---|" + "---|" * len(YEARS) + "---|---|---|---|"]
        for key in keys:
            idx = sets[key]
            g = d.loc[idx]
            gm, gf = g[g["pair"].isin(MAIN)], g[g["pair"].isin(FRESH)]
            s, fs = stats(gm), stats(gf)
            fresh_ok = fs["n"] >= 30 and fs["avg"] > 0 and fs["pos"] >= 3 and fs["hit"] >= fs["ch"]
            verdict_row = ("fresh PASS" if fresh_ok else "fresh FAIL") if s["ok"] else ""
            summary.append((model, key, s, fs, s["ok"], s["ok"] and fresh_ok))
            L.append("| " + " | ".join(str(x) for x in key[1:]) + f" | {s['n']} | {f(s['free'])} | **{f(s['avg'])}** | "
                     f"{f(s['t'], '+.1f')} | {f(s['hit'], '.0f')}% vs {f(s['ch'], '.0f')}% | "
                     + " | ".join(f(s["yr"].get(y, np.nan), "+.2f") for y in YEARS)
                     + f" | {s['pos']} | {'YES' if s['ok'] else 'no'} | "
                     + (f"{fs['n']} · {f(fs['avg'])} · {fs['pos']} · {f(fs['hit'], '.0f')}% vs {f(fs['ch'], '.0f')}%" if s["ok"] else "")
                     + f" | {verdict_row} |")
        x = d[main_mask & (d["model"] == model)]
        if model == "lingard":
            x = x[x["session"] & ((x["target"] == "5R") | (x["rr"] >= 5))]
        unit = x["struct"] + " " + x["tf"] + " " + x["rule"] + " " + x["target"] + " " + x["pair"]
        wf, _ = walk(pd.DataFrame({"unit": unit, "time": pd.to_datetime(x["time"], unit="ns", utc=True).astype(str),
                                   "R": x["R"]}))
        v = verdict(wf, "A")
        cons = [s for s in summary if s[0] == model]
        L += ["", f"**{title}: {sum(s[4] for s in cons)} of {len(cons)} rows consistent; {sum(s[5] for s in cons)} also "
              f"held on EUR/USD + silver.** Walk-forward (choose on past years, trade next year blind, 2023–26): "
              f"{f(v['avg'])}R over {v['trades']} trades, positive in {v['years_pos']} of 4 years → "
              f"**{'PASS' if v['pass'] else 'fail'}**.", "",
              f"All {title} trades pooled (GBP/USD + gold): {len(x):,} trades, {f(x['R_free'].mean())}R before costs, "
              f"**{f(x['R'].mean())}R after spread**, target hit {x['hit'].mean() * 100:.1f}% vs {x['chance'].mean() * 100:.1f}% chance.", ""]
    L += ["## By market (all rows, bias on)", "", "| Market | Toni trades | Toni avg R | Lingard trades | Lingard avg R |",
          "|---|---|---|---|---|"]
    for p in MARKETS:
        a = d[(d["pair"] == p) & (d["model"] == "toni") & d["bias"]]
        b = d[(d["pair"] == p) & (d["model"] == "lingard") & d["bias"] & d["session"] & ((d["target"] == "5R") | (d["rr"] >= 5))]
        L.append(f"| {p} | {len(a):,} | {f(a['R'].mean())} | {len(b):,} | {f(b['R'].mean())} |")
    REPORT.write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        df = run_pair(sys.argv[1])
        df.to_csv(OUT / f"tl_{sys.argv[1]}.csv", index=False)
        print(sys.argv[1], len(df), "trades")
    else:
        raise SystemExit(report())

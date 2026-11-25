"""Spec v16 (docs/spec-v16-smc-bias.md): D1/H4 structure bias + entry-timeframe MSS + OB/FVG entries.

    python -m backtest.smc_bias PAIR TF     (one part -> backtest/out/smc_PAIR_TF.csv)
    python -m backtest.smc_bias             (report)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.advanced import START, Outcome  # noqa: E402
from backtest.liquidity_ie import swing_flags  # noqa: E402
from backtest.romeo import arrays  # noqa: E402
from backtest.walkforward import verdict, walk  # noqa: E402
from engine import config as K  # noqa: E402
from engine import structure as S  # noqa: E402
from engine.candles import clean, load_m1_csv, resample  # noqa: E402
from engine.sessions import session_flags  # noqa: E402

OUT = ROOT / "backtest" / "out"
REPORT = ROOT / "backtest" / "reports" / "smc_bias_v16.md"
VALID = 12                 # entry candles a limit stays valid
RR_T = 3.0
HOLD = int(pd.Timedelta("3D").value)
YEARS = range(2022, 2027)
ENTRY = {"E1": "market at MSS close", "E2": "FVG near edge", "E3": "FVG middle", "E4": "OB open", "E5": "OB middle"}


def ns(x):
    return pd.DatetimeIndex(x).as_unit("ns").asi8


def mss_events(o, h, l, c):
    """Bearish space: candle j closes below the latest confirmed swing low (each low used once).
    Yields (j, top) with top = highest candle between that swing low and j."""
    _, sl = swing_flags(h, l)
    last, used = None, True
    for j in range(5, len(c) - 1):
        k = j - 2
        if sl[k]:
            last, used = k, False
        if last is None or used or j <= last + 2:
            continue
        if c[j] < l[last]:
            used = True
            top = last + 1 + int(np.argmax(h[last + 1:j + 1]))
            yield j, top


def run_part(pair: str, tf: str) -> pd.DataFrame:
    sp = K.PAIRS[pair]["spread"]
    m1, _ = clean(load_m1_csv(ROOT / K.PAIRS[pair]["file"]))
    m1 = m1[m1.index >= START - pd.Timedelta("400D")]
    D, H4, E = (resample(m1, x, "utc0") for x in ("D1", "H4", tf))
    bias = {}
    for name, F in (("D1", D), ("H4", H4)):
        bias[name] = (ns(F["close_time_utc"]), S.structure_direction(F["high"].to_numpy(), F["low"].to_numpy(),
                                                                      F["close"].to_numpy(), K.SWING_N))
    Eo, Ec = ns(E.index), ns(E["close_time_utc"])
    after, free = Outcome(m1, sp, "D1"), Outcome(m1, 0.0, "D1")
    after.hold = free.hold = HOLD
    rows = []
    for mir in (False, True):
        sg, real = (-1.0, 1) if mir else (1.0, -1)          # real: +1 buy, -1 sell
        o, h, l, c = arrays(E, mir)
        n = len(c)
        for j, top in mss_events(o, h, l, c):
            t = int(Ec[j])
            if t < START.value:
                continue
            b = {}
            for name, (tc, d) in bias.items():
                i = int(np.searchsorted(tc, t, side="right")) - 1
                b[name] = i >= 0 and d[i] == real
            stop = h[top] + 2 * sp
            entries = [("E1", c[j], t, None)]
            win = (int(Eo[j + 1]), int(Ec[min(j + VALID, n - 1)]))
            fvg = S.latest_open_bear_fvg(h, l, top, j)
            if fvg:
                entries += [("E2", fvg["bottom"], None, win), ("E3", fvg["mid"], None, win)]
            ob = S.bear_order_block(o, h, l, c, top, j, K.OB_SEARCH)
            if ob:
                entries += [("E4", ob["open"], None, win), ("E5", ob["mean"], None, win)]
            ses = session_flags(pd.Timestamp(t, tz="UTC")) != ""
            for name, e, t_ns, w in entries:
                if stop <= e or (w is not None and e <= c[j]):
                    continue
                tgt = e - RR_T * (stop - e)
                side = "long" if mir else "short"
                res = after(side, sg * e, sg * stop, None, sg * tgt, t_ns, w)
                if not res:
                    continue
                rec = {"pair": pair, "tf": tf, "side": side, "entry": name, "bias_both": b["D1"] and b["H4"],
                       "bias_d1": b["D1"], "session": ses, "mss_time": t, "R": res["R"], "hit": res["hit_T2"],
                       "chance": res["p_T2"], "time": res["time"], "R_free": np.nan}
                if rec["bias_both"]:
                    r0 = free(side, sg * e, sg * stop, None, sg * tgt, t_ns, w)
                    rec["R_free"] = r0["R"] if r0 else np.nan
                rows.append(rec)
    return pd.DataFrame(rows)


def fmt(v, p="+.3f"):
    return "—" if v != v else format(v, p)


def report() -> int:
    d = pd.concat([pd.read_csv(f) for f in sorted(OUT.glob("smc_*_*.csv"))], ignore_index=True)
    d["year"] = pd.to_datetime(d["time"], unit="ns", utc=True).dt.year
    versions = {"D1 + H4 bias (Ore's model)": d["bias_both"], "D1 bias only": d["bias_d1"],
                "no bias (baseline)": pd.Series(True, index=d.index)}
    lines = ["# Spec v16 result: D1/H4 bias + MSS + order block / FVG entries", "",
             "Spec: `docs/spec-v16-smc-bias.md` (committed before the run). GBP/USD + gold, Nov 2021 – Nov 2026, Ore's "
             "spreads, target 3R (chance 25%), stop above the top + 2 spreads.", ""]
    rows = []
    for vname, m in versions.items():
        x0 = d[m]
        lines += [f"## {vname}", "",
                  "| TF | Entry | Session | Trades | Win vs chance | Avg R no costs | **Avg R after spread** | "
                  + " | ".join(str(y) for y in YEARS) + " | Years + | Consistent |",
                  "|---|---|---|---|---|---|---|" + "---|" * len(YEARS) + "---|---|"]
        for (tf, en), g0 in x0.groupby(["tf", "entry"]):
            for sname, g in (("all", g0), ("London/NY", g0[g0["session"]])):
                yr = g.groupby("year")["R"].mean()
                pos = int(sum(1 for k in YEARS if yr.get(k, -1) > 0))
                y = g[g["hit"].notna()]
                hit, ch = y["hit"].mean() * 100, y["chance"].mean() * 100
                ok = len(g) >= 30 and g["R"].mean() > 0 and pos >= 4 and hit >= ch
                rows.append((vname, tf, en, sname, len(g), g["R"].mean(), ok))
                lines.append(f"| {tf} | {en} {ENTRY[en]} | {sname} | {len(g)} | {hit:.1f}% vs {ch:.1f}% | "
                             f"{fmt(g['R_free'].mean())} | **{fmt(g['R'].mean())}** | "
                             + " | ".join(fmt(yr.get(k, np.nan), "+.2f") for k in YEARS)
                             + f" | {pos} | {'YES' if ok else 'no'} |")
        unit = x0["tf"] + " " + x0["entry"] + " " + x0["pair"]
        wf, _ = walk(pd.DataFrame({"unit": unit, "time": pd.to_datetime(x0["time"], unit="ns", utc=True).astype(str),
                                   "R": x0["R"]}))
        v = verdict(wf, "A")
        lines += ["", f"Walk-forward: blind {fmt(v['avg'])}R over {v['trades']} trades, positive in {v['years_pos']} of 4 "
                  f"years -> **{'PASS' if v['pass'] else 'fail'}**.", ""]
    t = pd.DataFrame(rows, columns=["version", "tf", "entry", "session", "n", "avg", "ok"])
    t.to_csv(OUT / "smc_v16_rows.csv", index=False)
    both = d[d["bias_both"]]
    lines += ["## Summary", "",
              f"Consistent rows: **{int(t['ok'].sum())} of {len(t)}**. With Ore's D1+H4 bias: average {fmt(both['R'].mean())}R "
              f"after spread, {fmt(both['R_free'].mean())}R with no costs, over {len(both):,} trades. "
              f"No bias: {fmt(d['R'].mean())}R after spread over {len(d):,} trades."]
    REPORT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


def main() -> int:
    if len(sys.argv) == 3:
        df = run_part(sys.argv[1], sys.argv[2])
        df.to_csv(OUT / f"smc_{sys.argv[1]}_{sys.argv[2]}.csv", index=False)
        print(sys.argv[1], sys.argv[2], len(df), "trades")
        return 0
    return report()


if __name__ == "__main__":
    raise SystemExit(main())

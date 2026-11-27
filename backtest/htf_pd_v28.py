"""Spec v28 (docs/spec-v28-htf-confirm-pd.md): Ore's H4-confirmation and premium/discount rules on every strategy.

    python -m backtest.htf_pd_v28
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.pattern_stats import ore_rules  # noqa: E402
from backtest.patterns import MARKETS  # noqa: E402
from engine.candles import clean, load_m1_csv, resample  # noqa: E402
from engine.smc_structure import external_structure  # noqa: E402

OUT = ROOT / "backtest" / "out"
SET_A, SET_B = ["GBPUSD", "XAUUSD"], ["EURUSD", "XAGUSD"]
CUT_A = pd.Timestamp("2025-01-01", tz="UTC").value


class Context:
    """H4 / D1 structure state known at any time (body-close external structure, full history)."""

    def __init__(self, pair: str):
        m1, _ = clean(load_m1_csv(ROOT / MARKETS[pair]["file"]))
        self.tf = {}
        for tf in ("H4", "D1"):
            F = resample(m1, tf, "utc0")
            o, h, l, c = (F[k].to_numpy(float) for k in ("open", "high", "low", "close"))
            ev, hi, lo = external_structure(o, h, l, c, "close", track=True)
            trend = np.zeros(len(c), int)
            cur, k = 0, 0
            for i in range(len(c)):
                while k < len(ev) and ev[k]["j"] <= i:
                    cur, k = ev[k]["dir"], k + 1
                trend[i] = cur
            close = pd.DatetimeIndex(F["close_time_utc"]).as_unit("ns").asi8
            self.tf[tf] = (close, trend, hi, lo)

    def at(self, tf: str, t_ns: int):
        close, trend, hi, lo = self.tf[tf]
        i = int(np.searchsorted(close, t_ns, side="right")) - 1
        return (0, np.nan, np.nan) if i < 0 else (int(trend[i]), float(hi[i]), float(lo[i]))


def load_trades() -> pd.DataFrame:
    parts = []
    v22 = pd.concat([pd.read_csv(OUT / f"v22_{p}.csv") for p in SET_A + SET_B])
    ob = v22[(v22.model == "smc_ob") & (v22.tf == "H1") & (v22.target == "3R")]
    parts.append(ob[ob.d1h4.astype(bool)].assign(strategy="smc_ob"))
    toni = v22[(v22.model == "toni") & (v22.tf == "H1") & (v22.target == "liq") & v22.d1.astype(bool)]
    parts.append(toni.assign(strategy="toni"))
    lin = v22[(v22.model == "lingard") & (v22.tf == "H4") & (v22.target == "5R") & v22.d1.astype(bool)
              & v22.session.fillna("").ne("")]
    parts.append(lin.assign(strategy="lingard"))
    v23 = pd.concat([pd.read_csv(OUT / f"v23_{p}.csv") for p in SET_A + SET_B])
    v23 = v23[v23.ie_h4_d1trend.astype(bool)]
    ent = ob.drop_duplicates(["pair", "t_dec", "side"])[["pair", "t_dec", "side", "e"]]
    parts.append(v23.merge(ent, on=["pair", "t_dec", "side"], how="inner").assign(strategy="irl_erl"))
    v26 = pd.read_csv(OUT / "v26_trades.csv")
    parts.append(v26[v26.filled.astype(bool)].assign(strategy="ore_poi"))
    d = pd.concat([p[["pair", "strategy", "side", "t_dec", "e", "R"]] for p in parts], ignore_index=True)
    d = d[d.R.notna()]
    # CRT: one number per setup
    cols = ["pair", "range_tf", "range_open", "k", "direction", "decision_time", "session", "status", "R",
            "entry", "htf_fvg", "htf_ob", "trend_struct", "friday_late"]
    crt = []
    for files, pairs in ((["trades_design.csv", "trades_check.csv"], SET_A), (["fvg_fresh_trades.csv"], SET_B)):
        for f in files:
            for ch in pd.read_csv(OUT / f, usecols=cols, chunksize=500_000, low_memory=False):
                ch = ch[ch.pair.isin(pairs)]
                crt.append(ch[ore_rules(ch) & (ch.status == "filled") & ch.R.notna()])
    c = pd.concat(crt, ignore_index=True)
    c = c.groupby(["pair", "range_tf", "range_open", "k", "direction"]).agg(
        R=("R", "mean"), e=("entry", "mean"), t=("decision_time", "first")).reset_index()
    c["t_dec"] = pd.to_datetime(c.t, utc=True).map(lambda x: x.value)
    c["side"] = c.direction
    d = pd.concat([d, c.assign(strategy="crt")[["pair", "strategy", "side", "t_dec", "e", "R"]]], ignore_index=True)
    return d


def features(d: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for pair, g in d.groupby("pair"):
        cx = Context(pair)
        for r in g.itertuples():
            s = 1 if r.side == "long" else -1
            tr4, hi4, lo4 = cx.at("H4", int(r.t_dec))
            _, hi1, lo1 = cx.at("D1", int(r.t_dec))
            mid4, mid1 = (hi4 + lo4) / 2, (hi1 + lo1) / 2
            rows.append({"idx": r.Index, "h4_confirm": tr4 == s,
                         "pd_h4": bool((r.e > mid4) if s == -1 else (r.e < mid4)) if not np.isnan(mid4) else False,
                         "pd_d1": bool((r.e > mid1) if s == -1 else (r.e < mid1)) if not np.isnan(mid1) else False})
        print(pair, len(g), flush=True)
    f = pd.DataFrame(rows).set_index("idx")
    return d.join(f)


def verdict(d: pd.DataFrame):
    a = d[d.pair.isin(SET_A) & (d.t_dec < CUT_A)]
    b = d[d.pair.isin(SET_B)]
    out = []
    rules = {"1: H4 confirm": "h4_confirm", "2: premium/discount H4": "pd_h4", "2b: premium/discount D1": "pd_d1",
             "1+2": None}
    for strat in ["crt", "smc_ob", "irl_erl", "toni", "lingard", "ore_poi", "ALL"]:
        ga = a if strat == "ALL" else a[a.strategy == strat]
        gb = b if strat == "ALL" else b[b.strategy == strat]
        need = 30 if strat == "ALL" else 20
        for name, col in rules.items():
            row = {"strategy": strat, "rule": name}
            ok = True
            for tag, g in (("A", ga), ("B", gb)):
                m = (g.h4_confirm & g.pd_h4) if col is None else g[col]
                f = g[m]
                base = g.R.mean()
                row.update({f"{tag}_all_n": len(g), f"{tag}_all": round(base, 3), f"{tag}_kept_n": len(f),
                            f"{tag}_kept": round(f.R.mean(), 3) if len(f) else np.nan,
                            f"{tag}_dropped": round(g[~m].R.mean(), 3) if (~m).any() else np.nan})
                ok &= len(f) >= need and f.R.mean() > 0 and f.R.mean() >= base + 0.10
            row["PASS"] = bool(ok)
            out.append(row)
    return pd.DataFrame(out)


if __name__ == "__main__":
    d = features(load_trades())
    d.to_pickle(OUT / "v28_features.pkl")
    pd.set_option("display.width", 250)
    v = verdict(d)
    v.to_csv(OUT / "v28_results.csv", index=False)
    print(v.to_string(index=False))

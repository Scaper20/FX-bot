"""Independent audit of every Inter Equity setup found by backtest/liquidity_ie.py.

Written separately on purpose: it works in REAL prices (no mirroring) with its own swing check, so a
bug in the detector can't pass its own test. Checks each setup against the raw candles of its timeframe.

    python -m backtest.audit_liquidity
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import pandas as pd

from engine import config as K
from engine.candles import clean, load_m1_csv, resample

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "backtest" / "out"


def is_high(H, k):
    return all(H[k] > H[k + d] for d in (-2, -1, 1, 2))


def is_low(L, k):
    return all(L[k] < L[k + d] for d in (-2, -1, 1, 2))


def audit_sniper(s, O, H, L, C, Eo, Ec, sp, tol) -> list[str]:
    i = s["idx"]
    c1, c2, c3, c4 = i["c1"], i["c2"], i["c3"], i["c4"]
    e, stop, tgt = s["e_real"], s["stop_real"], s["target_real"]
    bad = []
    if not (c2 == c1 + 1 and c3 == c2 + 1 and c4 == c3 + 1):
        bad.append("candles not consecutive")
    if s["mir"]:                                                    # BUY
        if not L[c2] < L[c1]:
            bad.append("C2 did not sweep below C1 low")
        if not C[c2] > L[c1]:
            bad.append("C2 did not close back above C1 low")
        if not L[c3] > L[c2]:
            bad.append("C3 low not above C2 low")
        if not C[c3] > O[c3]:
            bad.append("C3 not bullish")
        want = L[c3] if s["entry_kind"] == "edge" else (L[c3] + L[c2]) / 2
        if abs(e - want) > tol:
            bad.append("entry not at C3 low / zone middle")
        if abs(stop - (L[c2] - 2 * sp)) > tol:
            bad.append("stop not 2 spreads below C2 low")
        k = s["target_idx"]
        if abs(tgt - H[k]) > tol or not is_high(H, k) or k > c3 - 2 or H[k + 1:c3 + 1].max() >= H[k]:
            bad.append("target is not an intact swing high known at C3")
        if not tgt > e or (tgt - e - sp) / (e - stop + sp) < K.MIN_RR - 1e-9:
            bad.append("target below 1:3")
    else:                                                           # SELL
        if not H[c2] > H[c1]:
            bad.append("C2 did not sweep above C1 high")
        if not C[c2] < H[c1]:
            bad.append("C2 did not close back below C1 high")
        if not H[c3] < H[c2]:
            bad.append("C3 high not below C2 high")
        if not C[c3] < O[c3]:
            bad.append("C3 not bearish")
        want = H[c3] if s["entry_kind"] == "edge" else (H[c3] + H[c2]) / 2
        if abs(e - want) > tol:
            bad.append("entry not at C3 high / zone middle")
        if abs(stop - (H[c2] + 2 * sp)) > tol:
            bad.append("stop not 2 spreads above C2 high")
        k = s["target_idx"]
        if abs(tgt - L[k]) > tol or not is_low(L, k) or k > c3 - 2 or L[k + 1:c3 + 1].min() <= L[k]:
            bad.append("target is not an intact swing low known at C3")
        if not tgt < e or (e - tgt - sp) / (stop - e + sp) < K.MIN_RR - 1e-9:
            bad.append("target below 1:3")
    if (s["window_start"], s["window_end"]) != (int(Eo[c4]), int(Ec[c4])):
        bad.append("order not limited to C4")
    return bad


def audit_core(s, O, H, L, C, Eo, Ec, sp, tol) -> list[str]:
    i = s["idx"]
    bl, leg, hr, lb, pl = i["broken_low"], i["leg_low"], i["retail_high"], i["lb"], i["place"]
    e, stop, tgt = s["e_real"], s["stop_real"], s["target_real"]
    bad = []
    if s["mir"]:                                                    # BUY (buyers induced, then trapped)
        if not is_high(H, bl):
            bad.append("broken level is not a swing high")
        if not (bl + 2 < leg and H[leg] > H[bl]):
            bad.append("leg high did not take the swing high after it formed")
        if not (hr > leg and is_low(L, hr) and pl == hr + 2):
            bad.append("retail low not a swing low after the leg high, placed when confirmed")
        if H[leg + 1:pl + 1].max() > H[leg]:
            bad.append("leg extended before the order (should have reset)")
        if abs(e - L[hr]) > tol:
            bad.append("entry not at the retail low")
        if not (lb < hr and is_low(L, lb) and L[lb] < e) or abs(stop - (L[lb] - 2 * sp)) > tol:
            bad.append("stop not below a swing low from the left (liquidity block)")
        if any(is_low(L, x) and L[x] < e for x in range(lb + 1, hr)):
            bad.append("a more recent liquidity block was skipped")
        if not (tgt >= H[leg] - tol) or (tgt - e - sp) / (e - stop + sp) < K.MIN_RR - 1e-9:
            bad.append("target not at/above the leg high, or below 1:3")
    else:                                                           # SELL
        if not is_low(L, bl):
            bad.append("broken level is not a swing low")
        if not (bl + 2 < leg and L[leg] < L[bl]):
            bad.append("leg low did not take the swing low after it formed")
        if not (hr > leg and is_high(H, hr) and pl == hr + 2):
            bad.append("retail high not a swing high after the leg low, placed when confirmed")
        if L[leg + 1:pl + 1].min() < L[leg]:
            bad.append("leg extended before the order (should have reset)")
        if abs(e - H[hr]) > tol:
            bad.append("entry not at the retail high")
        if not (lb < hr and is_high(H, lb) and H[lb] > e) or abs(stop - (H[lb] + 2 * sp)) > tol:
            bad.append("stop not above a swing high from the left (liquidity block)")
        if any(is_high(H, x) and H[x] > e for x in range(lb + 1, hr)):
            bad.append("a more recent liquidity block was skipped")
        if not (tgt <= L[leg] + tol) or (e - tgt - sp) / (stop - e + sp) < K.MIN_RR - 1e-9:
            bad.append("target not at/below the leg low, or below 1:3")
    if s["window_start"] != int(Eo[pl + 1]):
        bad.append("order window doesn't start after the retail high is confirmed")
    return bad


def main() -> int:
    setups = pd.read_pickle(OUT / "liquidity_ie_setups.pkl")
    kinds, n_bad, n = Counter(), 0, Counter()
    examples = []
    for pair in K.PAIRS:
        m1, _ = clean(load_m1_csv(ROOT / K.PAIRS[pair]["file"]))
        sp = K.PAIRS[pair]["spread"]
        tol = 1e-7 if pair == "GBPUSD" else 1e-4
        for tf in ("D1", "H4", "H1", "M15", "M5"):
            E = resample(m1, tf, "utc0")
            O, H, L, C = (E[k].to_numpy(float) for k in ("open", "high", "low", "close"))
            Eo = E.index.as_unit("ns").asi8
            Ec = pd.DatetimeIndex(E["close_time_utc"]).as_unit("ns").asi8
            for s in (x for x in setups if x["pair"] == pair and x["tf"] == tf):
                fn = audit_sniper if s["model"] == "sniper" else audit_core
                bad = fn(s, O, H, L, C, Eo, Ec, sp, tol)
                n[s["model"]] += 1
                if bad:
                    n_bad += 1
                    kinds.update(bad)
                    if len(examples) < 5:
                        examples.append((pair, tf, s["model"], s["idx"], bad))
    print(f"audited: {dict(n)} setups, {n_bad} with problems")
    for k, v in kinds.most_common():
        print(f"  {v:6d}  {k}")
    for ex in examples:
        print(ex)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

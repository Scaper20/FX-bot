"""SMC strategies on external market structure (spec v22). One place for the rules, used by the backtest
(backtest/smc_v22.py) and the live scanner (engine/smc_live.py), so they can't drift apart.

All prices are real (not mirrored). Each setup: dict(model, variant, dir (+1 buy / -1 sell), decision (index of
the candle whose close makes the setup known), entry, far (stop before the spread buffer), liq (structure
target or None), zone (first, last, low, high), line (from_idx, to_idx, price, label), valid (candles the limit
stays valid)). The caller adds 2 spreads to the stop and sets the R targets.
"""
from __future__ import annotations

import numpy as np

from . import structure as S
from .smc_structure import ore_order_block

LOOK = 30          # candles to wait for Toni's inducement
VALID = 20         # candles a limit stays valid (Toni, Lingard); the order-block strategy uses 12


def _zone_low_high(ob):
    return min(ob["near"], ob["far"]), max(ob["near"], ob["far"])


# ------------------------------------------------------------------ order-block strategy (v21 test B)

def orderblock_setups(o, h, l, c, events) -> list[dict]:
    """H1 MSS; Ore's 2/3-candle order block at the top/bottom of the move, complete by the MSS candle;
    limit at the first candle's near edge; stop beyond the block / move extreme."""
    out = []
    for ev in events:
        if ev["kind"] != "MSS":
            continue
        j, d, p = ev["j"], ev["dir"], ev["protected"]
        ob = ore_order_block(o, h, l, c, p, d, ahead=min(2, j - p))
        if not ob:
            continue
        ext = h[p] if d == -1 else l[p]
        far = max(ext, ob["far"]) if d == -1 else min(ext, ob["far"])
        e = ob["near"]
        if (d == -1 and not (far > e > c[j])) or (d == 1 and not (far < e < c[j])):
            continue
        lo, hi = _zone_low_high(ob)
        out.append({"model": "smc_ob", "variant": ob["kind"], "dir": d, "decision": j, "entry": e, "far": far,
                    "liq": None, "zone": (ob["first"], ob["last"], lo, hi),
                    "line": (ev["broken"], j, ev["level"], "MSS"), "valid": 12, "origin": p})
    return out


# ------------------------------------------------------------------ Toni Iyke

def _levels_broken(h, l, c, sw, p, j, d):
    """Swing levels (5-bar fractals) the leg from p to j closed beyond and that were intact when the leg began."""
    out = []
    for s in range(max(0, p - 200), j - 1):
        if not sw[s] or s + 2 > j:
            continue
        lvl = h[s] if d == 1 else l[s]
        seg = c[s + 1:p + 1] if s < p else np.array([])
        if len(seg) and ((d == 1 and seg.max() > lvl) or (d == -1 and seg.min() < lvl)):
            continue                                   # already broken before the leg
        leg = c[max(p, s) + 1:j + 1]
        if len(leg) and ((d == 1 and leg.max() > lvl) or (d == -1 and leg.min() < lvl)):
            out.append(s)
    return out


def toni_setups(o, h, l, c, events) -> list[dict]:
    """MSS (reversal) or multiple BOS (>= 2 levels broken in one leg, body closes) -> inducement (first pullback,
    then a body close beyond the structure candle's close) -> POI: breakers (bodies of the broken levels) or
    Ore's order block at the origin; unmitigated by the inducement leg; the one closest to the inducement."""
    sh, sl = S.swing_flags(h, l)
    n, out = len(c), []
    for ev in events:
        j, d, p = ev["j"], ev["dir"], ev["protected"]
        lv = _levels_broken(h, l, c, sh if d == 1 else sl, p, j, d)
        if ev["kind"] == "MSS":
            struct = "MSS"
        elif len(set(lv) | {ev["broken"]}) >= 2:
            struct = "multiple BOS"
        else:
            continue                                   # single BOS: ignored
        pull = next((k for k in range(j + 1, min(j + LOOK, n))
                     if (c[k] < o[k] if d == 1 else c[k] > o[k]) or (l[k] < l[k - 1] if d == 1 else h[k] > h[k - 1])),
                    None)
        if pull is None:
            continue
        v = next((m for m in range(pull + 1, min(j + LOOK, n)) if (c[m] > c[j] if d == 1 else c[m] < c[j])), None)
        if v is None:
            continue
        ind = l[j + 1:v + 1].min() if d == 1 else h[j + 1:v + 1].max()
        cands = []
        for s in sorted(set(lv) | {ev["broken"]}):
            bt, bb = max(o[s], c[s]), min(o[s], c[s])
            if d == 1:
                cands.append(("breaker", bt, bt, l[s], (s, s, l[s], h[s])))
            else:
                cands.append(("breaker", bb, bb, h[s], (s, s, l[s], h[s])))
        ob = ore_order_block(o, h, l, c, p, d, ahead=min(2, j - p))
        if ob:
            f0 = ob["first"]
            body = abs(c[f0] - o[f0])
            if d == 1:
                wick = h[f0] - max(o[f0], c[f0])
                e = h[f0] if wick < body else max(o[f0], c[f0])
                cands.append(("order block", max(o[f0], c[f0]), e, ob["far"], (f0, ob["last"], *_zone_low_high(ob))))
            else:
                wick = min(o[f0], c[f0]) - l[f0]
                e = l[f0] if wick < body else min(o[f0], c[f0])
                cands.append(("order block", min(o[f0], c[f0]), e, ob["far"], (f0, ob["last"], *_zone_low_high(ob))))
        # rule 3 (unmitigated: the inducement leg never reached the body) and rule 4 (closest to the inducement)
        if d == 1:
            valid = [x for x in cands if x[1] < ind and x[2] < c[v] and x[3] < x[2]]
            pick = max(valid, key=lambda x: x[2]) if valid else None
            liq = h[j:v + 1].max()
        else:
            valid = [x for x in cands if x[1] > ind and x[2] > c[v] and x[3] > x[2]]
            pick = min(valid, key=lambda x: x[2]) if valid else None
            liq = l[j:v + 1].min()
        if pick is None:
            continue
        out.append({"model": "toni", "variant": f"{struct} · {pick[0]}", "dir": d, "decision": v, "entry": pick[2],
                    "far": pick[3], "liq": liq, "zone": pick[4], "line": (ev["broken"], j, ev["level"], struct),
                    "valid": VALID, "struct": "mss" if struct == "MSS" else "dbos", "inducement": ind})
    return out


# ------------------------------------------------------------------ Lingard

def lingard_setups(o, h, l, c, events, atr) -> list[dict]:
    """First BOS after an MSS (wick breaks): its pullback (protected swing) is the first-pullback liquidity;
    POI = Ore's order block beyond that liquidity, nearest to it (within 1.5 ATR), inside the move that made the
    new trend. Limit at the block's near edge, stop beyond it; liq = the BOS extreme (next liquidity)."""
    out, first_after = [], {}
    for ev in events:
        d = ev["dir"]
        if ev["kind"] == "MSS":
            first_after[d] = ev                       # waiting for the first BOS in this direction
            first_after.pop(-d, None)
            continue
        mss = first_after.pop(d, None)
        if mss is None:
            continue
        j, p = ev["j"], ev["protected"]
        if np.isnan(atr[j]):
            continue
        liq_px = l[p] if d == 1 else h[p]
        best = None
        for origin in range(max(0, mss["protected"] - 2), ev["broken"] + 1):
            ob = ore_order_block(o, h, l, c, origin, d)
            if not ob or ob["last"] > j:
                continue
            e = ob["near"]
            if d == 1 and e < liq_px and liq_px - e <= 1.5 * atr[j] and ob["far"] < e:
                if best is None or e > best["near"]:
                    best = ob
            if d == -1 and e > liq_px and e - liq_px <= 1.5 * atr[j] and ob["far"] > e:
                if best is None or e < best["near"]:
                    best = ob
        if best is None:
            continue
        if (d == 1 and best["near"] >= c[j]) or (d == -1 and best["near"] <= c[j]):
            continue
        out.append({"model": "lingard", "variant": "first pullback", "dir": d, "decision": j, "entry": best["near"],
                    "far": best["far"], "liq": h[j] if d == 1 else l[j], "zone": (best["first"], best["last"],
                                                                                  *_zone_low_high(best)),
                    "line": (ev["broken"], j, ev["level"], "BOS"), "valid": VALID, "liquidity": float(liq_px),
                    "pullback": p})
    return out


# ------------------------------------------------------------------ Ore's liquidity model (spec v24)

VALID_ORE = 30


def _zone_entry(lo, hi, d):
    """Near edge and far edge of a zone for a trade in direction d (sell: enter at the bottom, stop at the top)."""
    return (lo, hi) if d == -1 else (hi, lo)


def ore_reversal_setups(o, h, l, c, events) -> list[dict]:
    """MSS, then the next event is a BOS the same way; its protected swing is Liq (the trap). POI above Liq (sell):
    OB = Ore's block at the top of the move; BB = Ore's opposite block at the swing the MSS broke (failed OB).
    Limit placed at the BOS close."""
    out = []
    for e1, e2 in zip(events[:-1], events[1:]):
        if e1["kind"] != "MSS" or e2["kind"] != "BOS" or e2["dir"] != e1["dir"]:
            continue
        d, j = e1["dir"], e2["j"]
        li = e2["protected"]
        liq = h[li] if d == -1 else l[li]
        cands = []
        top = e1["protected"]
        ob = ore_order_block(o, h, l, c, top, d, ahead=max(0, min(2, e1["j"] - top)))
        if ob:
            lo, hi = _zone_low_high(ob)
            ext = h[top] if d == -1 else l[top]
            e = ob["near"]
            far = max(hi, ext) if d == -1 else min(lo, ext)
            cands.append(("OB", e, far, (ob["first"], ob["last"], lo, hi), ob["kind"]))
        s = e1["broken"]
        bb = ore_order_block(o, h, l, c, s, -d, ahead=max(0, min(2, e1["j"] - s)))
        if bb:
            lo, hi = _zone_low_high(bb)
            e, far = _zone_entry(lo, hi, d)
            cands.append(("BB", e, far, (bb["first"], bb["last"], lo, hi), bb["kind"]))
        for name, e, far, zone, shape in cands:
            beyond_liq = e > liq if d == -1 else e < liq
            ahead_px = e > c[j] if d == -1 else e < c[j]
            right = far > e if d == -1 else far < e
            if not (beyond_liq and ahead_px and right):
                continue
            out.append({"model": "ore_rev", "variant": name, "shape": shape, "dir": d, "decision": j, "entry": float(e),
                        "far": float(far), "liq": None, "zone": zone, "line": (e1["broken"], e1["j"], e1["level"], "MSS"),
                        "valid": VALID_ORE, "liq_idx": li, "liq_px": float(liq), "top": top,
                        "bos": (e2["broken"], j, e2["level"])})
    return out


def ore_continuation_setups(o, h, l, c, events) -> list[dict]:
    """Two BOS in a row the same way; Liq = the second BOS's pullback; BB = Ore's opposite block at the swing the
    first BOS broke (else that swing candle wick to wick), on the far side of Liq. Limit placed at the second BOS."""
    out = []
    for a, b in zip(events[:-1], events[1:]):
        if a["kind"] != "BOS" or b["kind"] != "BOS" or a["dir"] != b["dir"]:
            continue
        d, j = b["dir"], b["j"]
        li = b["protected"]
        liq = l[li] if d == 1 else h[li]
        s = a["broken"]
        bb = ore_order_block(o, h, l, c, s, -d, ahead=max(0, min(2, a["j"] - s)))
        if bb:
            lo, hi = _zone_low_high(bb)
            zone, shape = (bb["first"], bb["last"], lo, hi), bb["kind"]
        else:
            lo, hi = float(l[s]), float(h[s])
            zone, shape = (s, s, lo, hi), "swing candle"
        e, far = _zone_entry(lo, hi, d)
        beyond_liq = e < liq if d == 1 else e > liq
        ahead_px = e < c[j] if d == 1 else e > c[j]
        if not (beyond_liq and ahead_px):
            continue
        out.append({"model": "ore_cont", "variant": "BB", "shape": shape, "dir": d, "decision": j, "entry": float(e),
                    "far": float(far), "liq": None, "zone": zone, "line": (b["broken"], j, b["level"], "BOS"),
                    "valid": VALID_ORE, "liq_idx": li, "liq_px": float(liq), "first_bos": (a["broken"], a["j"], a["level"])})
    return out

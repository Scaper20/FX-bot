"""Merge a freshly built practice set into the live one without losing anyone's answers.

    python scripts/merge_practice.py NEW_FILE

- Every setup in NEW_FILE is active.
- Old setups stay in the file (answers already given keep counting in everyone's stats), but any
  whose C2 did not close inside C1's body (Ore's rule, 23 Nov 2026) are marked retired and never
  served again. Old setups that do meet the rule stay active.
"""
from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from web import chartdata, service  # noqa: E402


def body_ok(item: dict) -> bool:
    c = item["card"]
    ch = chartdata.practice_chart(item["id"]) or {}
    sec = lambda t: int(pd.Timestamp(t).value // 10**9)
    bars = {b[0]: b for b in (ch.get("before") or {}).get(c["range_tf"], [])}
    r, s = bars.get(sec(c["range_open"])), bars.get(sec(c["sweep_open"]))
    if not r or not s:
        return False
    return min(r[1], r[4]) < s[4] < max(r[1], r[4])


def main() -> int:
    new = json.load(gzip.open(sys.argv[1], "rt"))
    old = service.practice_items()
    new_ids = {it["id"] for it in new}
    for it in new:
        assert body_ok(it), f"new setup {it['id']} breaks the body rule"
    kept, retired = [], 0
    for it in old:
        if it["id"] in new_ids:
            continue
        it = dict(it)
        it["retired"] = not body_ok(it)
        retired += it["retired"]
        kept.append(it)
    merged = new + kept
    with gzip.open(service.PRACTICE_FILE, "wt") as f:
        json.dump(merged, f, separators=(",", ":"))
    active = sum(1 for it in merged if not it.get("retired"))
    print(f"{len(new)} new + {len(kept)} old ({retired} retired) = {len(merged)} setups, {active} active")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

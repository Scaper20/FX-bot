import numpy as np
import pandas as pd

from backtest.walkforward import verdict, walk


def make(edge_unit_mean, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for y in range(2021, 2027):
        for u in range(20):
            mean = edge_unit_mean if u == 0 else 0.0
            for r in rng.normal(mean, 1.0, 120):
                rows.append({"unit": f"u{u}", "time": f"{y}-06-01T00:00:00Z", "R": r})
    return pd.DataFrame(rows)


def test_real_edge_is_found_and_passes():
    t, _ = walk(make(0.5))
    assert (t["A unit"] == "u0").all()
    assert verdict(t, "A")["pass"]


def test_noise_does_not_pass():
    # With no edge anywhere, a blind pick still passes by luck sometimes (3+ of 4 positive years is
    # about a 1-in-3 coin event), so a single pass means little; a real edge passes every time.
    passes = sum(verdict(walk(make(0.0, seed=s))[0], "A")["pass"] for s in range(10))
    real = sum(verdict(walk(make(0.5, seed=s))[0], "A")["pass"] for s in range(10))
    assert passes < 6 and real == 10

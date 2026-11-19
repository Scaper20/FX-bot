"""Fixed settings. Changing anything here after the Final run contaminates it."""

# Exness MT5 server time is GMT+0 (Ore saw the Sunday candle, 20 Nov 2026).
DAY_CLOSE = "utc0"

# Spread + slippage per trade, in price units. Assumption until Ore sends his
# real Exness Standard spreads. Results are also reported at 2x.
PAIRS = {
    "GBPUSD": {"spread": 0.00010, "pip": 0.0001, "file": "data/gbpusd-m1-bid-2021-11-01-2026-11-19.csv"},
    "XAUUSD": {"spread": 0.35, "pip": 0.1, "file": "data/xauusd-m1-bid-2021-11-01-2026-11-19.csv"},
}

RANGE_TO_ENTRY = {"D1": ("H1", "M15"), "H4": ("M15", "M5")}
MID_TF = {"D1": "H4", "H4": "H1"}

# Range candle OPEN time must fall in [start, end). Data after `end` is never loaded.
PERIODS = {
    "design": ("2021-11-01", "2024-01-01"),
    "check": ("2024-01-01", "2025-01-01"),
    "final": ("2025-01-01", "2026-11-19"),
}

MIN_RR = 3.0
HOLD_RANGE_CANDLES = 5     # time stop after fill
HTF_LOOKBACK = 60          # range-TF candles searched for HTF FVG/OB/swings
SWING_N = 2                # candles each side for a swing
OB_SEARCH = 5              # entry-TF candles back from the sweep high to find the order block
MSNR_TOL_ATR = 0.10        # "at a level" = within 0.1 x D1 ATR(14)

# Pre-registered pass rule (spec section 6)
MIN_TRADES_DESIGN = 60
MIN_TRADES_CHECK = 25

"""Fixed settings. Changing anything here after the Final run contaminates it."""
import os

# Exness MT5 server time is GMT+0 (Ore saw the Sunday candle, 20 Nov 2026).
DAY_CLOSE = "utc0"

# CRT: C2 must close back inside C1's BODY (open-close), Ore's rule of 23 Nov 2026.
# CRT_CLOSE=range reproduces the older (looser) tests, which accepted any close inside C1's high-low.
CRT_CLOSE = os.environ.get("CRT_CLOSE", "body")

# Spread per trade, in price units: Ore's Exness Standard spreads, London session (23 Nov 2026).
PAIRS = {
    "GBPUSD": {"spread": 0.00010, "pip": 0.0001, "file": "data/gbpusd-m1-bid-2021-11-01-2026-11-19.csv"},
    "XAUUSD": {"spread": 0.24, "pip": 0.1, "file": "data/xauusd-m1-bid-2021-11-01-2026-11-19.csv"},
}

# Pairs the LIVE scanner runs (28 Nov 2026, Ore: add EUR/USD and silver). PAIRS above stays the backtests' pair set.
# Silver (XAG/USD) is only on Twelve Data's paid Grow/Venture plans: move it into LIVE_PAIRS once the plan allows.
LIVE_PAIRS = {
    **PAIRS,
    "EURUSD": {"spread": 0.00010, "pip": 0.0001, "file": "data/eurusd-m1-bid-2021-11-01-2026-11-19.zip"},
    # 28 Nov 2026, Ore: add USD/CHF either way (spec v33 did not select it). Spread assumed 1.5 pips until Ore gives his.
    "USDCHF": {"spread": 0.00015, "pip": 0.0001, "file": "data/td/usdchf-m5.csv.gz"},
}
PAID_PLAN_PAIRS = {
    "XAGUSD": {"spread": 0.025, "pip": 0.01, "file": "data/xagusd-m1-bid-2021-11-01-2026-11-19.zip"},
}
NAMES = {"GBPUSD": "GBP/USD", "XAUUSD": "Gold", "EURUSD": "EUR/USD", "XAGUSD": "Silver", "USDCHF": "USD/CHF"}
METALS = ("XAU", "XAG", "XPT")


def pair_name(pair: str) -> str:
    return NAMES.get(pair, f"{pair[:3]}/{pair[3:]}")


def is_metal(pair: str) -> bool:
    return pair[:3] in METALS


def decimals(pair: str) -> int:
    """Price decimals: gold 2, silver 3, JPY pairs 3, other FX 5."""
    return {"XAU": 2, "XAG": 3, "XPT": 2}.get(pair[:3], 3 if pair.endswith("JPY") else 5)


def to_usd(pair: str, amount: float, price: float) -> float:
    """An amount in the pair's quote currency, in USD: XXX/USD as is, USD/XXX divided by the price."""
    if pair.endswith("USD"):
        return amount
    if pair.startswith("USD"):
        return amount / price
    raise ValueError(f"{pair}: no USD leg, needs a conversion rate")


def notional_usd(pair: str, price: float, contract: float) -> float:
    """Value of one lot in USD: price x contract for XXX/USD, the contract itself for USD/XXX."""
    return contract if pair.startswith("USD") else to_usd(pair, price * contract, price)


def fmt_price(pair: str, x) -> str:
    return "—" if x is None else f"{float(x):,.{decimals(pair)}f}"


def fmt_distance(pair: str, d: float) -> str:
    """'12.3 pips' for FX, '$4.20' for metals."""
    if is_metal(pair):
        return f"${abs(d):,.{max(2, decimals(pair))}f}"
    pip = (LIVE_PAIRS.get(pair) or PAID_PLAN_PAIRS.get(pair) or {}).get("pip") or (0.01 if pair.endswith("JPY") else 0.0001)
    return f"{abs(d) / pip:.1f} pips"


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

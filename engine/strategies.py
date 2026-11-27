"""The strategies the scanner runs. Each card carries card["strategy"] = one of these ids.
Results quoted here come from the reports in backtest/reports (after Ore's spreads)."""
from __future__ import annotations

STRATEGIES = {
    "crt": {
        "name": "CRT",
        "long": "Candle Range Theory",
        "rules_word": "your CRT rules",
        "short": "D1/H4 range candle swept, C2 closes back inside C1's body, lower-timeframe trigger",
        "evidence": ("No edge found: targets reached at the chance rate in every test, about zero before costs "
                     "and negative after the spread (specs v1–v12)."),
        "report": "backtest/reports/body_close_v12.md",
        "alert": "new",
        "practice": True,
    },
    "smc_ob": {
        "name": "Order block",
        "long": "H1 order block · D1+H4 trend",
        "rules_word": "the order-block rules",
        "short": "D1 and H4 trends agree, H1 market structure shift, Ore's 2/3-candle order block at the top/bottom, 3R",
        "evidence": ("Rebuilt 27 Nov 2026 on real market structure (spec v22): 28 trades in 5 years on GBP/USD + "
                     "gold, −0.59R a trade; −0.31R on EUR/USD + silver. No edge found; live by Ore's decision."),
        "report": "backtest/reports/smc_v22.md",
        "alert": "smc",
        "practice": False,
    },
    "toni": {
        "name": "Toni Iyke",
        "long": "Toni Iyke · structure → inducement → POI",
        "rules_word": "Toni's rules",
        "short": "D1 trend, H1 MSS or multiple BOS, inducement, closest untouched breaker/order block, target the swing point",
        "evidence": ("Spec v22 (real market structure): H1 multiple BOS with the D1 trend +0.03R over 155 trades "
                     "(4 of 5 years) on GBP/USD + gold but −0.15R on EUR/USD + silver; MSS setups −0.15R. "
                     "No edge found; live by Ore's decision."),
        "report": "backtest/reports/smc_v22.md",
        "alert": "toni",
        "practice": False,
    },
    "lingard": {
        "name": "Lingard",
        "long": "Lingard · first-pullback liquidity → order block",
        "rules_word": "Lingard's rules",
        "short": "D1 trend, H4 first BOS after an MSS, order block beyond the first pullback, London/NY, 5R",
        "evidence": ("Spec v22 (real market structure): H4 with the D1 trend 17 trades in 5 years on GBP/USD + gold, "
                     "−0.39R; H1 56 trades −0.03R. Too few trades to judge; no edge found. Live by Ore's decision."),
        "report": "backtest/reports/smc_v22.md",
        "alert": "lingard",
        "practice": False,
    },
}
DEFAULT = "crt"


def strategy_of(card: dict) -> str:
    """Older cards have no 'strategy' field: CRT, unless they carry the order-block model id."""
    if card.get("strategy") in STRATEGIES:
        return card["strategy"]
    return "smc_ob" if card.get("model") == "smc_h1_ob" else DEFAULT


def name(card: dict) -> str:
    s = STRATEGIES[strategy_of(card)]
    return s["long"] if strategy_of(card) != "crt" else f"{card.get('range_tf', '')} CRT".strip()

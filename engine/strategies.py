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
        "long": "H1 order block · D1+H4 bias",
        "rules_word": "the order-block rules",
        "short": "D1 and H4 structure agree, H1 market structure shift, limit at the order block's open, 3R",
        "evidence": ("Drawing review 27 Nov 2026: this version reads market structure from tiny swings, so its "
                     "'MSS' and order block are often minor candles. Its old backtest (+0.27R on GBP/USD + gold, "
                     "−0.12R on EUR/USD + silver) is not reliable; a correct rebuild (spec v21) found no edge."),
        "report": "backtest/reports/smc_bias_v16.md",
        "alert": "smc",
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

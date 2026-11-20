"""Candlestick charts as inline SVG (no JavaScript library), plus a text equivalent."""
from __future__ import annotations

from html import escape

import pandas as pd

INK, MUTED, GRID = "#0F1B2D", "#5B6577", "#E3E7ED"
UP, DOWN, AMBER, BLUE = "#0B7A5A", "#C8473B", "#D99A1E", "#2F5D9E"


def _fmt(pair: str, x: float) -> str:
    return f"{x:.5f}" if pair == "GBPUSD" else f"{x:.2f}"


def candles_svg(candles: list, levels: list[dict] | None = None, markers: list[dict] | None = None,
                shade: list[dict] | None = None, pair: str = "GBPUSD", title: str = "", width: int = 720,
                height: int = 300, after_from: str | None = None) -> str:
    """candles: [[iso_time, o, h, l, c], ...]. levels: {price, label, color, dash}.
    markers: {time, label}. shade: {start, end, color} by candle time (ISO). after_from: candles
    at/after this time are drawn faded (what happened later, in practice reveals)."""
    if not candles:
        return '<p class="muted">No candles to draw.</p>'
    levels, markers, shade = levels or [], markers or [], shade or []
    pad_l, pad_r, pad_t, pad_b = 8, 96, 24, 22
    lo = min(c[3] for c in candles)
    hi = max(c[2] for c in candles)
    for lv in levels:
        if lv.get("price") is not None:
            lo, hi = min(lo, lv["price"]), max(hi, lv["price"])
    span = (hi - lo) or 1.0
    lo, hi = lo - span * 0.04, hi + span * 0.04
    n = len(candles)
    plot_w = width - pad_l - pad_r
    step = plot_w / n
    body_w = max(1.0, step * 0.62)

    def y(p):
        return pad_t + (hi - p) / (hi - lo) * (height - pad_t - pad_b)

    def x(i):
        return pad_l + step * (i + 0.5)

    times = [pd.Timestamp(c[0]) for c in candles]

    def idx_of(t):
        t = pd.Timestamp(t)
        for i, ti in enumerate(times):
            if ti >= t:
                return i
        return n - 1

    out = [f'<svg viewBox="0 0 {width} {height}" class="chart" role="img" aria-label="{escape(title)}" '
           f'preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg">']
    for s in shade:
        a, b = idx_of(s["start"]), idx_of(s["end"]) if s.get("end") else n - 1
        out.append(f'<rect x="{x(a) - step / 2:.1f}" y="{pad_t}" width="{max(step, (b - a + 1) * step):.1f}" '
                   f'height="{height - pad_t - pad_b}" fill="{s.get("color", AMBER)}" opacity="0.10"/>')
    for k in range(5):                                   # light grid with price labels
        p = lo + (hi - lo) * k / 4
        out.append(f'<line x1="{pad_l}" x2="{width - pad_r}" y1="{y(p):.1f}" y2="{y(p):.1f}" stroke="{GRID}" stroke-width="1"/>')
    fade_from = idx_of(after_from) if after_from else None
    for i, (t, o, h, l, c) in enumerate(candles):
        col = UP if c >= o else DOWN
        op = 0.35 if (fade_from is not None and i >= fade_from) else 1.0
        top, bot = y(max(o, c)), y(min(o, c))
        out.append(f'<g opacity="{op}"><line x1="{x(i):.1f}" x2="{x(i):.1f}" y1="{y(h):.1f}" y2="{y(l):.1f}" '
                   f'stroke="{col}" stroke-width="1"/><rect x="{x(i) - body_w / 2:.1f}" y="{top:.1f}" '
                   f'width="{body_w:.1f}" height="{max(1.0, bot - top):.1f}" fill="{col}"/></g>')
    drawn = [lv for lv in levels if lv.get("price") is not None]
    for lv in drawn:
        yy = y(lv["price"])
        dash = ' stroke-dasharray="5 4"' if lv.get("dash") else ""
        out.append(f'<line x1="{pad_l}" x2="{width - pad_r}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="{lv.get("color", INK)}" '
                   f'stroke-width="1.3"{dash}/>')
    # labels: keep them at least 12px apart so they never print on top of each other
    placed = []
    for lv in sorted(drawn, key=lambda v: y(v["price"])):
        ly = y(lv["price"]) + 4
        if placed and ly - placed[-1] < 12:
            ly = placed[-1] + 12
        placed.append(ly)
        out.append(f'<text x="{width - pad_r + 4}" y="{ly:.1f}" font-size="11" fill="{lv.get("color", INK)}" '
                   f'class="mono">{escape(lv.get("label", ""))}</text>')
    for m in markers:
        xi = x(idx_of(m["time"]))
        out.append(f'<line x1="{xi:.1f}" x2="{xi:.1f}" y1="{pad_t}" y2="{height - pad_b}" stroke="{BLUE}" '
                   f'stroke-width="1" stroke-dasharray="2 3"/>')
        out.append(f'<text x="{xi + 3:.1f}" y="{pad_t - 8}" font-size="11" fill="{BLUE}">{escape(m["label"])}</text>')
    first, last = times[0], times[-1]
    out.append(f'<text x="{pad_l}" y="{height - 6}" font-size="11" fill="{MUTED}">{first:%d %b %H:%M} UTC</text>')
    out.append(f'<text x="{width - pad_r}" y="{height - 6}" font-size="11" fill="{MUTED}" text-anchor="end">'
               f'{last:%d %b %H:%M} UTC</text>')
    out.append("</svg>")
    return "".join(out)


def card_charts(card: dict, option: dict | None, after: list | None = None, decision: str | None = None) -> dict:
    """Two charts for a setup card: the range timeframe and the entry timeframe."""
    pair = card["pair"]
    f = lambda v: _fmt(pair, v)
    rng_levels = [
        {"price": card["range_high"], "label": f"High {f(card['range_high'])}", "color": INK, "dash": True},
        {"price": card["range_low"], "label": f"Low {f(card['range_low'])}", "color": INK, "dash": True},
        {"price": card["range_mid"], "label": "50%", "color": MUTED, "dash": True},
    ]
    shade = [{"start": card["range_open"], "end": card["range_open"], "color": AMBER}]
    if card.get("sweep_open"):
        shade.append({"start": card["sweep_open"], "end": card["sweep_open"], "color": BLUE})
    range_svg = candles_svg(card["chart"]["range"], rng_levels, shade=shade, pair=pair,
                            title=f"{pair} {card['range_tf']} range chart")
    lv = list(rng_levels)
    markers = []
    if option:
        lv += [{"price": option["entry"], "label": f"Entry {f(option['entry'])}", "color": AMBER},
               {"price": option["stop"], "label": f"Stop {f(option['stop'])}", "color": DOWN},
               {"price": option["target"], "label": f"Target {f(option['target'])}", "color": UP}]
        markers.append({"time": option["decision_time"], "label": "trigger"})
    entry_candles = card["chart"]["entry"] + (after or [])
    entry_svg = candles_svg(entry_candles, lv, markers, pair=pair, after_from=decision if after else None,
                            title=f"{pair} {card['chart'].get('entry_tf', '')} entry chart")
    return {"range": range_svg, "entry": entry_svg}


def text_equivalent(card: dict, option: dict | None, tz: str = "Africa/Lagos") -> str:
    pair = card["pair"]
    f = lambda v: _fmt(pair, v)
    loc = lambda t: pd.Timestamp(t).tz_convert(tz).strftime("%a %d %b %H:%M")
    side = "high" if card["direction"] == "short" else "low"
    parts = [
        f"{pair}, {card['range_tf']} range candle opened {loc(card['range_open'])}: high {f(card['range_high'])}, "
        f"low {f(card['range_low'])}, 50% {f(card['range_mid'])}.",
        f"The sweep candle (+{card['k']}) opened {loc(card['sweep_open'])}, traded beyond the range {side} to "
        f"{f(card['sweep_extreme'])} and closed back inside.",
    ]
    if option:
        parts.append(
            f"Trigger: {option['trigger']} on {option['entry_tf']} at {loc(option['decision_time'])}. "
            f"Option shown: {card['direction']} entry {f(option['entry'])}, stop {f(option['stop'])}, "
            f"target {f(option['target'])}, reward to risk {option['rr']} after spread.")
    return " ".join(parts)

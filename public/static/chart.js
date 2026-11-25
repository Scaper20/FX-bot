/* Interactive candlestick charts (TradingView Lightweight Charts 4.2.0, Apache-2.0).
   Any element <div class="ichart" data-src="/api/chart/..."> becomes a chart with timeframe buttons,
   drag/zoom, fit and full screen. If anything fails, the element is removed and the static SVG
   chart next to it stays visible. */
(function () {
  "use strict";
  var LIB = "https://unpkg.com/lightweight-charts@4.2.0/dist/lightweight-charts.standalone.production.js";
  var ORDER = ["M5", "M15", "H1", "H4", "D1"];
  var libPromise = null;

  function loadLib() {
    if (window.LightweightCharts) return Promise.resolve();
    if (!libPromise) {
      libPromise = new Promise(function (resolve, reject) {
        var s = document.createElement("script");
        s.src = LIB; s.async = true; s.crossOrigin = "anonymous";
        s.onload = resolve; s.onerror = reject;
        document.head.appendChild(s);
      });
    }
    return libPromise;
  }

  function toBars(rows, off) {
    return (rows || []).map(function (c) {
      return { time: c[0] + off, open: c[1], high: c[2], low: c[3], close: c[4] };
    });
  }

  function snap(t, bars) {          // time of the bar that contains t (last bar starting at or before t)
    var hit = null;
    for (var i = 0; i < bars.length; i++) {
      if (bars[i].time <= t) hit = bars[i].time; else break;
    }
    return hit;
  }

  function button(label, cls) {
    var b = document.createElement("button");
    b.type = "button"; b.className = "btn small ghost " + (cls || ""); b.textContent = label;
    return b;
  }

  function build(el, data) {
    var LWC = window.LightweightCharts;
    var off = data.tz_offset || 0;
    var tfs = ORDER.filter(function (tf) { return data.tfs[tf] && data.tfs[tf].length; });
    if (!tfs.length) throw new Error("no candles");

    el.innerHTML = "";
    var bar = document.createElement("div"); bar.className = "ichart-bar";
    var tfWrap = document.createElement("div"); tfWrap.className = "ichart-tfs"; tfWrap.setAttribute("role", "group");
    tfWrap.setAttribute("aria-label", "Timeframe");
    var buttons = {};
    tfs.forEach(function (tf) {
      var b = button(tf, "tf"); b.setAttribute("aria-pressed", "false");
      b.addEventListener("click", function () { show(tf); });
      buttons[tf] = b; tfWrap.appendChild(b);
    });
    var tools = document.createElement("div"); tools.className = "ichart-tools";
    var fitB = button("Fit"), fullB = button("Full screen");
    tools.appendChild(fitB); tools.appendChild(fullB);
    bar.appendChild(tfWrap); bar.appendChild(tools);
    var box = document.createElement("div"); box.className = "ichart-box";
    box.setAttribute("role", "img");
    box.setAttribute("aria-label", data.pair + " interactive chart; a text description is below the chart");
    var hint = document.createElement("p"); hint.className = "muted small ichart-hint";
    hint.textContent = "Drag to move, scroll or pinch to zoom, drag the price scale to stretch candles. Times " +
      (off ? "in your time zone" : "in GMT+0, the same as Exness MT5") + ".";
    el.appendChild(bar); el.appendChild(box); el.appendChild(hint);

    var p = data.precision || 5;
    var fmt = { type: "price", precision: p, minMove: Math.pow(10, -p) };
    var chart = LWC.createChart(box, {
      autoSize: true,
      layout: { background: { type: "solid", color: "#FFFFFF" }, textColor: "#0F1B2D",
                fontFamily: "'JetBrains Mono', ui-monospace, monospace", fontSize: 11 },
      grid: { vertLines: { color: "#F0F2F6" }, horzLines: { color: "#F0F2F6" } },
      rightPriceScale: { borderColor: "#E3E7ED", scaleMargins: { top: 0.08, bottom: 0.08 } },
      timeScale: { borderColor: "#E3E7ED", timeVisible: true, secondsVisible: false, rightOffset: 6 },
      crosshair: { mode: LWC.CrosshairMode.Normal },
      handleScale: { axisPressedMouseMove: { time: true, price: true }, mouseWheel: true, pinch: true },
      handleScroll: { mouseWheel: true, pressedMouseMove: true, horzTouchDrag: true, vertTouchDrag: false }
    });
    var main = chart.addCandlestickSeries({ upColor: "#0B7A5A", downColor: "#C8473B", borderVisible: false,
      wickUpColor: "#0B7A5A", wickDownColor: "#C8473B", priceFormat: fmt,
      priceLineVisible: false });            // the dotted last-price line looked like a CRT level
    var later = chart.addCandlestickSeries({ upColor: "rgba(11,122,90,0.35)", downColor: "rgba(200,71,59,0.35)",
      borderVisible: false, wickUpColor: "rgba(11,122,90,0.35)", wickDownColor: "rgba(200,71,59,0.35)",
      priceFormat: fmt, lastValueVisible: false, priceLineVisible: false });
    var narrow = box.clientWidth < 600;           // phones: names in a key below, not on the chart
    var long = data.direction === "long";
    // Each level is a line that starts when the level exists (range lines at the range candle,
    // entry/stop/target at the trigger), not a line across the whole history.
    var levelSeries = (data.levels || []).map(function (lv) {
      var ser = chart.addLineSeries({ color: lv.color, lineWidth: 1, priceFormat: fmt,
        lineStyle: lv.dashed ? LWC.LineStyle.Dashed : LWC.LineStyle.Solid, priceLineVisible: false,
        lastValueVisible: true, crosshairMarkerVisible: false, title: narrow ? "" : lv.title });
      return { lv: lv, ser: ser };
    });
    var key = document.createElement("p"); key.className = "ichart-key small";
    (data.levels || []).forEach(function (lv) {
      var k = document.createElement("span");
      k.innerHTML = '<i style="background:' + lv.color + '"></i>';
      k.appendChild(document.createTextNode(lv.title));
      key.appendChild(k);
    });
    var mk = document.createElement("span");
    mk.textContent = (long ? "▲" : "▼") + " " + (data.marker_key || "R range candle · S sweep (where the extreme was made) · T trigger candle");
    key.appendChild(mk);
    el.insertBefore(key, hint);

    var current = null;
    function show(tf) {
      current = tf;
      var bars = toBars(data.tfs[tf], off);
      var lastT = bars.length ? bars[bars.length - 1].time : 0;
      var after = toBars((data.after || {})[tf], off).filter(function (b) { return b.time > lastT; });
      main.setData(bars);
      later.setData(after);
      var times = bars.concat(after).map(function (b) { return b.time; });
      levelSeries.forEach(function (x) {
        var from = x.lv.from !== undefined ? snap(x.lv.from + off, bars) : null;
        if (from === null) from = times.length ? times[0] : 0;
        x.ser.setData(times.filter(function (t) { return t >= from; })
          .map(function (t) { return { time: t, value: x.lv.price }; }));
      });
      var ms = [], seen = {};
      (data.markers || []).forEach(function (m) {
        var t = snap(m.time + off, bars);
        if (m.kind === "sweep") {          // the candle inside the sweep candle that made the extreme
          var best = null;
          bars.forEach(function (b) {
            if (b.time >= m.time + off - 1 && b.time < m.end + off &&
                (best === null || (long ? b.low < best.low : b.high > best.high))) best = b;
          });
          if (best) t = best.time;
        }
        if (t === null) return;
        if (seen[t]) { seen[t].text += m.text; return; }
        seen[t] = { time: t, position: long ? "belowBar" : "aboveBar", color: m.color,
                    shape: long ? "arrowUp" : "arrowDown", text: m.text };
        ms.push(seen[t]);
      });
      ms.sort(function (a, b) { return a.time - b.time; });
      main.setMarkers(ms);
      var focus = snap(data.focus + off, bars);
      var idx = bars.length - 1;
      for (var i = 0; i < bars.length; i++) { if (bars[i].time === focus) { idx = i; break; } }
      chart.timeScale().setVisibleLogicalRange({ from: idx - 90, to: idx + Math.min(after.length, 60) + 8 });
      Object.keys(buttons).forEach(function (k) {
        buttons[k].setAttribute("aria-pressed", k === tf ? "true" : "false");
        buttons[k].classList.toggle("active", k === tf);
      });
    }
    fitB.addEventListener("click", function () { chart.timeScale().fitContent(); });

    function isFull() { return document.fullscreenElement === el || el.classList.contains("ichart-full"); }
    function setFullLabel() { fullB.textContent = isFull() ? "Exit full screen" : "Full screen"; }
    fullB.addEventListener("click", function () {
      if (isFull()) {
        if (document.fullscreenElement) document.exitFullscreen(); else el.classList.remove("ichart-full");
      } else if (el.requestFullscreen) {
        el.requestFullscreen().catch(function () { el.classList.add("ichart-full"); setFullLabel(); });
      } else {
        el.classList.add("ichart-full");            // iPhone Safari: full-window mode instead
      }
      setFullLabel();
    });
    document.addEventListener("fullscreenchange", setFullLabel);
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && el.classList.contains("ichart-full")) { el.classList.remove("ichart-full"); setFullLabel(); }
    });

    show(tfs.indexOf(data.default_tf) >= 0 ? data.default_tf : tfs[tfs.length > 2 ? 2 : 0]);
    var scope = el.closest(".card") || document;
    scope.querySelectorAll(".static-charts").forEach(function (s) { s.hidden = true; });
  }

  function init(el) {
    fetch(el.dataset.src, { credentials: "same-origin", headers: { "Accept": "application/json" } })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (data) { return loadLib().then(function () { build(el, data); }); })
      .catch(function () { el.remove(); });
  }

  function start() { document.querySelectorAll(".ichart[data-src]").forEach(init); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
})();

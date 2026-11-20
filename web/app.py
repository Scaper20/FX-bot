"""CRT setup scanner website (spec v1.3). Personal use: one password, no accounts."""
from __future__ import annotations

import csv
import functools
import hashlib
import hmac
import io
import os
import secrets
import time
from pathlib import Path

import pandas as pd
from flask import (Flask, Response, abort, flash, g, jsonify, redirect, render_template, request,
                   session, url_for)
from jinja2 import Undefined

from engine import config as K
from engine.feeds.twelvedata import CALLS_PER_SCAN, FeedError, TwelveDataFeed, fetch
from engine.live import ENGINE_VERSION, TRIGGER_LABEL, load_stats
from engine.sessions import LONDON, NEW_YORK

from . import charts, service
from .store import StoreError, from_env, merged_settings

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"


def _secret_key() -> str:
    if os.environ.get("SECRET_KEY"):
        return os.environ["SECRET_KEY"]
    base = os.environ.get("SUPABASE_SECRET_KEY", "") + "|" + os.environ.get("SITE_PASSWORD", "")
    if base != "|":
        return hashlib.sha256(("crt-session|" + base).encode()).hexdigest()
    return secrets.token_hex(32)


def create_app(store=None, feed=None, now_fn=None) -> Flask:
    app = Flask(__name__, template_folder=str(Path(__file__).parent / "templates"),
                static_folder=str(PUBLIC / "static"), static_url_path="/static")
    dev = os.environ.get("LOCAL_DEV") == "1"
    app.config.update(SECRET_KEY=_secret_key(), SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                      SESSION_COOKIE_SECURE=not dev, PERMANENT_SESSION_LIFETIME=60 * 60 * 24 * 30, DEV=dev)
    app.extensions["store"] = store or from_env()
    app.extensions["feed_factory"] = (lambda: feed) if feed is not None else _default_feed
    app.extensions["now_fn"] = now_fn or (lambda: pd.Timestamp.now(tz="UTC").floor("s"))

    # ------------------------------------------------------------ helpers
    def store():
        return app.extensions["store"]

    def now():
        return app.extensions["now_fn"]()

    @app.before_request
    def load_settings():
        g.settings = None

    def settings():
        if g.get("settings") is None:
            try:
                g.settings = store().get_settings()
            except StoreError:
                g.settings = merged_settings({})
        return g.settings

    def csrf_token():
        if "csrf" not in session:
            session["csrf"] = secrets.token_hex(16)
        return session["csrf"]

    def check_csrf():
        tok = request.form.get("csrf", "")
        if not tok or not hmac.compare_digest(tok, session.get("csrf", "")):
            abort(400, "Form expired. Go back, reload the page and try again.")

    def login_required(fn):
        @functools.wraps(fn)
        def wrapper(*a, **kw):
            if not session.get("ok"):
                return redirect(url_for("login", next=request.path))
            return fn(*a, **kw)
        return wrapper

    # ------------------------------------------------------------ template helpers
    @app.context_processor
    def inject():
        st = settings()
        tz = st.get("tz", "Africa/Lagos")

        def missing(x):
            return x is None or isinstance(x, Undefined)

        def loc(t, fmt="%a %d %b %H:%M"):
            if missing(t) or not t:
                return "—"
            return pd.Timestamp(t).tz_convert(tz).strftime(fmt)

        def price(pair, x):
            if missing(x):
                return "—"
            return f"{x:.5f}" if pair == "GBPUSD" else f"{x:,.2f}"

        def pct(x, digits=0):
            return "—" if missing(x) else f"{x * 100:.{digits}f}%"

        def rfmt(x):
            return "—" if missing(x) else f"{x:+.2f}R"

        return dict(loc=loc, price=price, pct=pct, rfmt=rfmt, csrf_token=csrf_token, settings=st,
                    labels=service.LABELS, reasons=service.REASONS, trigger_label=TRIGGER_LABEL,
                    engine_version=ENGINE_VERSION, clock=session_clock(now(), tz), nav=request.endpoint,
                    lot_size=lambda pair, e, s: service.lot_size(st, pair, e, s), dev=app.config["DEV"])

    # ------------------------------------------------------------ auth
    @app.route("/login", methods=["GET", "POST"])
    def login():
        pw = os.environ.get("SITE_PASSWORD") or ("local" if app.config["DEV"] else "")
        if request.method == "POST":
            check_csrf()
            if pw and hmac.compare_digest(request.form.get("password", ""), pw):
                session.clear()
                session.permanent = True
                session["ok"] = True
                nxt = request.args.get("next", "/")
                return redirect(nxt if nxt.startswith("/") and not nxt.startswith("//") else "/")
            time.sleep(1.0)
            flash("Wrong password." if pw else "SITE_PASSWORD is not set on the server yet.", "error")
        return render_template("login.html", configured=bool(pw))

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    # ------------------------------------------------------------ main pages
    @app.route("/")
    @login_required
    def home():
        try:
            data = service.dashboard(store(), now())
            todo = service.unreviewed(store())
            credits = store().credits_today()
            scans = store().recent_scans(1)
        except StoreError as e:
            return render_template("error.html", message=str(e)), 503
        return render_template("home.html", d=data, todo=todo, credits=credits, calls=CALLS_PER_SCAN,
                               last_any=scans[0] if scans else None)

    @app.route("/scan", methods=["POST"])
    @login_required
    def scan_now():
        check_csrf()
        last = store().last_scan()
        fresh = last and pd.Timestamp(last["started_at"]) > pd.Timestamp.now(tz="UTC") - pd.Timedelta("3min")
        if fresh and not request.form.get("force"):
            flash("Showing the scan from under 3 minutes ago (saves data credits).", "info")
            return redirect(url_for("home"))
        try:
            row = service.run_scan(store(), app.extensions["feed_factory"](), now(), trigger="manual",
                                   counts_credits=not _is_replay())
            res = row["result"]
            act = sum(1 for r in res["ready"] if r["actionable"])
            play = sum(1 for r in res["ready"] if not r["actionable"] and r["in_play"])
            flash(f"Scan done: {act} setup(s) you can still act on, {play} already in play, {row['armed']} armed. "
                  f"{row['ready']} CRT(s) with a trigger in total; {len(res['new'])} new, all logged in the Journal."
                  + (f" Problems: {'; '.join(res['errors'])}" if res["errors"] else ""), "ok")
        except (service.ScanError, StoreError, FeedError) as e:
            flash(f"Scan failed: {e}", "error")
        return redirect(url_for("home"))

    @app.route("/setup/<sid>")
    @login_required
    def setup(sid):
        row = store().get_setup(sid)
        if not row:
            abort(404)
        if row["source"] == "practice":
            return redirect(url_for("practice_result", pid=sid))
        card = row["card"]
        ops = service.all_options(row)
        oid = request.args.get("option") or card.get("best")
        op = next((o for o in ops if o["id"] == oid), ops[0] if ops else None)
        ch = charts.card_charts(card, op)
        return render_template("setup.html", row=row, card=card, ops=ops, op=op, charts=ch,
                               text=charts.text_equivalent(card, op, settings()["tz"]),
                               reviews=store().list_reviews(sid), status=row.get("status") or {},
                               show_all=request.args.get("all") == "1")

    @app.route("/setup/<sid>/review", methods=["POST"])
    @login_required
    def review(sid):
        check_csrf()
        row = store().get_setup(sid)
        if not row:
            abort(404)
        rv = _review_from_form(request.form)
        rv["setup_id"] = sid
        store().add_review(rv)
        flash("Review saved. Thank you, this is what teaches the system.", "ok")
        return redirect(url_for("setup", sid=sid, option=rv.get("option_id") or None))

    @app.route("/review/<int:rid>/result", methods=["POST"])
    @login_required
    def review_result(rid):
        check_csrf()
        f = request.form
        fields = {k: _num(f.get(k)) for k in ("actual_entry", "actual_exit", "actual_r")}
        fields["actual_closed_at"] = pd.Timestamp.now(tz="UTC").isoformat() if f.get("closed") else None
        store().update_review(rid, **fields)
        flash("Result saved.", "ok")
        return redirect(request.form.get("back") or url_for("journal"))

    @app.route("/journal")
    @login_required
    def journal():
        src = request.args.get("source", "live")
        rows = store().list_setups(source=src, limit=1000)
        pair = request.args.get("pair")
        if pair:
            rows = [r for r in rows if r["pair"] == pair]
        latest = {}
        for r in store().list_reviews():
            latest[r["setup_id"]] = r
        dec = request.args.get("decision")
        items = []
        for r in rows:
            rv = latest.get(r["id"])
            if dec == "none" and rv:
                continue
            if dec in ("take", "skip", "unsure") and (not rv or rv["decision"] != dec):
                continue
            op, st = service._option_outcome(r, rv.get("option_id") if rv and rv["decision"] == "take" else None)
            items.append({"row": r, "review": rv, "op": op, "st": st})
        return render_template("journal.html", items=items, source=src, pair=pair, decision=dec)

    @app.route("/journal.csv")
    @login_required
    def journal_csv():
        rows = store().list_setups(limit=5000)
        latest = {}
        for r in store().list_reviews():
            latest[r["setup_id"]] = r
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["setup_id", "source", "pair", "direction", "range_tf", "range_open", "first_seen",
                    "recommended", "decision", "option_id", "reasons", "notes", "confidence", "entry", "stop",
                    "target", "rr", "chance", "status", "outcome", "R", "actual_entry", "actual_exit", "actual_R"])
        for r in rows:
            rv = latest.get(r["id"]) or {}
            op, st = service._option_outcome(r, rv.get("option_id") if rv.get("decision") == "take" else None)
            op, st = op or {}, st or {}
            w.writerow([r["id"], r["source"], r["pair"], r["direction"], r["range_tf"], r["range_open"],
                        r.get("first_seen"), r.get("recommended"), rv.get("decision", ""), op.get("id", ""),
                        ";".join(rv.get("reasons") or []), rv.get("notes", ""), rv.get("confidence", ""),
                        op.get("entry"), op.get("stop"), op.get("target"), op.get("rr"), op.get("chance"),
                        st.get("status"), st.get("state"), st.get("R"), rv.get("actual_entry"),
                        rv.get("actual_exit"), rv.get("actual_r")])
        return Response(buf.getvalue(), mimetype="text/csv",
                        headers={"Content-Disposition": "attachment; filename=crt-journal.csv"})

    @app.route("/performance")
    @login_required
    def performance():
        return render_template("performance.html", live=service.performance(store(), "live"),
                               practice=service.performance(store(), "practice"))

    @app.route("/practice")
    @login_required
    def practice():
        item = service.next_practice(store())
        prog = service.practice_progress(store())
        if not item:
            return render_template("practice_done.html", prog=prog)
        card = item["card"]
        op = service.option_by_id(card, card.get("best"))
        ch = charts.card_charts(card, op)
        return render_template("practice.html", item=item, card=card, op=op, charts=ch, prog=prog,
                               text=charts.text_equivalent(card, op, settings()["tz"]))

    @app.route("/practice/<pid>", methods=["POST"])
    @login_required
    def practice_review(pid):
        check_csrf()
        item = service.practice_item(pid)
        if not item:
            abort(404)
        if not store().get_setup(pid):
            service.save_practice_review(store(), item, _review_from_form(request.form))
        return redirect(url_for("practice_result", pid=pid))

    @app.route("/practice/<pid>/result")
    @login_required
    def practice_result(pid):
        item = service.practice_item(pid)
        row = store().get_setup(pid)
        if not item or not row:
            abort(404)
        card = item["card"]
        rv = store().list_reviews(pid)
        chosen = rv[-1].get("option_id") if rv else None
        op = service.option_by_id(card, chosen) or service.option_by_id(card, card.get("best"))
        ch = charts.card_charts(card, op, after=item.get("after"), decision=op["decision_time"] if op else None)
        return render_template("practice_result.html", item=item, card=card, op=op, charts=ch, reviews=rv,
                               status=item["outcome"], prog=service.practice_progress(store()))

    @app.route("/strategy")
    @login_required
    def strategy():
        meta = load_stats().get("_meta", {})
        return render_template("strategy.html", meta=meta)

    @app.route("/backtest")
    @login_required
    def backtest():
        return render_template("backtest.html")

    @app.route("/help")
    @login_required
    def help_page():
        return render_template("help.html")

    @app.route("/settings", methods=["GET", "POST"])
    @login_required
    def settings_page():
        st = settings()
        if request.method == "POST":
            check_csrf()
            f = request.form
            new = {
                "spreads": {"GBPUSD": _num(f.get("spread_GBPUSD_pips"), 1.0) * 0.0001,
                            "XAUUSD": _num(f.get("spread_XAUUSD"), 0.35)},
                "balance": _num(f.get("balance"), st["balance"]),
                "risk_pct": _num(f.get("risk_pct"), st["risk_pct"]),
                "contract": {"GBPUSD": _num(f.get("contract_GBPUSD"), 100000),
                             "XAUUSD": _num(f.get("contract_XAUUSD"), 100)},
                "tz": f.get("tz") or st["tz"],
                "daily_credit_limit": int(_num(f.get("daily_credit_limit"), 780)),
            }
            if not (0 < new["spreads"]["GBPUSD"] < 0.01 and 0 < new["spreads"]["XAUUSD"] < 20
                    and 0 < new["risk_pct"] <= 10 and new["balance"] > 0):
                flash("Some values look wrong; nothing saved.", "error")
            else:
                store().save_settings(new)
                flash("Settings saved. New spreads apply from the next scan.", "ok")
            return redirect(url_for("settings_page"))
        return render_template("settings.html", st=st, credits=store().credits_today(),
                               scans=store().recent_scans(15), feed_result=session.pop("feed_result", None))

    @app.route("/settings/feed-check", methods=["POST"])
    @login_required
    def feed_check():
        check_csrf()
        out = []
        for pair in K.PAIRS:
            try:
                df = fetch(pair, "H1", outputsize=3)
                out.append(f"{pair}: OK, last H1 candle {df.index[-1]:%d %b %H:%M} UTC close {df['close'].iloc[-1]}")
            except FeedError as e:
                out.append(f"{pair}: {e}")
        store().add_credits(len(K.PAIRS))
        session["feed_result"] = out
        return redirect(url_for("settings_page"))

    # ------------------------------------------------------------ machine endpoints
    @app.route("/api/cron/scan", methods=["GET", "POST"])
    def cron_scan():
        auth = request.headers.get("Authorization", "")
        token = auth[7:] if auth.startswith("Bearer ") else ""
        valid = [t for t in (os.environ.get("CRON_SECRET"), _db_token()) if t]
        if not token or not any(hmac.compare_digest(token, t) for t in valid):
            return jsonify(ok=False, error="unauthorized"), 401
        t = now()
        if not _in_scan_hours(t) and request.args.get("force") != "1":
            return jsonify(ok=True, skipped="outside London/New York hours or weekend")
        try:
            row = service.run_scan(store(), app.extensions["feed_factory"](), t, trigger="schedule",
                                   counts_credits=not _is_replay())
            return jsonify(ok=True, ready=row["ready"], armed=row["armed"], message=row["message"])
        except (service.ScanError, StoreError, FeedError) as e:
            return jsonify(ok=False, error=str(e)), 200

    def _db_token():
        try:
            return store().get_secret("cron")
        except StoreError:
            return None

    @app.route("/api/health")
    def health():
        try:
            last = store().last_scan()
            db = True
        except StoreError:
            last, db = None, False
        return jsonify(ok=db, engine=ENGINE_VERSION, database=db,
                       feed_key_set=bool(os.environ.get("TWELVEDATA_API_KEY")),
                       password_set=bool(os.environ.get("SITE_PASSWORD")),
                       last_scan=last["started_at"] if last else None)

    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", message="Page not found."), 404

    @app.errorhandler(400)
    def bad_request(e):
        return render_template("error.html", message=getattr(e, "description", "Bad request")), 400

    return app


# ---------------------------------------------------------------- module helpers


def _num(x, default=None):
    try:
        return float(x) if x not in (None, "") else default
    except ValueError:
        return default


def _review_from_form(f) -> dict:
    decision = f.get("decision")
    if decision not in ("take", "skip", "unsure"):
        abort(400, "Choose take, skip or unsure.")
    reasons = [r for r in f.getlist("reasons") if r in service.REASON_LABEL]
    conf = f.get("confidence")
    return {"decision": decision, "option_id": f.get("option_id") or None, "reasons": reasons,
            "notes": (f.get("notes") or "")[:2000],
            "confidence": int(conf) if conf and conf.isdigit() and 1 <= int(conf) <= 5 else None}


def _is_replay() -> bool:
    return os.environ.get("FEED") == "replay"


_REPLAY = {}


def _default_feed():
    if _is_replay():
        if "feed" not in _REPLAY:
            from engine.candles import clean, load_m1_csv
            from engine.feeds.replay import ReplayFeed
            _REPLAY["feed"] = ReplayFeed({p: clean(load_m1_csv(ROOT / K.PAIRS[p]["file"]))[0] for p in K.PAIRS})
        return _REPLAY["feed"]
    return TwelveDataFeed()


def _in_scan_hours(t: pd.Timestamp) -> bool:
    """Scheduled scans: weekdays from 06:00 London to 18:00 New York (covers both sessions)."""
    ld, ny = t.tz_convert(LONDON), t.tz_convert(NEW_YORK)
    return ld.weekday() < 5 and ld.hour >= 6 and ny.hour < 18 and ld.date() == ny.date()


def session_clock(t: pd.Timestamp, tz: str) -> dict:
    ld, ny = t.tz_convert(LONDON), t.tz_convert(NEW_YORK)
    weekday_ok = ny.weekday() < 5 and not (ny.weekday() == 4 and ny.hour >= 17)
    london = weekday_ok and 7 <= ld.hour < 16
    newyork = weekday_ok and 8 <= ny.hour < 17
    return {"local": t.tz_convert(tz).strftime("%a %H:%M"), "london": london, "newyork": newyork,
            "overlap": london and newyork, "weekend": not weekday_ok and ny.weekday() >= 4,
            "utc": t.strftime("%H:%M")}

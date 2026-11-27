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
from engine.strategies import STRATEGIES, strategy_of

from . import chartdata, charts, community, insights, mailer, plan, reminders, service, zones
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
        tz = "UTC" if g.get("public") else st.get("tz", "Africa/Lagos")

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
                    labels=service.LABELS, reasons=service.REASONS, strategies=STRATEGIES, strategy_of=strategy_of, trigger_label=TRIGGER_LABEL,
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
            strat = request.args.get("strategy") if request.args.get("strategy") in STRATEGIES else None
            if strat:
                for key in ("cards", "other", "in_play"):
                    data[key] = [x for x in data[key] if x["strategy"] == strat]
            todo = service.unreviewed(store())
            credits = store().credits_today()
            scans = store().recent_scans(1)
        except StoreError as e:
            return render_template("error.html", message=str(e)), 503
        return render_template("home.html", d=data, todo=todo, credits=credits, calls=CALLS_PER_SCAN,
                               last_any=scans[0] if scans else None, strat=strat)

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
                                   base_url=request.url_root.rstrip("/"),
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
                               text=charts.text_equivalent(card, op),
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
        strat = request.args.get("strategy") if request.args.get("strategy") in STRATEGIES else None
        if strat:
            rows = [r for r in rows if strategy_of(r["card"]) == strat]
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
            items.append({"row": r, "review": rv, "op": op, "st": st, "strategy": strategy_of(r["card"])})
        return render_template("journal.html", items=items, source=src, pair=pair, decision=dec, strat=strat)

    @app.route("/journal.csv")
    @login_required
    def journal_csv():
        rows = store().list_setups(limit=5000)
        latest = {}
        for r in store().list_reviews():
            latest[r["setup_id"]] = r
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["setup_id", "strategy", "source", "pair", "direction", "range_tf", "range_open", "first_seen",
                    "recommended", "decision", "option_id", "reasons", "notes", "confidence", "entry", "stop",
                    "target", "rr", "chance", "status", "outcome", "R", "actual_entry", "actual_exit", "actual_R"])
        for r in rows:
            rv = latest.get(r["id"]) or {}
            op, st = service._option_outcome(r, rv.get("option_id") if rv.get("decision") == "take" else None)
            op, st = op or {}, st or {}
            w.writerow([r["id"], strategy_of(r["card"]), r["source"], r["pair"], r["direction"], r["range_tf"], r["range_open"],
                        r.get("first_seen"), r.get("recommended"), rv.get("decision", ""), op.get("id", ""),
                        ";".join(rv.get("reasons") or []), rv.get("notes", ""), rv.get("confidence", ""),
                        op.get("entry"), op.get("stop"), op.get("target"), op.get("rr"), op.get("chance"),
                        st.get("status"), st.get("state"), st.get("R"), rv.get("actual_entry"),
                        rv.get("actual_exit"), rv.get("actual_r")])
        return Response(buf.getvalue(), mimetype="text/csv",
                        headers={"Content-Disposition": "attachment; filename=setup-journal.csv"})

    @app.route("/performance")
    @login_required
    def performance():
        st = store()
        return render_template("performance.html",
                               live={k: service.performance(st, "live", k) for k in STRATEGIES},
                               live_all=service.performance(st, "live"),
                               practice=service.performance(st, "practice"),
                               community=community.all_stats(store()),
                               share_url=url_for("p_start", _external=True))

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
                               text=charts.text_equivalent(card, op),
                               chart_src=url_for("chart_practice", pid=item["id"]))

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
                               status=item["outcome"], prog=service.practice_progress(store()),
                               chart_src=url_for("chart_practice", pid=pid, option=op["id"] if op else None))

    # ------------------------------------------------------------ zone trainer
    @app.route("/train")
    @login_required
    def train():
        z = zones.next_item(store())
        if not z:
            return redirect(url_for("train_stats"))
        return redirect(url_for("train_item", zid=z["id"]))

    @app.route("/train/<zid>", methods=["GET", "POST"])
    @login_required
    def train_item(zid):
        z = zones.item(zid)
        if not z:
            abort(404)
        if request.method == "POST":
            check_csrf()
            label = request.form.get("label")
            if label not in zones.LABELS:
                abort(400)
            tags = [t for t in request.form.getlist("tags") if t in zones.TAG_LABEL]
            store().add_zone_label({"item_id": zid, "label": label, "tags": tags,
                                    "notes": (request.form.get("notes") or "")[:1000]})
            return redirect(url_for("train_result", zid=zid))
        if zid in zones.labels_by_item(store()) and not request.args.get("again"):
            return redirect(url_for("train_result", zid=zid))
        return render_template("train.html", z=z, svg=zones.chart(z, reveal=False), prog=zones.progress(store()),
                               kinds=zones.KINDS, labels=zones.LABELS, tags=zones.TAGS)

    @app.route("/train/<zid>/result")
    @login_required
    def train_result(zid):
        z = zones.item(zid)
        lab = zones.labels_by_item(store()).get(zid)
        if not z or not lab:
            abort(404)
        return render_template("train_result.html", z=z, lab=lab, svg=zones.chart(z, reveal=True),
                               prog=zones.progress(store()), kinds=zones.KINDS, labels=zones.LABELS,
                               tag_label=zones.TAG_LABEL, nxt=zones.next_item(store()))

    @app.route("/train/stats")
    @login_required
    def train_stats():
        return render_template("train_stats.html", st=zones.stats(store()), kinds=zones.KINDS, labels=zones.LABELS)

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
                "owner_email": community.norm_email(f.get("owner_email")) if community.valid_email(f.get("owner_email") or "") else "",
                "alerts": {"new": bool(f.get("alert_new")), "outcomes": bool(f.get("alert_outcomes")),
                           "digest": bool(f.get("alert_digest")), "filtered": bool(f.get("alert_filtered")),
                           "smc": bool(f.get("alert_smc")), "irl_erl": bool(f.get("alert_irl_erl")),
                           "toni": bool(f.get("alert_toni")),
                           "lingard": bool(f.get("alert_lingard")),
                           "max_per_day": int(_num(f.get("alert_max"), 30))},
                "spreads_confirmed": True,
                "reminders": {"community": bool(f.get("rem_community")), "owner": bool(f.get("rem_owner")),
                              "every_days": min(14, max(1, int(_num(f.get("rem_every"), 3)))),
                              "owner_every_days": min(14, max(1, int(_num(f.get("rem_owner_every"), 2))))},
                "last_owner_nudge": st.get("last_owner_nudge", ""),
                "last_digest": st.get("last_digest", ""), "alert_count": st.get("alert_count", {}),
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

    # ------------------------------------------------------------ public practice (community)
    def public_user_required(fn):
        @functools.wraps(fn)
        def wrapper(*a, **kw):
            g.public = True
            if not session.get("pu"):
                return redirect(url_for("p_start"))
            return fn(*a, **kw)
        return wrapper

    @app.route("/p", methods=["GET", "POST"])
    def p_start():
        g.public = True
        if community.email_signin_enabled():
            return p_start_email()
        if request.method == "POST":
            check_csrf()
            name = (request.form.get("username") or "").strip()
            if not community.valid_name(name):
                flash("Use 3 to 20 letters, numbers, dots, dashes or underscores.", "error")
                return render_template("p_start.html", name=name)
            result, tok = community.claim(store(), name, session.get("pt"), bool(request.form.get("its_me")))
            if result == "taken":
                return render_template("p_start.html", name=name, ask_confirm=True)
            session.permanent = True
            session["pu"], session["pu_name"] = community.key_of(name), name
            if tok:
                session["pt"] = tok
            return redirect(url_for("p_practice"))
        return render_template("p_start.html", name=session.get("pu_name", ""))

    def p_start_email():
        name, email = session.get("pu_name", ""), ""
        if request.method == "POST":
            check_csrf()
            name = (request.form.get("username") or "").strip()
            email = community.norm_email(request.form.get("email"))
            status, info = community.start_signin(store(), name, email, bool(request.form.get("notify")),
                                                  app.config["SECRET_KEY"], url_for("p_start", _external=True))
            msgs = {"bad_email": "That email address doesn't look right.",
                    "bad_name": "Use 3 to 20 letters, numbers, dots, dashes or underscores for the username.",
                    "name_taken": "That username belongs to another email. Pick a different one.",
                    "too_many": "Too many codes for this email in the last hour. Try again later.",
                    "busy": "Sign-ups are paused for today (daily email limit). Please try tomorrow.",
                    "mail_error": "We couldn't send the email right now. Please try again in a minute."}
            if status == "sent":
                session["p_email"] = email
                if info.get("existing"):
                    flash(f"Welcome back, {info['display']}. We sent a code to {email}.", "info")
                else:
                    flash(f"We sent a 6-digit code to {email}.", "info")
                return redirect(url_for("p_verify"))
            flash(msgs.get(status, "Something went wrong."), "error")
        return render_template("p_start_email.html", name=name, email=email)

    @app.route("/p/verify", methods=["GET", "POST"])
    def p_verify():
        g.public = True
        email = session.get("p_email")
        if not email:
            return redirect(url_for("p_start"))
        if request.method == "POST":
            check_csrf()
            status, key = community.verify_code(store(), email, request.form.get("code"), app.config["SECRET_KEY"])
            if status == "ok":
                user = store().community_user(key)
                session.permanent = True
                session["pu"], session["pu_name"] = key, user["display_name"]
                session.pop("p_email", None)
                return redirect(url_for("p_practice"))
            flash({"wrong": "That code isn't right. Check the email and try again.",
                   "expired": "That code has expired. Ask for a new one.",
                   "locked": "Too many wrong tries. Ask for a new code.",
                   "none": "No valid code for this email. Ask for a new one."}[status], "error")
        return render_template("p_verify.html", email=email)

    @app.route("/p/me/notify", methods=["POST"])
    def p_notify():
        g.public = True
        if not session.get("pu"):
            return redirect(url_for("p_start"))
        check_csrf()
        store().community_update_user(session["pu"], notify=bool(request.form.get("notify")))
        flash("Email preference saved.", "ok")
        return redirect(url_for("p_me"))

    @app.route("/p/me/delete", methods=["POST"])
    def p_delete():
        g.public = True
        if not session.get("pu"):
            return redirect(url_for("p_start"))
        check_csrf()
        if not request.form.get("confirm"):
            flash("Tick the box to confirm.", "error")
            return redirect(url_for("p_me"))
        store().community_delete_user(session["pu"])
        for k in ("pu", "pu_name", "pt"):
            session.pop(k, None)
        flash("Your account, email address and answers have been deleted.", "ok")
        return redirect(url_for("p_start"))

    @app.route("/p/unsubscribe/<token>", methods=["GET", "POST"])
    def p_unsubscribe(token):
        g.public = True
        user = store().community_user_by("unsub_token", token) if len(token) >= 16 else None
        if not user:
            return render_template("p_message.html", title="Link not valid",
                                   message="This unsubscribe link isn't valid any more."), 404
        if request.method == "POST":
            check_csrf()
            store().community_update_user(user["username_key"], notify=False)
            return render_template("p_message.html", title="Unsubscribed",
                                   message="You won't get update emails any more. Sign-in codes still work.")
        return render_template("p_unsubscribe.html", token=token)

    @app.route("/p/practice")
    @public_user_required
    def p_practice():
        key = session["pu"]
        item = community.next_item(store(), key)
        prog = community.progress(store(), key)
        if not item:
            return render_template("p_done.html", prog=prog)
        card = item["card"]
        op = service.option_by_id(card, card.get("best"))
        return render_template("p_practice.html", item=item, card=card, op=op, prog=prog,
                               charts=charts.card_charts(card, op), text=charts.text_equivalent(card, op),
                               chart_src=url_for("p_chart", pid=item["id"]))

    @app.route("/p/practice/<pid>", methods=["POST"])
    @public_user_required
    def p_review(pid):
        check_csrf()
        item = service.practice_item(pid)
        if not item:
            abort(404)
        res = community.save(store(), session["pu"], item, _review_from_form(request.form))
        if res == "limit":
            flash(f"That's {community.DAILY_LIMIT} reviews today: thank you! Come back tomorrow.", "info")
            return redirect(url_for("p_me"))
        return redirect(url_for("p_result", pid=pid))

    @app.route("/p/practice/<pid>/result")
    @public_user_required
    def p_result(pid):
        item = service.practice_item(pid)
        mine = [r for r in store().community_reviews(session["pu"]) if r["item_id"] == pid]
        if not item or not mine:                    # no peeking at outcomes before answering
            return redirect(url_for("p_practice"))
        card = item["card"]
        chosen = mine[-1].get("option_id") if mine[-1]["decision"] == "take" else None
        op = service.option_by_id(card, chosen) or service.option_by_id(card, card.get("best"))
        ch = charts.card_charts(card, op, after=item.get("after"), decision=op["decision_time"] if op else None)
        return render_template("p_result.html", item=item, card=card, op=op, charts=ch, reviews=mine,
                               status=item["outcome"], prog=community.progress(store(), session["pu"]),
                               chart_src=url_for("p_chart", pid=pid, option=op["id"] if op else None))

    @app.route("/p/me")
    @public_user_required
    def p_me():
        return render_template("p_me.html", st=community.user_stats(store(), session["pu"]),
                               prog=community.progress(store(), session["pu"]),
                               user=store().community_user(session["pu"]))

    @app.route("/plan")
    @login_required
    def plan_page():
        return render_template("plan.html", d=plan.build(store(), settings()))

    @app.route("/insights")
    @login_required
    def insights_page():
        return render_template("insights.html", d=insights.build(store()))

    # ------------------------------------------------------------ community admin (Ore)
    @app.route("/community", methods=["GET", "POST"])
    @login_required
    def community_admin():
        people = store().community_users_all()
        if request.method == "POST" and request.form.get("action") == "remind":
            check_csrf()
            res = reminders.run(store(), settings(), now().to_pydatetime(), request.url_root.rstrip("/"), force=True)
            flash(f"Practice reminder sent to {res['sent']} trader(s) ({res['failed']} failed); "
                  f"your own nudge: {res['owner']}." + (f" {res['errors'][0]}" if res["errors"] else ""),
                  "ok" if not res["failed"] else "error")
            return redirect(url_for("community_admin"))
        if request.method == "POST":
            check_csrf()
            subject = (request.form.get("subject") or "").strip()[:200]
            message = (request.form.get("message") or "").strip()[:20000]
            if not subject or not message:
                flash("Write a subject and a message.", "error")
            elif request.form.get("action") == "test":
                to = settings().get("owner_email")
                if not to:
                    flash("Add your own email in Settings first.", "error")
                else:
                    html, text = community.update_email(subject, message, "Ore", url_for("p_start", _external=True))
                    try:
                        mailer.send(to, "[Test] " + subject, html, text, tags=["update-test"])
                        flash(f"Test sent to {to}.", "ok")
                    except mailer.MailError as e:
                        flash(str(e), "error")
            else:
                res = community.send_update(store(), subject, message,
                                            url_for("p_unsubscribe", token="x", _external=True)[:-2])
                flash(f"Sent to {res['sent']} of {res['recipients']} trader(s); {res['failed']} failed. {res['note']}",
                      "ok" if not res["failed"] else "error")
            return render_template("community.html", people=people, recips=community.recipients(store()),
                                   log=store().email_log(), subject=subject, message=message,
                                   mail_ok=mailer.configured(), mail_live=mailer.live(),
                                   share_url=url_for("p_start", _external=True), rem=reminders.prefs(settings()))
        return render_template("community.html", people=people, recips=community.recipients(store()),
                               log=store().email_log(), subject="", message="", mail_ok=mailer.configured(),
                               mail_live=mailer.live(), share_url=url_for("p_start", _external=True),
                               rem=reminders.prefs(settings()))

    @app.route("/p/logout")
    def p_logout():
        for k in ("pu", "pu_name"):
            session.pop(k, None)
        return redirect(url_for("p_start"))

    # ------------------------------------------------------------ interactive chart data
    # Charts use GMT+0 (Exness server time) so candles line up with Ore's MT5.
    def _practice_payload(pid: str, answered: bool, tz_offset: int):
        item = service.practice_item(pid)
        if not item:
            abort(404)
        card = item["card"]
        op = service.option_by_id(card, request.args.get("option")) or service.option_by_id(card, card.get("best"))
        ch = chartdata.practice_chart(pid) or {}
        before = ch.get("before") or {}
        after = ch.get("after") if answered else None           # outcome candles only after answering
        return jsonify(chartdata.payload(card, op, before, after, tz_offset))

    @app.route("/api/chart/setup/<sid>")
    @login_required
    def chart_setup(sid):
        row = store().get_setup(sid)
        if not row:
            abort(404)
        card = row["card"]
        ops = service.all_options(row)
        op = next((o for o in ops if o["id"] == request.args.get("option")), None) or \
            service.option_by_id(card, card.get("best"))
        before = card.get("chart", {}).get("tfs") or {}
        newer = store().get_candles(card["pair"]) if before else {}
        merged = {tf: chartdata.merge(before.get(tf, []), newer.get(tf, [])) for tf in before}
        return jsonify(chartdata.payload(card, op, merged, None, 0))

    @app.route("/api/chart/practice/<pid>")
    @login_required
    def chart_practice(pid):
        return _practice_payload(pid, answered=store().get_setup(pid) is not None, tz_offset=0)

    @app.route("/p/api/chart/<pid>")
    @public_user_required
    def p_chart(pid):
        answered = any(r["item_id"] == pid for r in store().community_reviews(session["pu"]))
        return _practice_payload(pid, answered=answered, tz_offset=0)

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
                                   base_url=request.url_root.rstrip("/"),
                                   counts_credits=not _is_replay())
            return jsonify(ok=True, ready=row["ready"], armed=row["armed"], message=row["message"])
        except (service.ScanError, StoreError, FeedError) as e:
            return jsonify(ok=False, error=str(e)), 200

    @app.route("/api/cron/reminders", methods=["GET", "POST"])
    def cron_reminders():
        """Daily practice reminders (scheduled job). ?force=1 sends now, ignoring the interval."""
        auth = request.headers.get("Authorization", "")
        token = auth[7:] if auth.startswith("Bearer ") else ""
        valid = [t for t in (os.environ.get("CRON_SECRET"), _db_token()) if t]
        if not token or not any(hmac.compare_digest(token, t) for t in valid):
            return jsonify(ok=False, error="unauthorized"), 401
        try:
            res = reminders.run(store(), settings(), now().to_pydatetime(), request.url_root.rstrip("/"),
                                force=request.args.get("force") == "1")
            res.pop("errors", None)
            return jsonify(ok=True, **res)
        except StoreError as e:
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
        except Exception:
            last, db = None, False
        return jsonify(ok=db, engine=ENGINE_VERSION, database=db,
                       feed_key_set=bool(os.environ.get("TWELVEDATA_API_KEY")),
                       password_set=bool(os.environ.get("SITE_PASSWORD")),
                       email_configured=mailer.configured(), email_live=mailer.live(),
                       email_sender_domain=(mailer.sender().rsplit("@", 1)[-1].rstrip(">").strip() or None),
                       last_scan=last["started_at"] if last else None)

    @app.errorhandler(StoreError)
    def store_error(e):
        return render_template("error.html", message=str(e)), 503

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

import os
import logging
from pathlib import Path
from typing import List
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, abort

import config
import db
import rss_manager
import composer
import mailer

import recipients
import storage

logger = logging.getLogger("rss-web")
logging.basicConfig(level=logging.DEBUG if config.DEBUG else logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")

BASE_DIR = Path.cwd()
app = Flask("RSS Digest")
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret")

def load_recipients() -> List[str]:
    try:
        return recipients.get_recipients()
    except Exception as e:
        logger.exception("Failed to load recipients from DB, falling back to config.EMAIL_TO: %s", e)
        return getattr(config, "EMAIL_TO", []) or []

def save_recipients_list(email_list: List[str]) -> None:
    try:
        recipients.set_recipients(email_list)
    except Exception as e:
        logger.exception("Failed to save recipients to DB: %s", e)
        raise e

@app.route("/")
def public_latest():
    index = storage.load_digest_index()
    if not index:
        return render_template("public_empty.html", title="No digests yet")
    latest = index[0]
    html_path = (storage.DIGESTS_DIR / latest["filename"])
    if not html_path.exists():
        idx = [e for e in index if (storage.DIGESTS_DIR / e["filename"]).exists()]
        storage.save_digest_index(idx)
        return redirect(url_for("public_archive"))
    digest_html = html_path.read_text(encoding="utf-8")
    return render_template("public.html", digest_html=digest_html, subject=latest["subject"], generated_at=latest["timestamp"])

@app.route("/archive")
def public_archive():
    index = storage.load_digest_index()
    return render_template("archive.html", digests=index)

@app.route("/digest/<path:filename>")
def serve_digest(filename):
    safe = (storage.DIGESTS_DIR / filename).resolve()
    if storage.DIGESTS_DIR not in safe.parents and safe != storage.DIGESTS_DIR:
        abort(404)
    if not safe.exists():
        abort(404)
    return send_file(safe)

@app.route("/admin")
def admin_index():
    feeds = db.get_feeds()
    normalized = []
    for r in feeds:
        if isinstance(r, dict):
            normalized.append(r)
        else:
            try:
                normalized.append({
                    "id": r[0],
                    "url": r[1],
                    "category": r[2] if len(r) > 2 else None,
                    "enabled": r[3] if len(r) > 3 else True,
                    "added_at": r[4] if len(r) > 4 else None,
                })
            except Exception:
                normalized.append({"url": str(r)})
    recips = load_recipients()
    digests = storage.load_digest_index()
    return render_template("admin.html", feeds=normalized, recipients=recips, digests=digests)

@app.route("/admin/feeds/add", methods=["POST"])
def admin_add_feed():
    url = request.form.get("url", "").strip()
    if not url:
        flash("Feed URL required", "error")
        return redirect(url_for("admin_index"))
    try:
        db.add_feed(url)
        flash("Feed added", "success")
    except Exception as e:
        logger.exception("Failed to add feed: %s", e)
        flash(f"Failed to add feed: {e}", "error")
    return redirect(url_for("admin_index"))

@app.route("/admin/feeds/delete/<int:feed_id>", methods=["POST"])
def admin_delete_feed(feed_id):
    try:
        db.delete_feed(feed_id)
        flash("Feed deleted", "success")
    except Exception as e:
        logger.exception("delete_feed failed")
        flash(f"Failed to delete feed: {e}", "error")
    return redirect(url_for("admin_index"))

@app.route("/admin/recipients", methods=["POST"])
def admin_save_recipients():
    raw = request.form.get("recipients", "")
    lines = [l.strip() for l in __import__("re").split(r"[,\n]+", raw) if l.strip()]
    try:
        save_recipients_list(lines)
        flash("Recipients updated", "success")
    except Exception as e:
        flash(f"Failed saving recipients: {e}", "error")
    return redirect(url_for("admin_index"))

@app.route("/admin/run", methods=["POST"])
def admin_run_digest():
    logger.info("Admin initiated run: fetch/persist/compose/send")
    try:
        items = rss_manager.run_once(max_entries_per_feed=config.MAX_ENTRIES_PER_FEED, persist=True)
        logger.info("Fetched %d items", len(items))
        if not items:
            flash("No new items found. No digest created.", "info")
            return redirect(url_for("admin_index"))
        subject, html_body, text_body = composer.compose_digest(items, max_items=config.MAX_ITEMS)
        filename = storage.write_digest_html(subject, html_body, len(items))
        flash(f"Digest created and cached as {filename}", "success")
        recips = load_recipients() or getattr(config, "EMAIL_TO", [])
        if not recips:
            flash("No recipients configured; digest created but not sent.", "warning")
            return redirect(url_for("admin_index"))
        try:
            mailer.send_digest(recipients=recips, subject=subject, html_body=html_body, text_body=text_body,
                               send_individually=config.SEND_INDIVIDUALLY)
            flash(f"Digest sent to {len(recips)} recipients.", "success")
        except Exception as e:
            logger.exception("send_digest failed")
            flash(f"Digest created but sending failed: {e}", "error")
    except Exception as e:
        logger.exception("admin_run_digest failed")
        flash(f"Operation failed: {e}", "error")
    return redirect(url_for("admin_index"))


@app.route("/admin/digests/<path:filename>")
def admin_view_digest(filename):
    safe = (storage.DIGESTS_DIR / filename).resolve()
    if storage.DIGESTS_DIR not in safe.parents and safe != storage.DIGESTS_DIR:
        abort(404)
    if not safe.exists():
        abort(404)
    digest_html = safe.read_text(encoding="utf-8")
    return render_template("admin_view_digest.html", digest_html=digest_html, filename=filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=42329, debug=config.DEBUG)
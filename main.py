import logging
import sys
from typing import List, Dict, Any

import config
import db
import rss_manager
import composer
import mailer
import recipients
import storage

logger = logging.getLogger("rss_digest")
logging.basicConfig(level=logging.DEBUG if getattr(config, "DEBUG", False) else logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")

def _mark_articles_sent(articles: List[Dict[str, Any]]) -> None:
    if not articles:
        return
    conn = db.get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                for a in articles:
                    link = a.get("link")
                    feed_id = a.get("feed_id")
                    cur.execute(
                        "UPDATE articles SET sent = TRUE WHERE link = %s AND (feed_id IS NOT DISTINCT FROM %s)",
                        (link, feed_id),
                    )
    finally:
        conn.close()

def main() -> int:
    logger.info("Starting rss-digest runner")

    try:
        db.init_db()
    except Exception as exc:
        logger.exception("Failed to initialize DB: %s", exc)
        return 2

    try:
        new_items = rss_manager.run_once(max_entries_per_feed=getattr(config, "MAX_ENTRIES_PER_FEED", None))
    except Exception as exc:
        logger.exception("rss_manager run failed: %s", exc)
        return 3

    if not new_items:
        logger.info("No new articles found. Nothing to send.")
        return 0

    logger.info("Found %d new articles; composing digest", len(new_items))

    max_items = getattr(config, "MAX_ITEMS", None)
    try:
        subject, html_body, text_body = composer.compose_digest(new_items, max_items=max_items)
    except Exception as exc:
        logger.exception("Failed to compose digest: %s", exc)
        return 6

    try:
        filename = storage.write_digest_html(subject, html_body, len(new_items))
        logger.info("Wrote digest HTML to digests/%s", filename)
    except Exception as exc:
        logger.exception("Failed to write digest HTML file: %s", exc)
        filename = None

    try:
        recips = recipients.get_recipients() or getattr(config, "EMAIL_TO", [])
    except Exception as exc:
        logger.exception("Failed to read recipients from DB; falling back to config.EMAIL_TO: %s", exc)
        recips = getattr(config, "EMAIL_TO", [])

    if not recips:
        logger.warning("No recipients configured; digest created but not sent")
        return 0

    try:
        send_individual = getattr(config, "SEND_INDIVIDUALLY", False)
        mailer.send_digest(
            recipients=recips,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            send_individually=send_individual,
        )
        logger.info(
            "Digest sent successfully to %d recipients (mode: %s); cached file: %s",
            len(recips),
            "individual" if send_individual else "bcc",
            filename or "<none>",
            )
    except Exception as exc:
        logger.exception("Failed to send digest: %s", exc)
        return 4

    try:
        _mark_articles_sent(new_items)
        logger.info("Marked %d articles as sent in DB", len(new_items))
    except Exception as exc:
        logger.exception("Failed to mark articles as sent: %s", exc)
        return 5

    logger.info("Run complete")
    return 0

if __name__ == "__main__":
    sys.exit(main())
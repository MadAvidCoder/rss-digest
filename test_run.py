## A script to test functionality without spamming users

import os
from dotenv import load_dotenv
load_dotenv()

import logging
import config
import db
import rss_manager
import composer
import mailer

logging.basicConfig(level=logging.DEBUG if config.DEBUG else logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("rss-digest_testing")

def _mask_recipients(rcpts):
    masked = []
    for r in rcpts:
        try:
            local, domain = r.split("@", 1)
            if len(local) <= 1:
                masked.append(f"*@{domain}")
            else:
                masked.append(f"{local[0]}***@{domain}")
        except Exception:
            masked.append("***@***")
    return masked

def ensure_one_feed():
    feeds = db.get_feeds(enabled_only=True)
    if not feeds:
        # fallback: add first configured FEED_URL if present
        fallback = getattr(config, "FEED_URLS", []) or []
        if fallback:
            url = fallback[0]
            logger.info("No feeds in DB; adding fallback feed: %s", url)
            db.add_feed(url)
            return True
        else:
            logger.warning("No feeds in DB and no FEED_URLS configured; nothing to test")
            return False
    return True

def main():
    logger.info("Starting test_run")

    try:
        db.init_db()
    except Exception as exc:
        logger.exception("DB init failed: %s", exc)
        return 1

    if not ensure_one_feed():
        return 2

    try:
        new_items = rss_manager.run_once(max_entries_per_feed=config.MAX_ENTRIES_PER_FEED, persist=False)
    except Exception as exc:
        logger.exception("rss_manager.run_once failed: %s", exc)
        return 3

    logger.info("Fetched %d new items", len(new_items))
    if not new_items:
        print("No new items. Nothing to preview or send.")
        return 0

    subject, html_body, text_body = composer.compose_digest(new_items, max_items=config.MAX_ITEMS)

    preview_path = os.path.join(os.getcwd(), "digest_preview.html")
    with open(preview_path, "w", encoding="utf-8") as f:
        f.write(html_body)
    logger.info("Wrote HTML preview to %s", preview_path)

    print("Subject:", subject)
    print("Recipients (masked):", ", ".join(_mask_recipients(list(config.EMAIL_TO))))
    print("DRY_RUN:", config.DRY_RUN)
    print("SKIP_SMTP_AUTH:", config.SKIP_SMTP_AUTH)
    print("SMTP_SERVER:", config.SMTP_SERVER, "SMTP_PORT:", config.SMTP_PORT)

    if not config.DRY_RUN:
        try:
            mailer.send_digest(
                recipients=config.EMAIL_TO,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                send_individually=config.SEND_INDIVIDUALLY,
            )
            logger.info("Sent digest via mailer")
        except Exception as exc:
            logger.exception("Failed to send digest: %s", exc)
            return 4
    else:
        logger.info("DRY_RUN enabled, not sending mail. Preview available at %s", preview_path)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
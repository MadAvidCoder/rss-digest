from typing import List, Dict, Optional, Any
import logging

import feeds
import db
import config

logger = logging.getLogger(__name__)

def _row_to_feed(row: Any) -> Dict[str, Optional[Any]]:
    if row is None:
        return {"id": None, "url": None, "category": None, "enabled": None, "added_at": None}

    if isinstance(row, dict):
        return {
            "id": row.get("id"),
            "url": row.get("url"),
            "category": row.get("category"),
            "enabled": row.get("enabled"),
            "added_at": row.get("added_at"),
        }

    try:
        return {
            "id": row[0],
            "url": row[1],
            "category": row[2] if len(row) > 2 else None,
            "enabled": row[3] if len(row) > 3 else None,
            "added_at": row[4] if len(row) > 4 else None,
        }
    except Exception:
        return {"id": None, "url": None, "category": None, "enabled": None, "added_at": None}

def run_once(
    feed_urls: Optional[List[str]] = None,
    max_entries_per_feed: Optional[int] = None,
) -> List[Dict]:
    new_articles: List[Dict] = []

    sources = []
    if feed_urls:
        for u in feed_urls:
            sources.append({"id": None, "url": u})
    else:
        try:
            raw_feeds = db.get_feeds(enabled_only=True)
            if not raw_feeds:
                cfg_urls = getattr(config, "FEED_URLS", None)
                if cfg_urls:
                    for u in cfg_urls:
                        sources.append({"id": None, "url": u})
                else:
                    logger.info("No feeds set in DB and no FEED_URLS configured in .env")
            else:
                for r in raw_feeds:
                    f = _row_to_feed(r)
                    if f.get("url"):
                        sources.append({"id": f.get("id"), "url": f.get("url")})
        except Exception as exc:
            logger.exception("Failed to read feeds from DB: %s", exc)
            cfg_urls = getattr(config, "FEED_URLS", None)
            if cfg_urls:
                for u in cfg_urls:
                    sources.append({"id": None, "url": u})
            else:
                return []

    if not sources:
        return []

    for src in sources:
        feed_id = src.get("id")
        url = src.get("url")
        if not url:
            continue
        if config.DEBUG:
            logger.info("Fetching feed %s (feed_id=%s)", url, feed_id)

        try:
            result = feeds.fetch_feed(url, max_entries=max_entries_per_feed)
        except Exception as exc:
            logger.exception("Failed to fetch feed %s (feed_id=%s): %s", url, feed_id, exc)
            continue

        entries = result.get("entries", []) if isinstance(result, dict) else []
        for e in entries:
            try:
                link = e.get("link") or ""
                title = e.get("title") or ""
                summary = e.get("summary") or ""
                published = e.get("published")

                if feed_id is not None:
                    try:
                        if db.article_exists(feed_id, link):
                            continue
                    except Exception:
                        logger.debug("article_exists check failed for feed_id=%s link=%s; will attempt insert", feed_id, link)

                try:
                    db.add_article(feed_id, title, link, summary, None, published)
                    new_articles.append({
                        "feed_id": feed_id,
                        "feed_url": url,
                        "guid": e.get("guid"),
                        "title": title,
                        "link": link,
                        "summary": summary,
                        "published": published,
                    })
                except Exception as exc:
                    logger.exception("Failed to insert article for feed %s: %s", url, exc)
                    continue

            except Exception as exc:
                logger.exception("Failed processing entry from feed %s: %s", url, exc)
                continue

    return new_articles
## Fetches new posts on the RSS feeds and handles/processes them

from datetime import datetime
import time
from typing import List, Dict, Optional, Any
import feedparser

USER_AGENT = "rss-digest/1.0 (+https://github.com/MadAvidCoder/rss-digest)"

def _parse_datetime_from_struct(t) -> Optional[datetime]:
    if not t:
        return None
    try:
        return datetime.fromtimestamp(time.mktime(t))
    except Exception:
        return None

def normalise_entry(e: Any) -> Dict:
    guid = e.get("id") or e.get("guid") or e.get("link") or e.get("title") or ""
    title = (e.get("title") or "").strip()
    link = e.get("link") or ""
    summary = e.get("summary") or e.get("description") or ""
    published = None
    if e.get("published_parsed"):
        published = _parse_datetime_from_struct(e.published_parsed)
    elif e.get("updated_parsed"):
        published = _parse_datetime_from_struct(e.updated_parsed)
    return {
        "guid": str(guid),
        "title": title,
        "link": link,
        "summary": summary,
        "published": published,
        "raw": e,
    }

def fetch_feed(
    url: str,
    timeout: int = 10,
    etag: Optional[str] = None,
    modified: Optional[float] = None,
    max_entries: Optional[int] = None,
) -> Dict:
    parse_kwargs = {
        "request_headers": {"User-Agent": USER_AGENT},
        "timeout": timeout,
    }
    if etag:
        parse_kwargs["etag"] = etag
    if modified:
        parse_kwargs["modified"] = modified

    d = feedparser.parse(url, **parse_kwargs)

    status = getattr(d, "status", None) or d.get("status")
    returned_etag = getattr(d, "etag", None) or d.get("etag")
    returned_modified = getattr(d, "modified", None) or d.get("modified")
    bozo = getattr(d, "bozo", False)
    bozo_exc = getattr(d, "bozo_exception", None)

    entries_raw = getattr(d, "entries", []) or d.get("entries", [])
    entries: List[Dict] = []

    for e in entries_raw:
        try:
            ne = normalise_entry(e)
            entries.append(ne)
            if max_entries and len(entries) >= max_entries:
                break
        except Exception:
            continue

    return {
        "entries": entries,
        "status": status,
        "etag": returned_etag,
        "modified": returned_modified,
        "bozo": bozo,
        "bozo_exception": bozo_exc,
    }
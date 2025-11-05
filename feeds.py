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
    headers = {"User-Agent": USER_AGENT}
    if etag:
        headers["If-None-Match"] = etag
    if modified:
        headers["If-Modified-Since"] = modified

    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        return {
            "entries": [],
            "status": None,
            "etag": None,
            "modified": None,
            "bozo": True,
            "bozo_exception": exc,
        }

    status = resp.status_code
    returned_etag = resp.headers.get("ETag")
    returned_modified = resp.headers.get("Last-Modified")

    if status == 304:
        return {
            "entries": [],
            "status": status,
            "etag": returned_etag,
            "modified": returned_modified,
            "bozo": False,
            "bozo_exception": None,
        }

    content = resp.content or b""
    d = feedparser.parse(content)

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
## Handles caching of html digests

from pathlib import Path
import json
from datetime import datetime, UTC
from typing import List, Dict

BASE = Path.cwd()
DIGESTS_DIR = BASE / "digests"
DIGEST_INDEX = DIGESTS_DIR / "index.json"

DIGESTS_DIR.mkdir(exist_ok=True)

def load_digest_index() -> List[Dict]:
    if not DIGEST_INDEX.exists():
        DIGEST_INDEX.write_text("[]", encoding="utf-8")
        return []
    return json.loads(DIGEST_INDEX.read_text(encoding="utf-8"))

def save_digest_index(index: List[Dict]) -> None:
    DIGEST_INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

def add_digest_entry(subject: str, filename: str, item_count: int) -> Dict:
    index = load_digest_index()
    entry = {
        "subject": subject,
        "filename": filename,
        "item_count": item_count,
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
    }
    index.insert(0, entry)
    index = index[:50]
    save_digest_index(index)
    return entry

def write_digest_html(subject: str, html_body: str, item_count: int) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    filename = f"digest-{stamp}.html"
    outpath = DIGESTS_DIR / filename
    outpath.write_text(html_body, encoding="utf-8")
    add_digest_entry(subject, filename, item_count)
    return filename
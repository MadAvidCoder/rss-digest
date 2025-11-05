from typing import List, Dict, Optional, Tuple
from datetime import datetime, UTC
from jinja2 import Template
import re
import config

HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>{{ subject }}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial; color: #111; line-height: 1.4; padding: 18px; }
    a { color: #1a73e8; text-decoration: none; }
    .item { margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #eee; }
    .meta { color: #666; font-size: 12px; margin-bottom: 6px; }
    .title { font-size: 16px; margin: 6px 0; }
    .summary { color: #222; }
    header { margin-bottom: 18px; }
    footer { margin-top: 24px; color: #888; font-size: 12px; }
  </style>
</head>
<body>
  <header>
    <h2>{{ subject }}</h2>
    {% if intro %}<p>{{ intro }}</p>{% endif %}
  </header>

  {% for it in items %}
    <article class="item">
      <div class="meta">
        {% if it.feed_title %}<strong>{{ it.feed_title }}</strong>{% else %}{{ it.feed_url }}{% endif %}
        {% if it.category %} · {{ it.category }}{% endif %}
        {% if it.published %} · {{ it.published|datetimeformat }}{% endif %}
      </div>
      <div class="title"><a href="{{ it.link }}">{{ it.title }}</a></div>
      <div class="summary">{{ it.summary | safe }}</div>
    </article>
  {% endfor %}

  <footer>
    <div>Sent by {{ from_name }}</div>
  </footer>
</body>
</html>
"""

TEXT_ITEM_TMPL = """{feed}{category}{published}
{title}
{link}

{summary}
"""

def _datetimeformat(value: Optional[datetime]) -> str:
    if not value:
        return ""
    try:
        return value.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(value)

def _html_to_text(html: str) -> str:
    html = re.sub(r"(?is)<(script|style).*?>.*?</\1>", "", html)
    html = re.sub(r"(?i)<br\s*/?>", "\n", html)
    html = re.sub(r"(?i)</p\s*>", "\n\n", html)

    def _a_repl(m):
        t = re.sub(r"<[^>]+>", "", m.group(0))
        href = re.search(r'href=[\'"]([^\'"]+)[\'"]', m.group(0))
        if href:
            return f"{t} ({href.group(1)})"
        return t

    html = re.sub(r"(?i)<a\b[^>]*>.*?</a>", _a_repl, html)
    text = re.sub(r"<[^>]+>", "", html)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = re.sub(r"\n\s+\n", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()

def _format_text_items(items: List[Dict]) -> str:
    parts: List[str] = []
    for it in items:
        feed = it.get("feed_title") or it.get("feed_url") or ""
        category = f" [{it.get('category')}]" if it.get("category") else ""
        published = ""
        if it.get("published"):
            published = f" · {_datetimeformat(it['published'])}"
        title = it.get("title") or ""
        link = it.get("link") or ""
        raw_summary = it.get("summary") or ""
        summary = _html_to_text(raw_summary)
        parts.append(TEXT_ITEM_TMPL.format(
            feed=feed,
            category=category,
            published=published,
            title=title,
            link=link,
            summary=summary,
        ).rstrip())
    return "\n\n".join(parts).strip()

def compose_digest(items: List[Dict], subject_override: Optional[str] = None, max_items: Optional[int] = None, intro: Optional[str] = None) -> Tuple[str, str, str]:
    if max_items is not None:
        items = items[:max_items]

    subject = subject_override or f"{getattr(config, 'SUBJECT_PREFIX', '[RSS Digest]')} Daily Digest — {datetime.now(UTC).date()}"

    tpl = Template(HTML_TEMPLATE)
    tpl.environment.filters["datetimeformat"] = _datetimeformat

    html = tpl.render(subject=subject, items=items, intro=intro or "", from_name=getattr(config, "FROM_NAME", "RSS Digest"))
    text_body = _format_text_items(items)
    if not text_body:
        text_body = f"{subject}\n\nNo new items."

    return subject, html, text_body
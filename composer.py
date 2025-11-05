from typing import List, Dict, Optional, Tuple
from datetime import datetime, UTC
from jinja2 import Template
import re
import html
import config

HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>{{ subject }}</title>
  <style>
    :root{
      --bg:#f6f8fa; --card:#ffffff; --muted:#6b7280; --accent:#1f6feb;
      --border:#e6e9ee; --maxw:720px;
      --radius:10px;
    }
    body{background:var(--bg); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
      Roboto, "Helvetica Neue", Arial; color:#0f172a; margin:0; padding:24px;}
    .wrapper{max-width:var(--maxw); margin:0 auto;}
    .header{background:linear-gradient(90deg,#fff 0%, #fbfdff 100%); padding:18px 20px; border-radius:12px; border:1px solid var(--border); margin-bottom:16px;}
    .logo{display:flex; align-items:center; gap:12px;}
    .brand{font-weight:700; font-size:18px; color:var(--accent);}
    .sub{color:var(--muted); font-size:13px;}
    .toc{background:transparent; padding:12px 0 8px 0; color:var(--muted); font-size:14px;}
    .toc a{color:var(--accent); text-decoration:none;}
    .card{background:var(--card); border:1px solid var(--border); border-radius:8px; padding:16px; margin-bottom:12px;}
    .meta{color:var(--muted); font-size:13px; margin-bottom:6px;}
    .title{font-size:17px; margin:4px 0 8px 0; font-weight:600;}
    .summary{color:#111827; line-height:1.45; margin-bottom:12px;}
    .actions{display:flex; gap:8px; align-items:center;}
    .btn{background:var(--accent); color:#fff; padding:8px 12px; border-radius:6px; text-decoration:none; font-size:13px;}
    .read-more{background:#fff; color:var(--accent); border:1px solid var(--accent); padding:6px 10px; border-radius:6px; text-decoration:none; font-size:13px;}
    footer{margin-top:18px; color:var(--muted); font-size:13px; text-align:center;}
    @media (max-width:520px){
      .title{font-size:15px;}
      .header{padding:12px;}
    }
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      <div class="logo">
        <div>
          <div class="brand">{{ from_name }}</div>
          <div class="sub">{{ subject }}</div>
        </div>
      </div>
      {% if intro %}
        <p style="margin-top:10px; color:var(--muted)">{{ intro }}</p>
      {% endif %}
      <div class="toc">
        <strong>In this digest ({{ items|length }})</strong>
        <ul>
          {% for it in items %}
            <li><a href="#item-{{ loop.index0 }}">{{ loop.index }}. {{ it.title }}</a> <span style="color:var(--muted)">— {{ it.feed_title or it.feed_url }}</span></li>
          {% endfor %}
        </ul>
      </div>
    </div>

    {% for it in items %}
      <article id="item-{{ loop.index0 }}" class="card">
        <div class="meta">
          {% if it.feed_title %}<strong>{{ it.feed_title }}</strong>{% else %}{{ it.feed_url }}{% endif %}
          {% if it.category %} · {{ it.category }}{% endif %}
          {% if it.published %} · {{ it.published|datetimeformat }}{% endif %}
        </div>
        <div class="title"><a href="{{ it.link }}" style="color:inherit; text-decoration:none;">{{ it.title }}</a></div>
        <div class="summary">{{ it.summary | safe }}</div>
        <div class="actions" style="margin-top:12px;">
          <a class="btn" href="{{ it.link }}" target="_blank" rel="noopener">Read full article</a>
          <a class="read-more" href="{{ it.link }}" target="_blank" rel="noopener">Open</a>
        </div>
      </article>
    {% endfor %}

    <footer>
      Sent by {{ from_name }} — <span style="color:var(--muted)">generated {{ generated_at }}</span>
    </footer>
  </div>
</body>
</html>
"""

TEXT_TOC = "In this digest ({count})\n\n{toc}\n\n"
TEXT_ITEM_TMPL = """{index}. {title}
{feed}{category}{published}
{link}

{summary}
---
"""

def _datetimeformat(value: Optional[datetime]) -> str:
    if not value:
        return ""
    try:
        return value.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(value)

def _strip_tags(html_text: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", "", html_text)
    def _a_repl(m):
        tag = m.group(0)
        href = re.search(r'href=[\'"]([^\'"]+)[\'"]', tag)
        inner = re.sub(r"<[^>]+>", "", tag)
        if href:
            return f"{inner} ({href.group(1)})"
        return inner
    text = re.sub(r"(?i)<a\b[^>]*>.*?</a>", _a_repl, text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r'\s+\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    return text.strip()

def _truncate_text(s: str, max_chars: int = 600) -> str:
    if not s:
        return ""
    if len(s) <= max_chars:
        return s
    cut = s.rfind('.', 0, max_chars)
    if cut > max_chars * 0.5:
        return s[:cut+1].strip() + "…"
    return s[:max_chars].rstrip() + "…"

def _prepare_item(it: Dict, max_summary_chars: int) -> Dict:
    summary_html = it.get("summary") or ""
    summary_text = _strip_tags(summary_html)
    short_summary = _truncate_text(summary_text, max_summary_chars) if max_summary_chars else summary_text
    return {
        **it,
        "summary_text": summary_text,
        "summary": summary_html if summary_html else html.escape(short_summary),
        "short_summary": short_summary,
    }

def compose_digest(
    items: List[Dict],
    subject_override: Optional[str] = None,
    max_items: Optional[int] = None,
    intro: Optional[str] = None,
    include_toc: bool = True,
    max_summary_chars: int = 600,
) -> Tuple[str, str, str]:
    if max_items is not None:
        items = items[:max_items]

    prepared = []
    for it in items:
        prepared.append(_prepare_item(it, max_summary_chars))

    subject = subject_override or f"{getattr(config, 'SUBJECT_PREFIX', '[RSS]')} Daily Digest — {datetime.utcnow().date()}"
    tpl = Template(HTML_TEMPLATE)
    tpl.environment.filters["datetimeformat"] = _datetimeformat

    html_body = tpl.render(
        subject=subject,
        items=prepared,
        intro=intro or "",
        from_name=getattr(config, "FROM_NAME", "RSS Digest"),
        generated_at=datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
    )

    toc_lines = []
    for idx, it in enumerate(prepared, start=1):
        feed = it.get("feed_title") or it.get("feed_url") or ""
        toc_lines.append(f"{idx}. {it.get('title')} — {feed}")

    toc_text = "\n".join(toc_lines)
    text_parts = []
    if include_toc:
        text_parts.append(TEXT_TOC.format(count=len(prepared), toc=toc_text))

    for idx, it in enumerate(prepared, start=1):
        feed = it.get("feed_title") or it.get("feed_url") or ""
        category = f" [{it.get('category')}]" if it.get("category") else ""
        published = ""
        if it.get("published"):
            published = f" · {_datetimeformat(it['published'])}"
        title = it.get("title") or ""
        link = it.get("link") or ""
        summary = it.get("short_summary") or _strip_tags(it.get("summary_text") or "")
        text_parts.append(TEXT_ITEM_TMPL.format(
            index=idx,
            title=title,
            feed=feed,
            category=category,
            published=published,
            link=link,
            summary=summary
        ).rstrip())

    text_body = "\n\n".join(text_parts).strip()
    if not text_body:
        text_body = f"{subject}\n\nNo new items."

    return subject, html_body, text_body
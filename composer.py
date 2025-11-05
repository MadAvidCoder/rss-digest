from typing import List, Dict, Optional, Tuple
from datetime import datetime, UTC
from jinja2 import Template
import re
import html
from urllib.parse import urlparse, urljoin
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
      --bg: #f5f7fb;
      --panel: #ffffff;
      --muted: #6b7280;
      --accent: #0f62fe;
      --accent-2: #1464f4;
      --card-border: #e6eaf0;
      --radius:12px;
      --maxw:760px;
      --shadow: 0 6px 18px rgba(18, 21, 26, 0.06);
    }
    html,body{height:100%}
    body{
      margin:0; padding:22px; background:var(--bg);
      font-family: Inter, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
      color:#0f172a;
      -webkit-font-smoothing:antialiased;
      -moz-osx-font-smoothing:grayscale;
    }
    .container{max-width:var(--maxw); margin:0 auto;}
    .panel{background:var(--panel); border-radius:16px; padding:18px; box-shadow:var(--shadow); border:1px solid var(--card-border);}
    .header{display:flex; align-items:center; gap:14px; padding-bottom:12px; border-bottom:1px solid #f0f3f7;}
    .brand {font-weight:700; font-size:20px; color:var(--accent);}
    .tagline{color:var(--muted); font-size:13px;}
    .meta-row{display:flex; gap:8px; align-items:center; margin-left:auto; color:var(--muted); font-size:13px;}
    .toc{margin:14px 0; color:var(--muted); font-size:14px;}
    .toc ul{padding-left:18px; margin:6px 0;}
    .toc a{color:var(--accent); text-decoration:none;}
    .items{margin-top:14px; display:flex; flex-direction:column; gap:12px;}
    .item{display:flex; gap:12px; align-items:flex-start; padding:12px; border-radius:12px; background:linear-gradient(180deg, rgba(255,255,255,0.6), rgba(255,255,255,0.6)); border:1px solid #f1f4f8;}
    .left {flex:1 1 auto; min-width:0;}
    .thumbnail{width:156px; height:100px; flex:0 0 156px; border-radius:8px; object-fit:cover; border:1px solid var(--card-border); background:#f7fafc;}
    .title{font-size:16px; font-weight:700; margin:0 0 6px 0; color:#071033;}
    .summary{color:#0b1220; font-size:14px; line-height:1.4; margin-bottom:8px; overflow:hidden;}
    .meta{color:var(--muted); font-size:13px; margin-bottom:8px;}
    .actions{display:flex; gap:8px; align-items:center;}
    .btn{
      display:inline-block; padding:9px 12px; border-radius:8px; color:#fff; text-decoration:none; font-size:13px;
      background:linear-gradient(90deg,var(--accent),var(--accent-2));
      box-shadow: 0 6px 18px rgba(15,98,254,0.12);
    }
    .muted-link{color:var(--accent); text-decoration:none; font-weight:600; font-size:13px;}
    .feed-badge{display:inline-flex; gap:8px; align-items:center;}
    .feed-icon{width:28px; height:28px; border-radius:6px; object-fit:cover; border:1px solid var(--card-border); background:#fff;}
    footer{margin-top:18px; font-size:13px; color:var(--muted); text-align:center;}
    @media (max-width:720px){
      .item{flex-direction:column;}
      .thumbnail{width:100%; height:170px; flex:0 0 auto;}
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="panel">
      <div class="header">
        <div style="display:flex;gap:12px;align-items:center">
          <img src="{{ brand_icon }}" alt="" width="44" height="44" style="border-radius:10px;object-fit:cover;border:1px solid #eee;"/>
          <div>
            <div class="brand">{{ from_name }}</div>
            <div class="tagline">{{ subject }}</div>
          </div>
        </div>
        <div class="meta-row">
          <div>generated {{ generated_at }}</div>
        </div>
      </div>

      {% if intro %}
      <div style="margin-top:12px;color:var(--muted)">{{ intro }}</div>
      {% endif %}

      {% if items %}
      <div class="toc">
        <strong>In this digest ({{ items|length }})</strong>
        <ul>
          {% for it in items %}
            <li><a href="#item-{{ loop.index0 }}">{{ loop.index }}. {{ it.title }}</a> — <span style="color:var(--muted)">{{ it.feed_title or it.feed_url }}</span></li>
          {% endfor %}
        </ul>
      </div>

      <div class="items">
        {% for it in items %}
        <article id="item-{{ loop.index0 }}" class="item">
          <div class="left">
            <div class="feed-badge" style="margin-bottom:8px">
              <img class="feed-icon" src="{{ it.feed_icon }}" alt="" />
              <div style="font-size:13px;color:var(--muted)">{{ it.feed_title or it.feed_url }}</div>
            </div>
            <div class="title"><a class="muted-link" href="{{ it.link }}">{{ it.title }}</a></div>
            <div class="meta">
              {% if it.category %}<span>{{ it.category }}</span> · {% endif %}
              {% if it.published %}<span>{{ it.published|datetimeformat }}</span>{% endif %}
            </div>
            <div class="summary">{{ it.summary | safe }}</div>
            <div class="actions">
              <a class="btn" href="{{ it.link }}" target="_blank" rel="noopener">Read article</a>
              <a class="muted-link" href="{{ it.link }}" target="_blank" rel="noopener">Open in new tab</a>
            </div>
          </div>
          {% if it.thumbnail %}
            <img class="thumbnail" src="{{ it.thumbnail }}" alt="thumbnail"/>
          {% else %}
            <div style="width:156px;height:100px;display:flex;align-items:center;justify-content:center;color:var(--muted);font-size:13px;border-radius:8px;background:#fafbfc;border:1px solid var(--card-border)">{{ it.feed_title or "" }}</div>
          {% endif %}
        </article>
        {% endfor %}
      </div>
      {% else %}
        <div style="padding:18px;color:var(--muted)">No new items.</div>
      {% endif %}

      <footer>
        Sent by {{ from_name }} — <span style="color:var(--muted)">generated {{ generated_at }}</span>
      </footer>
    </div>
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

def _get_origin(url: str) -> str:
    try:
        p = urlparse(url)
        if not p.scheme:
            return "https://" + p.netloc
        return f"{p.scheme}://{p.netloc}"
    except Exception:
        return ""

def _get_domain_only(url: str) -> str:
    try:
        p = urlparse(url)
        host = p.netloc or url
        if ":" in host:
            host = host.split(":")[0]
        return host
    except Exception:
        return url

def _favicon_url_for_feed(feed_url: Optional[str]) -> str:
    if not feed_url:
        return ""
    domain = _get_domain_only(feed_url)
    return f"https://icons.duckduckgo.com/ip3/{domain}.ico"

def _make_urls_absolute(html_fragment: str, base_url: Optional[str]) -> str:
    if not html_fragment or not base_url:
        return html_fragment or ""

    def repl_src(m):
        orig = m.group(1)
        if re.match(r"^(data:|cid:|http:|https:|mailto:|javascript:)", orig, re.I):
            return f'src="{orig}"'
        try:
            absolute = urljoin(base_url, orig)
            return f'src="{absolute}"'
        except Exception:
            return f'src="{orig}"'

    def repl_href(m):
        orig = m.group(1)
        if re.match(r"^(http:|https:|mailto:|javascript:|#)", orig, re.I):
            return f'href="{orig}"'
        try:
            absolute = urljoin(base_url, orig)
            return f'href="{absolute}"'
        except Exception:
            return f'href="{orig}"'

    html_fragment = re.sub(r'src=["\']([^"\']+)["\']', repl_src, html_fragment, flags=re.I)
    html_fragment = re.sub(r'href=["\']([^"\']+)["\']', repl_href, html_fragment, flags=re.I)
    return html_fragment


def _extract_first_image(html_fragment: str, base_url: Optional[str]) -> Optional[str]:
    if not html_fragment:
        return None
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html_fragment, flags=re.I)
    if not m:
        return None
    src = m.group(1)
    if re.match(r'^(http:|https:|data:|cid:)', src, re.I):
        return src
    try:
        return urljoin(base_url or "", src)
    except Exception:
        return src

def _strip_tags(html_text: str) -> str:
    if not html_text:
        return ""
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
    feed_url = it.get("feed_url") or it.get("feed") or ""
    base = _get_origin(feed_url) or feed_url
    summary_html = it.get("summary") or it.get("raw", {}).get("summary", "") or ""
    summary_html_abs = _make_urls_absolute(summary_html, base)
    thumbnail = _extract_first_image(summary_html_abs, base)
    if thumbnail and not re.match(r'^(http:|https:|data:|cid:)', thumbnail, re.I):
        thumbnail = urljoin(base, thumbnail)
    summary_text = _strip_tags(summary_html_abs)
    short_summary = _truncate_text(summary_text, max_summary_chars) if max_summary_chars else summary_text
    feed_icon = _favicon_url_for_feed(feed_url) or ""
    return {
        **it,
        "summary": summary_html_abs or html.escape(short_summary),
        "summary_text": summary_text,
        "short_summary": short_summary,
        "thumbnail": thumbnail,
        "feed_icon": feed_icon,
        "feed_title": it.get("feed_title") or it.get("feed_name") or None,
    }


def compose_digest(
    items: List[Dict],
    subject_override: Optional[str] = None,
    max_items: Optional[int] = None,
    intro: Optional[str] = None,
    max_summary_chars: int = 600,
) -> Tuple[str, str, str]:
    if max_items is not None:
        items = items[:max_items]

    prepared = [_prepare_item(it, max_summary_chars) for it in items]

    subject = subject_override or f"{getattr(config, 'SUBJECT_PREFIX', '[RSS]')} Daily Digest — {datetime.utcnow().date()}"
    tpl = Template(HTML_TEMPLATE)
    tpl.environment.filters["datetimeformat"] = _datetimeformat

    brand_icon = ""
    if prepared:
        brand_icon = prepared[0].get("feed_icon") or _favicon_url_for_feed(prepared[0].get("feed_url"))
    if not brand_icon:
        brand_icon = "https://icons.duckduckgo.com/ip3/rss-digest.local.ico"

    html_body = tpl.render(
        subject=subject,
        items=prepared,
        intro=intro or "",
        from_name=getattr(config, "FROM_NAME", "RSS Digest"),
        generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        brand_icon=brand_icon,
    )

    toc_lines = []
    for idx, it in enumerate(prepared, start=1):
        feed = it.get("feed_title") or it.get("feed_url") or ""
        toc_lines.append(f"{idx}. {it.get('title')} — {feed}")
    toc_text = "\n".join(toc_lines)
    text_parts = []
    if toc_text:
        text_parts.append(TEXT_TOC.format(count=len(prepared), toc=toc_text))

    for idx, it in enumerate(prepared, start=1):
        feed = it.get("feed_title") or it.get("feed_url") or ""
        category = f" [{it.get('category')}]" if it.get("category") else ""
        published = f" · {_datetimeformat(it['published'])}" if it.get("published") else ""
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
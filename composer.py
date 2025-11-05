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
    @media only screen and (max-width:620px){
      .container{width:100% !important;}
      .two-col{display:block !important; width:100% !important;}
      .col{display:block !important; width:100% !important;}
      .thumbnail{width:100% !important; height:auto !important;}
      .feed-badge{display:inline-flex;align-items:center;gap:8px;}
    }
    /* Minimal head styles; main styles inline for maximum client support */
  </style>
</head>
<body style="margin:0;padding:0;background-color:#f5f7fb;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;">
  <!-- Preheader -->
  <span style="display:none !important; visibility:hidden; mso-hide:all; font-size:1px; line-height:1px; max-height:0; max-width:0; opacity:0; overflow:hidden;">
    {{ preheader }}
  </span>

  <table width="100%" cellpadding="0" cellspacing="0" border="0" role="presentation" style="background-color:#f5f7fb;width:100%;padding:18px 12px;">
    <tr><td align="center">
      <table class="container" width="720" cellpadding="0" cellspacing="0" border="0" role="presentation" style="width:720px;max-width:720px;">
        <!-- Header -->
        <tr>
          <td style="padding:12px 0;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0" role="presentation" style="background:#ffffff;border-radius:10px;padding:14px;border:1px solid #e9eef5;">
              <tr>
                <td style="vertical-align:middle;">
                  <table width="100%" cellpadding="0" cellspacing="0" border="0" role="presentation">
                    <tr>
                      <td style="vertical-align:middle;">
                        <img src="{{ brand_icon }}" width="48" height="48" alt="" style="display:block;border-radius:10px;border:1px solid #eef3fa;"/>
                      </td>
                      <td style="vertical-align:middle;padding-left:12px;">
                        <div style="font-size:18px;font-weight:700;color:#0b2a66;line-height:1.05;">{{ from_name }}</div>
                        <div style="font-size:13px;color:#6b7280;margin-top:6px;">{{ subject }}</div>
                      </td>
                      <td style="vertical-align:middle;text-align:right;">
                        <div style="font-size:12px;color:#94a3b8;">{{ generated_at }}</div>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>

              {% if intro %}
              <tr><td style="padding-top:8px;padding-bottom:6px;color:#374151;font-size:14px;">{{ intro }}</td></tr>
              {% endif %}

              <!-- Compact feeds summary and small jump link -->
              {% if feed_list %}
              <tr>
                <td style="padding-top:6px;padding-bottom:6px;">
                  <table width="100%" cellpadding="0" cellspacing="0" border="0" role="presentation">
                    <tr>
                      <td style="vertical-align:middle;">
                        {% for f in feed_list %}
                          <span style="display:inline-flex;align-items:center;gap:8px;margin-right:10px;margin-bottom:6px;font-size:13px;">
                            <img src="{{ f.icon }}" width="18" height="18" alt="" style="display:block;border-radius:4px;border:1px solid #eef3fa;"/>
                            <span style="color:#0f172a;">{{ f.name }}</span>
                            <span style="color:#94a3b8;font-size:12px;margin-left:6px;">({{ f.count }})</span>
                          </span>
                        {% endfor %}
                      </td>
                      <td style="text-align:right;vertical-align:middle;">
                        <a href="#full-toc" style="color:#0f62fe;text-decoration:none;font-size:13px;font-weight:600;">Jump to full table of contents</a>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
              {% endif %}
            </table>
          </td>
        </tr>

        <!-- Items -->
        {% for it in items %}
        <tr>
          <td style="padding-top:12px;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0" role="presentation" style="background:#ffffff;border-radius:10px;border:1px solid #e9eef5;">
              <tr>
                <td style="padding:12px;">
                  <table width="100%" cellpadding="0" cellspacing="0" border="0" role="presentation">
                    <tr class="two-col">
                      <!-- Content -->
                      <td class="col" valign="top" style="padding-right:12px;vertical-align:top;">
                        <table cellpadding="0" cellspacing="0" border="0" role="presentation" width="100%">
                          <tr><td style="padding-bottom:6px;">
                            <table cellpadding="0" cellspacing="0" border="0" role="presentation">
                              <tr>
                                <td style="vertical-align:middle;padding-right:8px;">
                                  <img src="{{ it.feed_icon }}" width="28" height="28" alt="" style="display:block;border-radius:6px;border:1px solid #eef3fa;" />
                                </td>
                                <td style="vertical-align:middle;font-size:13px;color:#6b7280;">
                                  <strong style="font-weight:700;color:#0b2a66;">{{ it.feed_title or it.feed_url }}</strong>
                                </td>
                              </tr>
                            </table>
                          </td></tr>

                          <tr><td style="padding-bottom:8px;"><a href="{{ it.link }}" style="color:#071033;text-decoration:none;font-size:16px;font-weight:700;">{{ it.title }}</a></td></tr>

                          <tr><td style="padding-bottom:8px;color:#6b7280;font-size:13px;">{% if it.category %}{{ it.category }} · {% endif %}{% if it.published %}{{ it.published|datetimeformat }}{% endif %}</td></tr>

                          <tr><td style="padding-bottom:10px;color:#333a52;font-size:14px;line-height:1.45;">{{ it.summary | safe }}</td></tr>

                          <tr>
                            <td>
                              <!-- Primary button only -->
                              <table cellpadding="0" cellspacing="0" border="0" role="presentation">
                                <tr>
                                  <td>
                                    <a href="{{ it.link }}" style="background-color:#0f62fe;border-radius:6px;color:#ffffff;display:inline-block;padding:10px 14px;text-decoration:none;font-weight:600;font-size:13px;">
                                      Read article →
                                    </a>
                                  </td>
                                </tr>
                              </table>
                            </td>
                          </tr>

                        </table>
                      </td>

                      <!-- Thumbnail -->
                      <td class="col" valign="top" style="width:180px;">
                        {% if it.thumbnail %}
                          <a href="{{ it.link }}"><img alt="" class="thumbnail" src="{{ it.thumbnail }}" width="170" height="110" style="display:block;border-radius:8px;border:1px solid #eef3fa;object-fit:cover;max-width:100%;height:auto;" /></a>
                        {% else %}
                          <div style="width:170px;height:110px;border-radius:8px;border:1px solid #eef3fa;background:#fbfdff;color:#6b7280;display:flex;align-items:center;justify-content:center;font-size:13px;">
                            {{ it.feed_title or '' }}
                          </div>
                        {% endif %}
                      </td>

                    </tr>
                  </table>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        {% endfor %}

        <!-- Full TOC at the bottom (out of the way of the header) -->
        {% if items %}
        <tr>
          <td style="padding-top:12px;">
            <a id="full-toc"></a>
            <table width="100%" cellpadding="0" cellspacing="0" border="0" role="presentation" style="background:#ffffff;border-radius:10px;padding:12px;border:1px solid #e9eef5;">
              <tr>
                <td style="font-size:14px;color:#0b2a66;font-weight:700;padding-bottom:8px;">Full table of contents</td>
              </tr>
              {% for it in items %}
              <tr>
                <td style="padding:8px 0;border-top:1px solid #f1f5f9;">
                  <a href="#item-{{ loop.index0 }}" style="color:#0f62fe;text-decoration:none;font-size:14px;">{{ loop.index }}. {{ it.title }}</a>
                  <div style="color:#8292a6;font-size:12px;margin-top:4px;">{{ it.feed_title or it.feed_url }}</div>
                </td>
              </tr>
              {% endfor %}
            </table>
          </td>
        </tr>
        {% endif %}

        <tr><td style="padding-top:14px;text-align:center;">
          <table cellpadding="0" cellspacing="0" border="0" role="presentation">
            <tr><td style="font-size:13px;color:#94a3b8;">Sent by {{ from_name }} — {{ generated_at }}</td></tr>
          </table>
        </td></tr>

      </table>
    </td></tr>
  </table>
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

def _strip_first_image_from_html(html_fragment: str) -> str:
    if not html_fragment:
        return ""
    return re.sub(r'<img\b[^>]*>', '', html_fragment, count=1, flags=re.I)

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

def _generate_inline_svg_brand() -> str:
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' width='120' height='120' viewBox='0 0 120 120'>"
        "<defs>"
        "<linearGradient id='g' x1='0' x2='1' y1='0' y2='1'>"
        "<stop offset='0' stop-color='#0f62fe'/>"
        "<stop offset='1' stop-color='#1464f4'/>"
        "</linearGradient>"
        "</defs>"
        "<rect width='120' height='120' rx='18' fill='url(#g)'/>"
        "<text x='50%' y='56%' dominant-baseline='middle' text-anchor='middle' font-family='Arial, Helvetica, sans-serif' font-size='46' fill='white' font-weight='700'>RD</text>"
        "</svg>"
    )
    data_uri = "data:image/svg+xml;utf8," + svg.replace('"', "'")
    return data_uri

def _prepare_item(it: Dict, max_summary_chars: int) -> Dict:
    feed_url = it.get("feed_url") or it.get("feed") or ""
    base = _get_origin(feed_url) or feed_url
    summary_html = it.get("summary") or it.get("raw", {}).get("summary", "") or ""
    summary_html_abs = _make_urls_absolute(summary_html, base)
    thumbnail = _extract_first_image(summary_html_abs, base)
    summary_without_first_img = _strip_first_image_from_html(summary_html_abs)
    if thumbnail and not re.match(r'^(http:|https:|data:|cid:)', thumbnail, re.I):
        thumbnail = urljoin(base, thumbnail)
    summary_text = _strip_tags(summary_without_first_img)
    short_summary = _truncate_text(summary_text, max_summary_chars) if max_summary_chars else summary_text
    feed_icon = _favicon_url_for_feed(feed_url) or ""
    return {
        **it,
        "summary": summary_without_first_img or html.escape(short_summary),
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
    preheader: Optional[str] = None
) -> Tuple[str, str, str]:
    if max_items is not None:
        items = items[:max_items]

    prepared = [_prepare_item(it, max_summary_chars) for it in items]

    feed_counts: Dict[str, Dict] = {}
    for it in prepared:
        name = (it.get("feed_title") or it.get("feed_url") or "unknown").strip()
        icon = it.get("feed_icon") or _favicon_url_for_feed(it.get("feed_url"))
        key = name
        if key not in feed_counts:
            feed_counts[key] = {"name": name, "icon": icon, "count": 0}
        feed_counts[key]["count"] += 1
    feed_list = list(feed_counts.values())

    subject = subject_override or f"{getattr(config, 'SUBJECT_PREFIX', '[RSS]')} Daily Digest — {datetime.now(UTC).date()}"

    if not preheader:
        if intro:
            pre = intro.strip()
        elif prepared and prepared[0].get("short_summary"):
            pre = prepared[0]["short_summary"][:140]
        else:
            pre = subject
    else:
        pre = preheader

    tpl = Template(HTML_TEMPLATE)
    tpl.environment.filters["datetimeformat"] = _datetimeformat

    brand_icon = ""
    if prepared:
        brand_icon = prepared[0].get("feed_icon") or _favicon_url_for_feed(prepared[0].get("feed_url"))
    if not brand_icon:
        brand_icon = _generate_inline_svg_brand()

    html_body = tpl.render(
        subject=subject,
        items=prepared,
        intro=intro or "",
        from_name=getattr(config, "FROM_NAME", "RSS Digest"),
        generated_at=datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        brand_icon=brand_icon,
        feed_list=feed_list,
        preheader=pre,
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
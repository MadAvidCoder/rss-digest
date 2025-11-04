## Handles all SMTP and mailing operations

from email.message import EmailMessage
import smtplib
import ssl
import re
from typing import List, Optional, Union
import config
import logging

logger = logging.getLogger(__name__)
SMTP_TIMEOUT = 30

def _normalise_recipients(recipients: Union[str, List[str]]) -> List[str]:
    if isinstance(recipients, str):
        return [r.strip() for r in recipients.split(',') if r.strip()]
    return [r.strip() for r in recipients if r and r.strip()]

def _mask_recipients(recipients: List[str]) -> List[str]:
    masked = []
    for r in recipients:
        try:
            local, domain = r.split("@", 1)
            if len(local) <= 1:
                m = f"*@{domain}"
            else:
                m = f"{local[0]}***@{domain}"
            masked.append(m)
        except Exception:
            masked.append("***@***")
    return masked

def _build_message(from_addr: str, to_addr: str, subject: str, html_body: str, text_body: str, reply_to: Optional[str]) -> EmailMessage:
    msg = EmailMessage()
    display_from = f"{getattr(config, 'FROM_NAME', '')} <{from_addr}>" if getattr(config, "FROM_NAME", None) else from_addr
    msg["From"] = display_from
    msg["To"] = to_addr
    msg["Subject"] = subject
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")
    return msg

def html_to_text(html: str) -> str:
    html = re.sub(r"(?is)<(script|style).*?>.*?</\1>", "", html)
    html = re.sub(r"(?i)<br\s*/?>", "\n", html)
    html = re.sub(r"(?i)</p\s*>", "\n\n", html)
    text = re.sub(r"<[^>]+>", "", html)
    text = re.sub(r"\n\s+\n", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()

def send_digest(
    recipients: Union[str, List[str]],
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
    reply_to: Optional[str] = None,
    send_individually: bool = True,
) -> None:
    rcpts = _normalise_recipients(recipients)
    if not rcpts:
        raise ValueError("send_digest(): No recipients provided")

    from_addr = config.EMAIL_FROM
    if not from_addr:
        raise RuntimeError("send_digest(): EMAIL_FROM is not configured in .env")
    if not config.EMAIL_PASSWORD:
        raise RuntimeError("send_digest(): EMAIL_PASSWORD is not configured in .env")

    if not text_body:
        text_body = html_to_text(html_body)

    smtp_server = getattr(config, "SMTP_SERVER", "smtp.hackclub.app")
    smtp_port = int(getattr(config, "SMTP_PORT", 587))

    def _open_smtp():
        if smtp_port == 465:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=SMTP_TIMEOUT, context=context)
            server.login(from_addr, config.EMAIL_PASSWORD)
            return server
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=SMTP_TIMEOUT)
            server.ehlo()
            try:
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
            except smtplib.SMTPException:
                if config.DEBUG:
                    logger.debug("STARTTLS failed or unsupported; continuing without STARTTLS")
            server.login(from_addr, config.EMAIL_PASSWORD)
            return server

    server = None
    try:
        server = _open_smtp()

        if send_individually:
            sent_count = 0
            for r in rcpts:
                msg = _build_message(from_addr=from_addr, to_addr=r, subject=subject, html_body=html_body, text_body=text_body, reply_to=reply_to)
                try:
                    server.send_message(msg, to_addrs=[r])
                    sent_count += 1
                except Exception as exc:
                    logger.error("Failed sending to %s: %s", r, exc)
                if config.DEBUG:
                    logger.info("Sent %d individual messages", sent_count)
                return
        else:
            generic_to = from_addr
            msg = _build_message(from_addr=from_addr, to_addr=generic_to, subject=subject, html_body=html_body, text_body=text_body, reply_to=reply_to)
            try:
                server.send_message(msg, to_addrs=rcpts)
                if config.DEBUG:
                    logger.info("Sent one message with %d BCC recipients", len(rcpts))
            except Exception as exc:
                logger.error("Failed sending BCC message: %s", exc)
                raise
    finally:
        if server:
            try:
                server.quit()
            except Exception:
                pass
"""Shared branded layout for the platform's transactional email (GRX-USER-003).

Every platform-sent transactional message (verification, password reset, team
invitation) is one `EmailContent` rendered through `render()`, so the wrapper -- header
band, typography, call-to-action button, footer -- is defined once here rather than
re-inlined per message. Callers supply *plain text* only; this module owns all HTML.

Two constraints drive the markup, and both are why it does not look like ordinary web
markup:

* **Tables and inline styles.** Several major clients (Outlook's Word rendering engine,
  Gmail's web client) strip `<style>` blocks and ignore modern layout properties, so the
  structure is nested tables with `style="..."` on every element.
* **No external assets.** A remote logo would be blocked by default in most clients and
  render as a broken box, so the wordmark is live text, not an image.

Callers pass unescaped plain text and this module escapes it (`_p`, `_attr`). That
direction matters: `full_name` is user-controlled, and the previous per-message
f-strings interpolated it into HTML raw, so a display name containing markup could
inject arbitrary content into the mail body.
"""

from dataclasses import dataclass
from html import escape

BRAND_NAME = "Growixa"
BRAND_CAPTION = "BY IITDEVELOPER"

# Mirrors the web app's tokens in apps/web/src/app/globals.css. Duplicated as literals
# because email HTML cannot reference CSS custom properties -- keep the two in step.
_PAGE_BG = "#f4f6fb"
_CARD_BG = "#ffffff"
_HEADER_BG = "#0b1e3f"
_INK = "#0b1b33"
_SLATE = "#64748b"
_PRIMARY = "#1457e6"
_MINT = "#5eead4"
_BORDER = "#e2e8f0"

_FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"


@dataclass(frozen=True)
class EmailContent:
    """One transactional message, as plain text. `subject` travels with the body so a
    caller passes a single object to the sender instead of keeping the subject and the
    body in step by hand."""

    subject: str
    # Shown by most clients as the grey preview line next to the subject. Without one,
    # clients fall back to scraping the first text in the body -- which for a table
    # layout is whatever markup noise comes first.
    preheader: str
    heading: str
    paragraphs: tuple[str, ...]
    action_label: str | None = None
    action_url: str | None = None
    # Small print under the divider (expiry, "you can ignore this"), not the legal
    # footer -- that is the same on every message and lives in the template below.
    footer_note: str | None = None


@dataclass(frozen=True)
class RenderedEmail:
    subject: str
    html: str
    text: str


def _p(value: str) -> str:
    return escape(value, quote=False)


def _attr(value: str) -> str:
    return escape(value, quote=True)


def _paragraph_html(text: str) -> str:
    return (
        f'<p style="margin:0 0 16px;font-family:{_FONT};font-size:15px;'
        f'line-height:1.6;color:{_INK};">{_p(text)}</p>'
    )


def _button_html(label: str, url: str) -> str:
    """A "bulletproof" button: the clickable surface is a table cell with a `bgcolor`
    attribute, because Outlook drops `background` styles on an anchor and would
    otherwise render this as bare blue text with no button behind it."""
    return (
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
        'style="margin:8px 0 24px;"><tr>'
        f'<td bgcolor="{_PRIMARY}" style="border-radius:8px;">'
        f'<a href="{_attr(url)}" style="display:inline-block;padding:13px 28px;'
        f"font-family:{_FONT};font-size:15px;font-weight:600;color:#ffffff;"
        f'text-decoration:none;border-radius:8px;">{_p(label)}</a>'
        "</td></tr></table>"
    )


def _fallback_link_html(url: str) -> str:
    """Clients that suppress the button (and users who simply do not trust one) still
    need the destination visible. `word-break` matters: a token-bearing URL is long
    enough to force horizontal scrolling on mobile otherwise."""
    return (
        f'<p style="margin:0 0 8px;font-family:{_FONT};font-size:13px;'
        f'line-height:1.5;color:{_SLATE};">Or paste this link into your browser:</p>'
        f'<p style="margin:0 0 20px;font-family:{_FONT};font-size:13px;'
        f'line-height:1.5;word-break:break-all;">'
        f'<a href="{_attr(url)}" style="color:{_PRIMARY};">{_p(url)}</a></p>'
    )


def render(content: EmailContent) -> RenderedEmail:
    body_parts = [_paragraph_html(paragraph) for paragraph in content.paragraphs]

    if content.action_label and content.action_url:
        body_parts.append(_button_html(content.action_label, content.action_url))
        body_parts.append(_fallback_link_html(content.action_url))

    if content.footer_note:
        body_parts.append(
            f'<p style="margin:24px 0 0;padding-top:20px;border-top:1px solid {_BORDER};'
            f'font-family:{_FONT};font-size:13px;line-height:1.5;color:{_SLATE};">'
            f"{_p(content.footer_note)}</p>"
        )

    html = f"""\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_p(content.subject)}</title>
</head>
<body style="margin:0;padding:0;background-color:{_PAGE_BG};">
<div style="display:none;font-size:1px;color:{_PAGE_BG};max-height:0;overflow:hidden;">\
{_p(content.preheader)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" \
style="background-color:{_PAGE_BG};padding:32px 12px;">
<tr><td align="center">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" \
style="max-width:560px;background-color:{_CARD_BG};border-radius:14px;overflow:hidden;\
border:1px solid {_BORDER};">
<tr><td style="background-color:{_HEADER_BG};padding:24px 32px;">
<div style="font-family:{_FONT};font-size:19px;font-weight:700;color:#ffffff;\
letter-spacing:-0.01em;">{BRAND_NAME}</div>
<div style="font-family:{_FONT};font-size:10px;font-weight:600;color:{_MINT};\
letter-spacing:0.12em;margin-top:2px;">{BRAND_CAPTION}</div>
</td></tr>
<tr><td style="padding:32px;">
<h1 style="margin:0 0 16px;font-family:{_FONT};font-size:21px;font-weight:700;\
line-height:1.35;color:{_INK};">{_p(content.heading)}</h1>
{"".join(body_parts)}
</td></tr>
</table>
<p style="margin:20px 0 0;font-family:{_FONT};font-size:12px;line-height:1.5;\
color:{_SLATE};max-width:560px;">This is an automated message from {BRAND_NAME}. \
Please do not reply to it.</p>
</td></tr>
</table>
</body>
</html>"""

    text_parts = [content.heading, "", *_text_body(content)]
    text = "\n".join(text_parts).strip() + "\n"

    return RenderedEmail(subject=content.subject, html=html, text=text)


def _text_body(content: EmailContent) -> list[str]:
    parts: list[str] = []
    for paragraph in content.paragraphs:
        parts.extend((paragraph, ""))

    if content.action_label and content.action_url:
        parts.extend((f"{content.action_label}: {content.action_url}", ""))

    if content.footer_note:
        parts.extend((content.footer_note, ""))

    parts.extend(("--", f"This is an automated message from {BRAND_NAME}. Please do not reply."))
    return parts


__all__ = ["BRAND_CAPTION", "BRAND_NAME", "EmailContent", "RenderedEmail", "render"]

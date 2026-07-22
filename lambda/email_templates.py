"""
email_templates.py — campaign lifecycle emails for sterilizari-gratuite.ro
==========================================================================

Renders the (subject, html, text) triple for the organizer emails
('submitted' | 'approved' | 'rejected') and the citizen emails
('registered' | 'campaign_alert' | 'deleted').

Design notes (email is NOT a webpage):
  - Table-based layout, inline CSS only, web-safe fonts. The brand fonts
    (Funnel Display / Rethink Sans) are listed first but degrade to
    Trebuchet/Helvetica/Arial — email clients rarely load web fonts. No JS, no
    flexbox/grid (they break in Outlook/Gmail). border-radius degrades to square
    in old Outlook.
  - Palette mirrors the site's visual identity: navy primary (#041A49), orange
    accent (#F95905), light-grey page (#F2F1F0). See frontend app/assets/css/main.css.
  - A hidden preheader controls the inbox preview line.
  - EVERY dynamic value is HTML-escaped (org name, reason, address, locality)
    so user-supplied text can't break the markup or inject content.
  - Dependency-free: import this from the Lambda, or run it standalone to
    generate previews.

Wiring into the Lambda (see lambda_function.send_campaign_email):

    import email_templates
    subject, body_html, body_text = email_templates.render(
        kind, organization_name=..., campaign_public_id=..., organizer_public_id=...,
        site_url=..., details=..., reason=...,
    )
    _send_ses_email(to_email, subject, body_html=body_html, body_text=body_text)
"""

import html
from typing import Optional

# ── Brand / config (edit these) ──────────────────────────────────────────────
BRAND = "sterilizari-gratuite.ro"
SUPPORT_EMAIL = "contact@sterilizari-gratuite.ro"

# Email header logo. A PNG rendered from frontend/public/favicon.svg and served
# from the site root (frontend/public/email-logo.png → https://.../email-logo.png).
# Email clients don't reliably render SVG, so we reference a hosted PNG by
# absolute URL and always pair it with the text wordmark as the alt fallback.
LOGO_URL = f"https://{BRAND}/email-logo.png"

# Web-safe font stacks. Brand fonts first (loaded via @font-face below in clients
# that support web fonts — Apple/iOS Mail) → graceful fallback to system-safe
# families (Gmail/Outlook-Windows strip web fonts and use these).
BODY_FONT = "'Rethink Sans', Helvetica, Arial, sans-serif"
HEAD_FONT = "'Funnel Display', 'Trebuchet MS', Helvetica, Arial, sans-serif"

# Self-hosted brand fonts (woff2 in frontend/public/fonts/, served from our own
# domain — not Google). Variable 400–700; latin + latin-ext so Romanian
# diacritics (ă â î ș ț) render. Plain string (not an f-string) so the CSS braces
# don't need escaping where it's interpolated into the layout.
FONT_FACE_CSS = (
    "@font-face{font-family:'Funnel Display';font-style:normal;font-weight:400 700;font-display:swap;"
    f"src:url(https://{BRAND}/fonts/funnel-display-latin-ext.woff2) format('woff2');"
    "unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF;}"
    "@font-face{font-family:'Funnel Display';font-style:normal;font-weight:400 700;font-display:swap;"
    f"src:url(https://{BRAND}/fonts/funnel-display-latin.woff2) format('woff2');"
    "unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD;}"
    "@font-face{font-family:'Rethink Sans';font-style:normal;font-weight:400 700;font-display:swap;"
    f"src:url(https://{BRAND}/fonts/rethink-sans-latin-ext.woff2) format('woff2');"
    "unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF;}"
    "@font-face{font-family:'Rethink Sans';font-style:normal;font-weight:400 700;font-display:swap;"
    f"src:url(https://{BRAND}/fonts/rethink-sans-latin.woff2) format('woff2');"
    "unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD;}"
)

PALETTE = {
    "page_bg":   "#f2f1f0",   # --color-light-grey
    "card_bg":   "#ffffff",
    "ink":       "#0f172a",   # --color-text
    "muted":     "#475569",   # --color-text-muted
    "border":    "#e2e8f0",
    "brand":     "#041a49",   # --color-navy (primary; buttons, wordmark)
    "brand_ink": "#06256a",   # --color-primary-hover
    "accent":    "#f95905",   # --color-orange (links, accent rule)
    "accent_ink": "#c2440a",
}

# Per-kind: subject, intro line, and banner (label, text colour, background).
_KINDS = {
    "submitted": {
        "subject": "Campania ta a fost înregistrată",
        "intro": "Am primit campania ta și este în curs de verificare. "
                 "Te anunțăm pe email imediat ce a fost analizată.",
        "banner_label": "În verificare",
        "banner_fg": "#06256a",
        "banner_bg": "#e7ecf5",
    },
    "approved": {
        "subject": "Campania ta a fost aprobată",
        "intro": "Vești bune! Campania ta a fost aprobată și este acum publică pe "
                 "hartă. Cetățenii din zonă o pot vedea și se pot programa.",
        "banner_label": "Aprobată",
        "banner_fg": "#14622f",
        "banner_bg": "#e7f6ec",
    },
    "rejected": {
        "subject": "Campania ta nu a fost aprobată",
        "intro": "Din păcate, campania ta nu a fost aprobată în forma actuală. "
                 "Poți corecta detaliile și o poți retrimite oricând.",
        "banner_label": "Respinsă",
        "banner_fg": "#8f1f18",
        "banner_bg": "#fdecea",
    },
}


# ── Value formatting (duck-typed so dates/times/strings all work) ─────────────
def _esc(v) -> str:
    return html.escape("" if v is None else str(v))


def _date_str(v) -> str:
    if v is None:
        return ""
    return v.isoformat() if hasattr(v, "isoformat") else str(v)


def _clock_str(v) -> str:
    if v is None:
        return ""
    return v.strftime("%H:%M") if hasattr(v, "strftime") else str(v)[:5]


def _detail_fields(details: dict):
    """Return an ordered list of (label, value) pairs, skipping empties."""
    d = details or {}
    start_s = _date_str(d.get("date_start"))
    end_s = _date_str(d.get("date_end"))
    when = start_s
    if end_s and end_s != start_s:
        when += " – " + end_s
    ts, te = _clock_str(d.get("time_start")), _clock_str(d.get("time_end"))
    hours = f"{ts}–{te}" if ts and te else (ts or te)
    sp = d.get("species") or {}
    species = ", ".join(f"{k}: {v} locuri" for k, v in sp.items()) if sp else ""
    location = ", ".join(x for x in (d.get("locality"), d.get("county_name")) if x)
    pairs = [
        ("Locație", location),
        ("Adresă", d.get("address") or ""),
        ("Dată", when),
        ("Interval orar", hours),
        ("Locuri disponibile", species),
    ]
    return [(k, v) for k, v in pairs if v]


# ── HTML fragments ────────────────────────────────────────────────────────────
def _details_card_html(details: dict) -> str:
    fields = _detail_fields(details)
    if not fields:
        return ""
    rows = "".join(
        f"""
        <tr>
          <td style="padding:7px 0;font-size:13px;color:{PALETTE['muted']};
                     width:42%;vertical-align:top;">{_esc(label)}</td>
          <td style="padding:7px 0;font-size:14px;color:{PALETTE['ink']};
                     font-weight:600;vertical-align:top;">{_esc(value)}</td>
        </tr>"""
        for label, value in fields
    )
    return f"""
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
             style="margin:18px 0;border:1px solid {PALETTE['border']};
                    border-radius:10px;background:#fafbfc;">
        <tr><td style="padding:16px 20px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{rows}
          </table>
        </td></tr>
      </table>"""


def _details_text(details: dict) -> str:
    fields = _detail_fields(details)
    return "\n".join(f"{k}: {v}" for k, v in fields)


def _button_html(label: str, url: str) -> str:
    return f"""
      <table role="presentation" cellpadding="0" cellspacing="0" style="margin:8px 0 4px;">
        <tr><td style="border-radius:8px;background:{PALETTE['brand']};">
          <a href="{_esc(url)}" target="_blank"
             style="display:inline-block;padding:12px 26px;font-size:15px;font-weight:600;
                    color:#ffffff;text-decoration:none;border-radius:8px;
                    font-family:{BODY_FONT};">{_esc(label)}</a>
        </td></tr>
      </table>"""


def _layout(*, preheader: str, banner_label: str, banner_fg: str, banner_bg: str,
            inner_html: str) -> str:
    """Full HTML document with header / banner / body / footer."""
    return f"""<!DOCTYPE html>
<html lang="ro">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="x-apple-disable-message-reformatting">
  <title>{_esc(BRAND)}</title>
  <!-- Brand web fonts (progressive enhancement), self-hosted on our domain.
       Apple Mail / iOS Mail render these; Gmail / Outlook-Windows / Yahoo strip
       web fonts and use the web-safe fallback in each font-family stack. -->
  <style>{FONT_FACE_CSS}</style>
</head>
<body style="margin:0;padding:0;background:{PALETTE['page_bg']};
             font-family:{BODY_FONT};">
  <span style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent;">
    {_esc(preheader)}</span>

  <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
         style="background:{PALETTE['page_bg']};padding:28px 12px;">
    <tr><td align="center">

      <table role="presentation" width="600" cellpadding="0" cellspacing="0"
             style="width:600px;max-width:600px;background:{PALETTE['card_bg']};
                    border-radius:14px;overflow:hidden;
                    border:1px solid {PALETTE['border']};">

        <!-- Header / wordmark — favicon mark + navy wordmark, orange accent rule -->
        <tr><td style="padding:24px 32px 16px;border-bottom:3px solid {PALETTE['accent']};">
          <img src="{_esc(LOGO_URL)}" alt="{_esc(BRAND)}" width="34" height="34"
               style="vertical-align:middle;border:0;display:inline-block;margin-right:10px;">
          <span style="font-family:{HEAD_FONT};font-size:22px;
                       font-weight:700;color:{PALETTE['brand']};
                       letter-spacing:-0.3px;vertical-align:middle;">{_esc(BRAND)}</span>
        </td></tr>

        <!-- Status banner -->
        <tr><td style="padding:18px 32px 0;">
          <span style="display:inline-block;padding:6px 14px;border-radius:999px;
                       font-size:12px;font-weight:700;letter-spacing:0.4px;
                       text-transform:uppercase;color:{banner_fg};
                       background:{banner_bg};">{_esc(banner_label)}</span>
        </td></tr>

        <!-- Body -->
        <tr><td style="padding:14px 32px 28px;color:{PALETTE['ink']};
                       font-size:15px;line-height:1.6;">{inner_html}
        </td></tr>

        <!-- Footer -->
        <tr><td style="padding:18px 32px 26px;border-top:1px solid {PALETTE['border']};
                       background:#fafbfc;">
          <p style="margin:0 0 6px;font-size:12px;line-height:1.5;color:{PALETTE['muted']};">
            Primești acest email pentru că ai înregistrat o campanie pe
            {_esc(BRAND)}. Acesta este un mesaj tranzacțional legat de campania ta.</p>
          <p style="margin:0;font-size:12px;line-height:1.5;color:{PALETTE['muted']};">
            Întrebări? Scrie-ne la
            <a href="mailto:{_esc(SUPPORT_EMAIL)}"
               style="color:{PALETTE['accent']};text-decoration:none;">{_esc(SUPPORT_EMAIL)}</a>.
          </p>
        </td></tr>

      </table>

    </td></tr>
  </table>
</body>
</html>"""


# ── Public API ────────────────────────────────────────────────────────────────
def render(
    kind: str, *, organization_name: str, campaign_public_id: str,
    organizer_public_id: Optional[str] = None, site_url: str,
    details: Optional[dict] = None, reason: Optional[str] = None,
    manage_url: Optional[str] = None,
):
    """Return (subject, html, text) for the given kind. Unknown kind -> ValueError.
    `manage_url` (the campaign-management magic link) is rendered only for 'approved'."""
    if kind not in _KINDS:
        raise ValueError(f"unknown email kind: {kind}")
    cfg = _KINDS[kind]

    status_url = f"{site_url}/campanie/{campaign_public_id}"
    org_url = f"{site_url}/organizator/{organizer_public_id}" if organizer_public_id else None

    # Reason block (rejected only)
    reason_html = ""
    if kind == "rejected" and reason:
        reason_html = (
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            f'style="margin:4px 0 14px;border-left:3px solid {cfg["banner_fg"]};'
            f'background:{cfg["banner_bg"]};border-radius:0 8px 8px 0;">'
            f'<tr><td style="padding:12px 16px;font-size:14px;line-height:1.5;'
            f'color:{PALETTE["ink"]};"><strong>Motiv:</strong> {_esc(reason)}</td></tr></table>'
        )

    cta_label = "Vezi campania" if kind != "rejected" else "Retrimite / vezi detalii"
    org_link_html = (
        f'<p style="margin:16px 0 0;font-size:13px;color:{PALETTE["muted"]};">'
        f'Toate campaniile tale: <a href="{_esc(org_url)}" '
        f'style="color:{PALETTE["accent"]};text-decoration:none;">{_esc(org_url)}</a></p>'
        if org_url else ""
    )

    # Approved emails carry the per-campaign management link: the organizer can
    # stop registrations ("Sold Out") once all slots are booked.
    manage_html = ""
    if kind == "approved" and manage_url:
        manage_html = (
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            f'style="margin:18px 0 4px;border-top:1px solid {PALETTE["border"]};">'
            f'<tr><td style="padding-top:16px;">'
            f'<p style="margin:0 0 8px;font-size:14px;color:{PALETTE["ink"]};">'
            f'Când toate locurile sunt ocupate, poți opri înscrierile din pagina de '
            f'gestionare a campaniei. Telefonul public dispare și vizitatorii văd '
            f'„Locuri ocupate”.</p>'
            f'{_button_html("Gestionează campania", manage_url)}'
            f'</td></tr></table>'
        )

    inner_html = (
        f'<p style="margin:0 0 4px;font-size:17px;font-weight:700;">'
        f'Bună, {_esc(organization_name)},</p>'
        f'<p style="margin:0 0 8px;">{_esc(cfg["intro"])}</p>'
        f'{reason_html}'
        f'{_details_card_html(details or {})}'
        f'<p style="margin:14px 0 4px;font-size:13px;color:{PALETTE["muted"]};">'
        f'ID campanie</p>'
        f'<p style="margin:0 0 16px;font-size:14px;font-family:monospace;'
        f'color:{PALETTE["ink"]};">{_esc(campaign_public_id)}</p>'
        f'{_button_html(cta_label, status_url)}'
        f'{manage_html}'
        f'{org_link_html}'
        f'<p style="margin:22px 0 0;font-size:15px;">Mulțumim,<br>'
        f'<strong>Echipa {_esc(BRAND)}</strong></p>'
    )

    html_out = _layout(
        preheader=cfg["intro"],
        banner_label=cfg["banner_label"],
        banner_fg=cfg["banner_fg"],
        banner_bg=cfg["banner_bg"],
        inner_html=inner_html,
    )

    # Plain-text alternative
    parts = [f"Bună, {organization_name},", "", cfg["intro"], ""]
    if kind == "rejected" and reason:
        parts += [f"Motiv: {reason}", ""]
    det = _details_text(details or {})
    if det:
        parts += [det, ""]
    parts += [f"ID campanie: {campaign_public_id}",
              f"Vezi campania: {status_url}"]
    if kind == "approved" and manage_url:
        parts.append(f"Gestionează campania (oprește înscrierile): {manage_url}")
    if org_url:
        parts.append(f"Toate campaniile tale: {org_url}")
    parts += ["", f"Mulțumim,", f"Echipa {BRAND}"]
    text_out = "\n".join(parts)

    return cfg["subject"], html_out, text_out


# ── Citizen-facing emails: registered | campaign_alert | deleted ──────────────
_CITIZEN = {
    "registered": {
        "subject": "Te-ai înscris cu succes",
        "intro": "Te-ai înscris cu succes pe lista de așteptare. Te anunțăm pe "
                 "email imediat ce apare o campanie de sterilizare gratuită în zona ta.",
        "banner_label": "Înscris", "banner_fg": PALETTE["brand_ink"], "banner_bg": "#e7ecf5",
    },
    "campaign_alert": {
        "subject": "A apărut o campanie de sterilizare în zona ta",
        "intro": "Vești bune! A apărut o campanie de sterilizare gratuită în zona ta.",
        "banner_label": "Campanie nouă", "banner_fg": "#14622f", "banner_bg": "#e7f6ec",
    },
    "deleted": {
        "subject": "Datele tale au fost șterse",
        "intro": "Confirmăm că datele tale au fost șterse complet din sistemul nostru, "
                 "conform solicitării tale. Nu te vom mai contacta.",
        "banner_label": "Date șterse", "banner_fg": "#8f1f18", "banner_bg": "#fdecea",
    },
}


def render_citizen(
    kind: str, *, name: Optional[str] = None, locality: Optional[str] = None,
    organization_name: Optional[str] = None, details: Optional[dict] = None,
    campaign_url: Optional[str] = None, manage_url: Optional[str] = None,
):
    """Return (subject, html, text) for a citizen email:
    'registered' | 'campaign_alert' | 'deleted'."""
    if kind not in _CITIZEN:
        raise ValueError(f"unknown citizen email kind: {kind}")
    cfg = _CITIZEN[kind]
    greeting = f"Bună, {_esc(name)}," if name else "Bună,"

    extra_html, extra_text = "", []
    if kind == "registered":
        if locality:
            extra_html += (f'<p style="margin:0 0 8px;">Locație: '
                           f'<strong>{_esc(locality)}</strong></p>')
            extra_text.append(f"Locație: {locality}")
        if manage_url:
            extra_html += _button_html("Gestionează abonarea", manage_url)
            extra_text.append(f"Gestionează abonarea: {manage_url}")
    elif kind == "campaign_alert":
        if organization_name:
            extra_html += (f'<p style="margin:0 0 8px;">Organizator: '
                           f'<strong>{_esc(organization_name)}</strong></p>')
            extra_text.append(f"Organizator: {organization_name}")
        extra_html += _details_card_html(details or {})
        det_txt = _details_text(details or {})
        if det_txt:
            extra_text.append(det_txt)
        if campaign_url:
            extra_html += _button_html("Vezi campania", campaign_url)
            extra_text.append(f"Vezi campania: {campaign_url}")
        if manage_url:
            extra_html += (f'<p style="margin:14px 0 0;font-size:13px;color:{PALETTE["muted"]};">'
                           f'Nu mai vrei aceste notificări? '
                           f'<a href="{_esc(manage_url)}" '
                           f'style="color:{PALETTE["accent"]};text-decoration:none;">'
                           f'Dezabonează-te</a>.</p>')
            extra_text.append(f"Dezabonare: {manage_url}")
    # 'deleted' has no extra blocks or links.

    inner_html = (
        f'<p style="margin:0 0 4px;font-size:17px;font-weight:700;">{greeting}</p>'
        f'<p style="margin:0 0 8px;">{_esc(cfg["intro"])}</p>'
        f'{extra_html}'
        f'<p style="margin:22px 0 0;font-size:15px;">Mulțumim,<br>'
        f'<strong>Echipa {_esc(BRAND)}</strong></p>'
    )
    html_out = _layout(preheader=cfg["intro"], banner_label=cfg["banner_label"],
                       banner_fg=cfg["banner_fg"], banner_bg=cfg["banner_bg"],
                       inner_html=inner_html)

    text_out = "\n".join([greeting, "", cfg["intro"], "", *extra_text,
                          "", "Mulțumim,", f"Echipa {BRAND}"])
    return cfg["subject"], html_out, text_out


# ── Standalone preview generation ─────────────────────────────────────────────
if __name__ == "__main__":
    import datetime
    sample = dict(
        organization_name="Asociația Prietenii Animalelor",
        campaign_public_id="a3f1c2e4-5b6d-47a8-9c10-2e7f4b8d9a01",
        organizer_public_id="8d2b1f44-90ab-4c33-bb21-7e9c0a1d2f55",
        site_url="https://sterilizari-gratuite.ro",
        details={
            "county_name": "Suceava", "locality": "Bosanci",
            "address": "Str. Primăriei nr. 4",
            "date_start": datetime.date(2026, 6, 20),
            "date_end": datetime.date(2026, 6, 21),
            "time_start": "09:00", "time_end": "17:00",
            "species": {"dog": 20, "cat": 30},
        },
    )
    for k in ("submitted", "approved", "rejected"):
        kw = dict(sample)
        if k == "rejected":
            kw["reason"] = ("Numărul de telefon de contact nu a putut fi verificat. "
                            "Te rugăm să retrimiți campania cu un număr valid.")
        if k == "approved":
            kw["manage_url"] = "https://sterilizari-gratuite.ro/gestionare-campanie/TOKEN123"
        subj, html_doc, text_doc = render(k, **kw)
        with open(f"preview-{k}.html", "w", encoding="utf-8") as f:
            f.write(html_doc)
        print(f"[{k}] subject: {subj}  ({len(html_doc)} bytes html)")

    # Citizen-facing previews
    citizen_details = {
        "county_name": "Suceava", "locality": "Bosanci",
        "address": "Str. Primăriei nr. 4",
        "date_start": datetime.date(2026, 6, 20), "date_end": None,
        "time_start": "09:00", "time_end": "17:00",
        "species": {"dog": 20, "cat": 30},
    }
    citizen_cases = {
        "registered": dict(name="Maria Popescu", locality="Bosanci",
                           manage_url="https://sterilizari-gratuite.ro/cont/TOKEN123"),
        "campaign_alert": dict(name="Maria Popescu", locality="Bosanci",
                               organization_name="Asociația Prietenii Animalelor",
                               details=citizen_details,
                               campaign_url="https://sterilizari-gratuite.ro/campanie/UUID",
                               manage_url="https://sterilizari-gratuite.ro/cont/TOKEN123"),
        "deleted": dict(name="Maria Popescu"),
    }
    for k, kw in citizen_cases.items():
        subj, html_doc, text_doc = render_citizen(k, **kw)
        with open(f"preview-citizen-{k}.html", "w", encoding="utf-8") as f:
            f.write(html_doc)
        print(f"[citizen:{k}] subject: {subj}  ({len(html_doc)} bytes html)")

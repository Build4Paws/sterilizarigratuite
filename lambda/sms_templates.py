"""
sms_templates.py — short SMS bodies for citizen notifications (messengeros).

Design:
  - **ASCII only (no diacritics).** Diacritics force UCS-2 encoding (70 chars/
    segment vs 160 for GSM-7), doubling cost. Romanian SMS conventionally drops
    them. Email keeps full diacritics; SMS is plain.
  - Keep each body to ~1 segment where possible. The campaign alert includes a
    campaign URL and may spill into a 2nd segment — acceptable.
  - No per-recipient unsubscribe link in the (batched) alert: a single sms_body
    is shared across all recipients. Opt-out is via the manage page / provider
    STOP handling. Per-recipient links would require messengeros templates+params
    or one send per recipient.
"""

BRAND = "sterilizarigratuite.ro"


def render_citizen_sms(
    kind: str, *, locality=None, organization_name=None,
    campaign_url=None, manage_url=None,
) -> str:
    """Return the SMS body for a citizen notification kind. Unknown -> ValueError."""
    if kind == "registered":
        return (
            f"Te-ai inscris pe {BRAND}. Te anuntam cand apare o campanie de "
            "sterilizare gratuita in zona ta."
        )
    if kind == "campaign_alert":
        loc = f" in {locality}" if locality else ""
        url = f" Detalii: {campaign_url}" if campaign_url else ""
        return f"A aparut o campanie de sterilizare gratuita{loc}!{url}"
    raise ValueError(f"unknown sms kind: {kind}")

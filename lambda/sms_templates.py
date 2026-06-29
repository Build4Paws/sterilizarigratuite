"""
sms_templates.py — short SMS bodies for citizen notifications (messengeros).

Design:
  - **ASCII only (no diacritics).** Diacritics force UCS-2 encoding (70 chars/
    segment vs 160 for GSM-7), doubling cost. Romanian SMS conventionally drops
    them. Email keeps full diacritics; SMS is plain. Dynamic values that may
    carry diacritics (the locality name) are ASCII-folded here via `_ascii`.
  - Keep each body to 1 GSM-7 segment (<=160 chars). Worst case for the campaign
    alert — longest RO locality ("Statiunea Zoologica Marina Agigea", 33 chars),
    both species, longest phone — is ~148 chars, so it always fits one segment.
  - No per-recipient unsubscribe link in the (batched) alert: a single sms_body
    is shared across all recipients. Opt-out is via the provider STOP handling.
"""
import unicodedata
from datetime import date as _date, datetime as _datetime

# Romanian diacritics -> ASCII. Covers both the comma-below (ș/ț, U+0218/U+021A)
# and legacy cedilla (ş/ţ, U+015E/U+0162) encodings.
_RO_FOLD = str.maketrans({
    "ă": "a", "â": "a", "î": "i", "ș": "s", "ț": "t", "ş": "s", "ţ": "t",
    "Ă": "A", "Â": "A", "Î": "I", "Ș": "S", "Ț": "T", "Ş": "S", "Ţ": "T",
})


def _ascii(s) -> str:
    """Fold Romanian diacritics to ASCII; drop anything else non-ASCII so the SMS
    stays GSM-7 (1 segment). Preserves the original casing of the name."""
    if not s:
        return ""
    return (unicodedata.normalize("NFKD", str(s).translate(_RO_FOLD))
            .encode("ascii", "ignore").decode("ascii"))


def _species_ro(species) -> str:
    """Render the species set as Romanian SMS text: 'caini', 'pisici', or
    'caini si pisici'. `species` is an iterable of codes ('dog'/'cat')."""
    codes = set(species or ())
    parts = []
    if "dog" in codes:
        parts.append("caini")
    if "cat" in codes:
        parts.append("pisici")
    return " si ".join(parts)


def _fmt_date(d) -> str:
    """Format the campaign start date as dd.mm.yyyy. Accepts a date/datetime or
    an ISO 'YYYY-MM-DD' string."""
    if isinstance(d, (_date, _datetime)):
        return d.strftime("%d.%m.%Y")
    if isinstance(d, str) and len(d) >= 10:
        y, m, day = d[:10].split("-")
        return f"{day}.{m}.{y}"
    return str(d or "")


def render_citizen_sms(
    kind: str, *, locality=None, species=None, date_start=None, phone=None,
    organization_name=None, campaign_url=None, manage_url=None,
) -> str:
    """Return the SMS body for a citizen notification kind. Unknown -> ValueError.

    NOTE: there is intentionally NO 'registered' SMS — registration is
    email-only. A 'registered' kind raises ValueError, which `_render_sms`
    swallows, so no SMS is ever sent at registration even if a caller slips in."""
    if kind == "campaign_alert":
        return (
            f"Sterilizare gratuita {_species_ro(species)} in {_ascii(locality)}, "
            f"{_fmt_date(date_start)}. Suna la {phone or ''} pt programare. "
            "Locuri limitate."
        )
    raise ValueError(f"unknown sms kind: {kind}")

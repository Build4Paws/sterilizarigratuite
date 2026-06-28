"""Shared toolbox: DB, HTTP responses, security, tokens, geo, email, SMS."""
import base64
import concurrent.futures
import hashlib
import hmac
import json
import re
import secrets
import urllib.parse
import urllib.request
from datetime import date, datetime, time as _time, timedelta, timezone
from typing import Any, Optional
from uuid import UUID
from zoneinfo import ZoneInfo

import boto3
from botocore.config import Config as _BotoConfig
import psycopg
from psycopg.rows import dict_row

from .config import (
    log, PII_FIELDS, ENVIRONMENTS, current_env, current_origin,
    TURNSTILE_SECRET, TURNSTILE_ENABLED, TURNSTILE_VERIFY_URL, TOKEN_PEPPER,
    SES_SENDER, SES_REGION,
    MESSENGEROS_API_KEY, MESSENGEROS_DELIVERY_PROVIDER, MESSENGEROS_PROJECT, MESSENGEROS_SMS_URL,
    NOTIFY_TZ, NOTIFY_ALLOWED_START, NOTIFY_ALLOWED_END,
)

# Per-environment connections, keyed by env so a warm container can't serve a
# prod request on a devdb connection (or vice-versa).
_conns: "dict[str, psycopg.Connection]" = {}


def get_conn() -> psycopg.Connection:
    """Lazy-init connection for the active environment, recycle if dead."""
    env = current_env()
    conn = _conns.get(env)
    if conn is not None and not conn.closed:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            return conn
        except psycopg.OperationalError:
            log.warning("Stale %s connection, reconnecting", env)
    # autocommit=True so idle statements (the SELECT 1 health check above, and
    # every read-only GET handler) don't leave an implicit transaction open on
    # the reused warm connection. With a transaction left open, the next
    # `with conn.transaction()` degrades to a mere SAVEPOINT that releases
    # without committing the enclosing transaction — so writes silently never
    # persist. In autocommit mode each `with conn.transaction()` brackets a real
    # top-level transaction that COMMITs on exit (nested blocks stay savepoints).
    _conns[env] = psycopg.connect(
        ENVIRONMENTS[env]["dsn"], row_factory=dict_row, autocommit=True
    )
    return _conns[env]



def _json_default(o: Any) -> Any:
    """Strict serializer so the wire format matches the contract exactly:
    timestamps -> ISO-8601 UTC 'Z'; dates -> YYYY-MM-DD; times -> HH:MM."""
    if isinstance(o, datetime):
        if o.tzinfo is None:
            o = o.replace(tzinfo=timezone.utc)
        return o.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(o, _time):
        return o.strftime("%H:%M")
    if isinstance(o, date):
        return o.isoformat()
    if isinstance(o, UUID):
        return str(o)
    if isinstance(o, (bytes, bytearray)):
        return base64.b64encode(o).decode()
    return str(o)


def _cors_headers() -> dict:
    """CORS headers scoped to the active environment's allowed origin.
    PATCH + Authorization are allowed for the admin routes (harmless to public)."""
    return {
        "Access-Control-Allow-Origin": current_origin(),
        "Access-Control-Allow-Methods": "GET,POST,PATCH,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Max-Age": "600",
        "Vary": "Origin",
    }


def respond(status: int, body: Any = None) -> dict:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json", **_cors_headers()},
        "body": json.dumps(body, default=_json_default, ensure_ascii=False) if body is not None else "",
    }


def err(status: int, code: str, message: str = "", **extra) -> dict:
    payload = {"error": code}
    if message:
        payload["message"] = message
    payload.update(extra)
    return respond(status, payload)


def scrub_pii(d: dict) -> dict:
    """Return a copy safe to log — masks PII fields."""
    return {k: ("***" if k in PII_FIELDS else v) for k, v in d.items()}


PHONE_RE = re.compile(r"^\+?[0-9\s\-]{7,15}$")


def normalize_phone(p: str) -> str:
    """Keep digits only; '+40 712 345 678' → '40712345678'."""
    return re.sub(r"\D", "", p or "")


def verify_turnstile(token: str, remote_ip: Optional[str]) -> bool:
    """Server-side verification with Cloudflare Turnstile. Required for every
    public POST.

    Fail-closed AND hard time-boxed: the siteverify call runs in a worker thread
    capped at ~6s total. urllib's socket `timeout` doesn't reliably bound a
    DNS/connect stall when the Lambda has no internet egress (e.g. a VPC without
    a NAT gateway) — without this cap such a stall would burn the whole function
    timeout and surface as an opaque 503 instead of a clean captcha_failed."""
    if not TURNSTILE_ENABLED:
        log.warning("turnstile bypass active — DO NOT USE IN PROD")
        return True
    if not token:
        return False

    def _call() -> bool:
        data = urllib.parse.urlencode(
            {"secret": TURNSTILE_SECRET, "response": token, "remoteip": remote_ip or ""}
        ).encode()
        with urllib.request.urlopen(TURNSTILE_VERIFY_URL, data=data, timeout=5) as r:
            return bool(json.loads(r.read()).get("success"))

    # Don't use a `with` executor: its shutdown(wait=True) would block on a stuck
    # thread, defeating the cap. Submit, wait at most 6s, then abandon.
    ex = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        return ex.submit(_call).result(timeout=6)
    except concurrent.futures.TimeoutError:
        log.warning("Turnstile verify timed out — check Lambda egress to challenges.cloudflare.com")
        return False
    except Exception as e:
        log.warning("Turnstile verify failed: %s", type(e).__name__)
        return False
    finally:
        ex.shutdown(wait=False)


def hash_token(raw: str) -> bytes:
    """HMAC-SHA256 with server pepper. Pepper means a DB leak alone can't validate tokens."""
    return hmac.new(TOKEN_PEPPER, raw.encode(), hashlib.sha256).digest()


def new_token() -> tuple[str, bytes]:
    """Generate a fresh URL-safe token; return (plaintext, hash)."""
    raw = secrets.token_urlsafe(32)
    return raw, hash_token(raw)



_ses = None


def _ses_client():
    global _ses
    if _ses is None:
        # Short timeouts + no retries: if the Lambda is in a VPC without egress
        # to SES, send_email must FAIL FAST (caught below) rather than hang until
        # the Lambda's own timeout kills the whole request. Best-effort email
        # must never block the user-facing response.
        _ses = boto3.client(
            "ses", region_name=SES_REGION,
            config=_BotoConfig(connect_timeout=3, read_timeout=5,
                               retries={"max_attempts": 1}),
        )
    return _ses


def _send_ses_email(to_email: str, subject: str, body_text: str, body_html: str) -> None:
    """Low-level SES send. Best-effort: never raises; recipient never logged (PII)."""
    if not SES_SENDER:
        log.warning("SES_SENDER not configured; skipping email")
        return
    try:
        _ses_client().send_email(
            Source=SES_SENDER,
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Text": {"Data": body_text, "Charset": "UTF-8"},
                    "Html": {"Data": body_html, "Charset": "UTF-8"},
                },
            },
        )
        log.info("campaign email sent", extra={"subject": subject})
    except Exception as e:
        # Surface the SES error CODE (safe: not PII) so failures are diagnosable.
        # botocore ClientError carries it at response["Error"]["Code"].
        code = ""
        resp = getattr(e, "response", None)
        if isinstance(resp, dict):
            code = resp.get("Error", {}).get("Code", "")
        log.warning("SES send failed: %s%s", type(e).__name__, f" ({code})" if code else "")


def _as_date_str(v) -> str:
    if v is None:
        return ""
    return v.isoformat() if hasattr(v, "isoformat") else str(v)


def _as_clock_str(v) -> str:
    if v is None:
        return ""
    return v.strftime("%H:%M") if hasattr(v, "strftime") else str(v)[:5]


def _campaign_details_blocks(d: dict) -> tuple[str, str]:
    """Render a campaign-details dict into (text, html) blocks for the email.
    Keys (all optional): county_name, locality, address, date_start, date_end,
    time_start, time_end, species (dict species_code -> slots)."""
    when = _as_date_str(d.get("date_start"))
    if d.get("date_end"):
        when += " – " + _as_date_str(d.get("date_end"))
    ts, te = _as_clock_str(d.get("time_start")), _as_clock_str(d.get("time_end"))
    hours = f"{ts}–{te}" if ts and te else (ts or te)
    sp = d.get("species") or {}
    sp_txt = ", ".join(f"{k}: {v} locuri" for k, v in sp.items()) if sp else ""
    loc = ", ".join(x for x in (d.get("locality"), d.get("county_name")) if x)

    fields = [
        ("Locație", loc),
        ("Adresă", d.get("address") or ""),
        ("Dată", when),
        ("Interval orar", hours),
        ("Locuri", sp_txt),
    ]
    text = "\n".join(f"{k}: {v}" for k, v in fields if v)
    html_items = "".join(f"<li><strong>{k}:</strong> {v}</li>" for k, v in fields if v)
    return text, (f"<ul>{html_items}</ul>" if html_items else "")


_EMAIL_SUBJECTS = {
    "submitted": "Campania ta a fost înregistrată",
    "approved":  "Campania ta a fost aprobată",
    "rejected":  "Campania ta nu a fost aprobată",
}
_EMAIL_INTROS = {
    "submitted": "Am primit campania ta și este în curs de verificare.",
    "approved":  "Vești bune! Campania ta a fost aprobată și este acum publică.",
    "rejected":  "Din păcate, campania ta nu a fost aprobată.",
}


def send_campaign_email(
    kind: str, *, to_email: str, organization_name: str, campaign_public_id: str,
    organizer_public_id: Optional[str] = None, site_url: str,
    details: Optional[dict] = None, reason: Optional[str] = None,
) -> None:
    """Send the organizer a lifecycle email: 'submitted' | 'approved' | 'rejected'.
    Renders the STYLED templates from email_templates.py (must be bundled beside
    this file). Best-effort — never raises, never rolls back a transaction (call
    AFTER commit), never logs the recipient. `reason` is only used for 'rejected'."""
    try:
        import email_templates  # bundled in the deployment package
        subject, body_html, body_text = email_templates.render(
            kind,
            organization_name=organization_name,
            campaign_public_id=campaign_public_id,
            organizer_public_id=organizer_public_id,
            site_url=site_url,
            details=details,
            reason=reason,
        )
    except ValueError:
        log.warning("unknown campaign email kind: %s", kind)
        return
    except Exception:
        # Missing module / render bug must not break the request — email is
        # best-effort. (If you see this, email_templates.py isn't deployed.)
        log.exception("email render failed; not sending")
        return
    _send_ses_email(to_email, subject, body_text, body_html)


def fetch_campaign_email_payload(cur, campaign_internal_id: int) -> Optional[dict]:
    """Gather everything send_campaign_email needs for a campaign (organizer's
    contact email + name, public ids, and the displayable details). Call this
    inside the moderation transaction, BEFORE commit; send AFTER commit."""
    cur.execute(
        """
        SELECT o.contact_email, o.name AS organization_name, o.public_id AS organizer_public_id,
               c.public_id AS campaign_public_id, c.address, c.locality_id,
               c.date_start, c.date_end, c.time_start, c.time_end,
               co.name AS county_name, l.name AS locality,
               (SELECT jsonb_object_agg(cs.species_code, cs.slots)
                FROM campaign_species cs WHERE cs.campaign_id = c.id) AS species
        FROM campaigns c
        JOIN organizers o ON o.id = c.organizer_id
        JOIN counties   co ON co.code = c.county_code
        JOIN localities l  ON l.id = c.locality_id
        WHERE c.id = %s
        """,
        (campaign_internal_id,),
    )
    return cur.fetchone()


# Frontend page that consumes a citizen magic-link token. ADJUST to your actual
# Nuxt route (the API route is /m/{token}; this is the page that calls it).
CITIZEN_MANAGE_PATH = "/cont"


def _citizen_manage_url(token: str) -> str:
    return f"{current_origin()}{CITIZEN_MANAGE_PATH}/{token}"


def send_citizen_email(
    kind: str, *, to_email: Optional[str], name: Optional[str] = None,
    locality: Optional[str] = None, organization_name: Optional[str] = None,
    details: Optional[dict] = None, campaign_url: Optional[str] = None,
    manage_url: Optional[str] = None,
) -> None:
    """Best-effort citizen email ('registered'|'campaign_alert'|'deleted') via
    email_templates.render_citizen. No-ops if the citizen has no email. Never
    raises; never logs the recipient."""
    if not to_email:
        return
    try:
        import email_templates  # bundled in the deployment package
        subject, body_html, body_text = email_templates.render_citizen(
            kind, name=name, locality=locality, organization_name=organization_name,
            details=details, campaign_url=campaign_url, manage_url=manage_url,
        )
    except ValueError:
        log.warning("unknown citizen email kind: %s", kind)
        return
    except Exception:
        log.exception("citizen email render failed; not sending")
        return
    _send_ses_email(to_email, subject, body_text, body_html)


def _send_sms(recipients: list[dict], sms_body: str) -> None:
    """POST one batched SMS to messengeros for all `recipients`
    (each {"phone_number": "+40..."}). Best-effort; phone numbers never logged."""
    if not MESSENGEROS_API_KEY or not MESSENGEROS_DELIVERY_PROVIDER:
        log.warning("messengeros not configured; skipping SMS")
        return
    if not recipients:
        return

    sms_obj = {
        "delivery_provider": MESSENGEROS_DELIVERY_PROVIDER,
        "recipients": recipients,
        "sms_body": sms_body,
    }
    # `project` is a TOP-LEVEL field per the messengeros API (sibling of
    # `notification`), not part of the sms object.
    body = {"notification": {"sms": [sms_obj]}}
    if MESSENGEROS_PROJECT:
        body["project"] = MESSENGEROS_PROJECT
    payload = json.dumps(body).encode()

    def _call() -> int:
        req = urllib.request.Request(
            MESSENGEROS_SMS_URL, data=payload, method="POST",
            headers={"Content-Type": "application/json", "x-api-key": MESSENGEROS_API_KEY},
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status

    ex = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        status = ex.submit(_call).result(timeout=6)
        log.info("sms dispatched", extra={"recipients": len(recipients), "status": status})
    except concurrent.futures.TimeoutError:
        log.warning("messengeros send timed out — check Lambda egress to inbound.messengeros.com")
    except Exception as e:
        log.warning("messengeros send failed: %s", type(e).__name__)
    finally:
        ex.shutdown(wait=False)


def _render_sms(kind: str, **kw) -> Optional[str]:
    try:
        import sms_templates  # bundled in the deployment package
        return sms_templates.render_citizen_sms(kind, **kw)
    except ValueError:
        log.warning("unknown sms kind: %s", kind)
    except Exception:
        log.exception("sms render failed; not sending")
    return None


def send_citizen_sms(kind: str, *, to_phone: Optional[str], **kw) -> None:
    """Best-effort SMS to a single citizen. No-ops without a phone."""
    if not to_phone:
        return
    body = _render_sms(kind, **kw)
    if body:
        _send_sms([{"phone_number": to_phone}], body)


def send_citizens_sms_batch(kind: str, *, phones: list, **kw) -> None:
    """Best-effort SMS to many citizens in ONE messengeros call (one shared body
    — no per-recipient personalization). Used for the campaign-alert fan-out."""
    nums = [p for p in (phones or []) if p]
    if not nums:
        return
    body = _render_sms(kind, **kw)
    if body:
        _send_sms([{"phone_number": p} for p in nums], body)


def _parse_hhmm(s: str) -> _time:
    h, m = s.strip().split(":")
    return _time(int(h), int(m))


def within_send_window(now: Optional[datetime] = None) -> bool:
    """True if the current local time (NOTIFY_TZ) is inside the allowed
    quiet-hours window. Supports windows that wrap midnight (start > end, e.g.
    '22:00'..'06:00'). On bad/missing config it fails OPEN (returns True) so a
    misconfiguration never silently halts all notifications."""
    try:
        local = (now or datetime.now(timezone.utc)).astimezone(ZoneInfo(NOTIFY_TZ)).time()
        start, end = _parse_hhmm(NOTIFY_ALLOWED_START), _parse_hhmm(NOTIFY_ALLOWED_END)
    except Exception:
        log.exception("bad NOTIFY_* window config; allowing send")
        return True
    if start <= end:
        return start <= local <= end
    return local >= start or local <= end  # window wraps midnight


def audit(cur, *, actor: str, action: str, entity_type: str, entity_id: Optional[int],
          ip: Optional[str], ua: Optional[str], metadata: Optional[dict] = None):
    cur.execute(
        """
        INSERT INTO audit_log (actor, action, entity_type, entity_id, ip_address, user_agent, metadata)
        VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
        """,
        (actor, action, entity_type, entity_id, ip, ua, json.dumps(metadata or {})),
    )


def issue_token(cur, *, kind: str, citizen_id: Optional[int] = None,
                organizer_id: Optional[int] = None, ttl: timedelta) -> str:
    raw, hashed = new_token()
    expires_at = datetime.now(timezone.utc) + ttl
    cur.execute(
        """
        INSERT INTO tokens (token_hash, kind, citizen_id, organizer_id, expires_at)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (hashed, kind, citizen_id, organizer_id, expires_at),
    )
    return raw


def resolve_locality(cur, county_code: str, locality_name: str) -> Optional[int]:
    cur.execute(
        """
        SELECT id FROM localities
        WHERE county_code = %s AND LOWER(name) = LOWER(%s)
        LIMIT 1
        """,
        (county_code, locality_name),
    )
    r = cur.fetchone()
    return r["id"] if r else None



def client_ip(event: dict) -> Optional[str]:
    return event.get("requestContext", {}).get("http", {}).get("sourceIp")


def client_ua(event: dict) -> Optional[str]:
    return (event.get("headers") or {}).get("user-agent")



def _load_token(cur, raw_token: str, expected_kind: str) -> Optional[dict]:
    """Validate token: kind matches, not expired, not used, not revoked."""
    cur.execute(
        """
        SELECT id, kind, citizen_id, organizer_id, expires_at, used_at, revoked_at
        FROM tokens WHERE token_hash = %s
        """,
        (hash_token(raw_token),),
    )
    row = cur.fetchone()
    if not row:
        return None
    if row["kind"] != expected_kind:
        return None
    if row["used_at"] or row["revoked_at"]:
        return None
    if row["expires_at"] < datetime.now(timezone.utc):
        return None
    return row


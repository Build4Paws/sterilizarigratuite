"""
sterilizarigratuite — unified API Lambda (public + admin)
=========================================================

Routes (all under one API Gateway HTTP API):

  Public:
    POST   /register
    GET    /register/{id}
    POST   /campaigns/submit
    GET    /campaigns
    GET    /campaigns/{id}
    GET    /organizer/{id}
    GET    /stats/locality?county=&locality=
    GET    /stats/map
    GET    /counties
    GET    /counties/{code}/localities

  Magic-link (token in path):
    GET    /m/{token}
    POST   /m/{token}/unsubscribe
    POST   /m/{token}/erase
    POST   /r/{token}/confirm
    POST   /r/{token}/unsubscribe

  Admin (Cognito JWT authorizer at the gateway; `admins` group enforced here):
    GET    /admin/campaigns
    GET    /admin/campaigns/{id}
    POST   /admin/campaigns/{id}/approve
    POST   /admin/campaigns/{id}/reject
    PATCH  /admin/campaigns/{id}
    GET    /admin/citizens
    GET    /admin/citizens/{id}            (writes citizen.view audit — PII access)
    PATCH  /admin/citizens/{id}
    POST   /admin/citizens/{id}/unsubscribe
    POST   /admin/citizens/{id}/erase      (GDPR Art.17)
    GET    /admin/organizers
    GET    /admin/organizers/{id}
    PATCH  /admin/organizers/{id}
    GET    /admin/stats/overview
    GET    /admin/audit

Auth
  Public routes keep their existing gateway auth (AWS_IAM/SigV4). Admin routes
  sit behind a Cognito User Pool JWT authorizer. The authorizer validates the
  token (issuer + audience); this Lambda additionally enforces `admins` group
  membership and uses the `email` claim as campaigns.reviewed_by + audit actor.

Environment selection
  requestContext.domainName decides which environment to serve:
    api.sterilizarigratuite.ro      -> prod
    dev.api.sterilizarigratuite.ro  -> dev
  Each environment has its own database and its own allowed CORS origin.
  Unknown hosts are rejected (fail closed) — never defaulted to prod. Admin
  requests inherit this automatically: admin on the dev domain hits devdb.

Captcha
  Cloudflare Turnstile, verified server-side here (verify_turnstile). The
  frontend renders the widget and forwards the token (`turnstileToken`); the
  secret never leaves this Lambda. Legacy HCAPTCHA_* env vars are honored as a
  fallback so a code deploy can precede the env rename.

Environment variables (all required unless noted):
  Per-environment DB (PREFIX is PROD or DEV):
    {PREFIX}_PG_HOST, {PREFIX}_PG_PORT (opt, default 5432),
    {PREFIX}_PG_DB, {PREFIX}_PG_USER, {PREFIX}_PG_PASSWORD
  Per-environment CORS:
    PROD_ALLOWED_ORIGIN, DEV_ALLOWED_ORIGIN
  Shared:
    TURNSTILE_SECRET (legacy: HCAPTCHA_SECRET), TURNSTILE_ENABLED (opt, "true";
    legacy: HCAPTCHA_ENABLED), TOKEN_PEPPER,
    RATE_LIMIT_PER_IP_PER_HOUR (opt, 20), SES_SENDER (opt), SES_REGION (opt)

  Security: back all DB passwords and TURNSTILE_SECRET with Secrets Manager /
  SSM references, never literal values. Keep dev and prod datasets separate.
"""

import base64
import concurrent.futures
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import urllib.parse
import urllib.request
from datetime import date, datetime, time as _time, timedelta, timezone
from typing import Annotated, Any, Literal, Optional
from uuid import UUID

import boto3  # bundled in the Lambda Python runtime; no layer needed
from botocore.config import Config as _BotoConfig
import psycopg
from psycopg.rows import dict_row
from pydantic import BaseModel, EmailStr, Field, ValidationError, field_validator, model_validator

# ─────────────────────────────────────────────────────────────────────────────
# Config & logging
# ─────────────────────────────────────────────────────────────────────────────

log = logging.getLogger()
log.setLevel(logging.INFO)

# Captcha = Cloudflare Turnstile (server-side verification). The legacy
# HCAPTCHA_* names are still read as a fallback so the code can be deployed
# before the function's env vars are renamed.
TURNSTILE_SECRET = os.environ.get("TURNSTILE_SECRET") or os.environ.get("HCAPTCHA_SECRET")
if not TURNSTILE_SECRET:
    raise RuntimeError("TURNSTILE_SECRET (or legacy HCAPTCHA_SECRET) env var is required")
TURNSTILE_ENABLED = (
    os.environ.get("TURNSTILE_ENABLED")
    or os.environ.get("HCAPTCHA_ENABLED", "true")
).lower() == "true"
TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

TOKEN_PEPPER = os.environ["TOKEN_PEPPER"].encode()

# Email (SES). SES_SENDER must be a verified identity; if unset, email is skipped.
SES_SENDER = os.environ.get("SES_SENDER")
SES_REGION = os.environ.get("SES_REGION") or os.environ.get("AWS_REGION", "eu-central-1")

PII_FIELDS = {"phone", "email", "name", "contactEmail", "contactPhone", "phonePublic", "address"}

# Admin enums / limits
CAMPAIGN_STATUSES = {"pending", "approved", "rejected", "cancelled", "finished"}
CITIZEN_STATUSES = {"pending_confirm", "active", "unsubscribed", "deleted"}
COUNTY_RE = re.compile(r"^[A-Z]{1,2}$")
DEFAULT_LIMIT = 50
MAX_LIMIT = 200


# ─────────────────────────────────────────────────────────────────────────────
# Per-environment config
# ─────────────────────────────────────────────────────────────────────────────
# Nothing about an environment is hardcoded — every value comes from a Lambda
# env var.
# SECURITY/GDPR follow-up: sslmode=prefer encrypts only if the server offers
# TLS, otherwise falls back to plaintext. For citizen PII, enable TLS on the
# Postgres server and switch this to "require" (ideally "verify-full" with the
# server CA) so DB traffic is always encrypted in transit.
def _build_dsn(prefix: str) -> str:
    return (
        f"host={os.environ[f'{prefix}_PG_HOST']} "
        f"port={os.environ.get(f'{prefix}_PG_PORT', '5432')} "
        f"dbname={os.environ[f'{prefix}_PG_DB']} "
        f"user={os.environ[f'{prefix}_PG_USER']} "
        f"password={os.environ[f'{prefix}_PG_PASSWORD']} "
        f"sslmode=prefer "
        f"connect_timeout=5 "
        f"application_name=sterilizari-{prefix.lower()}"
    )


ENVIRONMENTS: dict[str, dict] = {
    "prod": {"dsn": _build_dsn("PROD"), "origin": os.environ["PROD_ALLOWED_ORIGIN"]},
    "dev":  {"dsn": _build_dsn("DEV"),  "origin": os.environ["DEV_ALLOWED_ORIGIN"]},
}

# Incoming custom domain → environment key.
DOMAIN_TO_ENV: dict[str, str] = {
    "api.sterilizarigratuite.ro":     "prod",
    "dev.api.sterilizarigratuite.ro": "dev",
    # Add the raw execute-api host here (mapped to "dev") if you want to test
    # via the d-xxxx.execute-api.* URL, which otherwise fails closed with 403.
}

# Request-scoped: set once per invocation in lambda_handler. Safe as a module
# global because a Lambda execution environment processes one event at a time.
_active_env: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Connection (per-environment, module-level for container reuse)
# ─────────────────────────────────────────────────────────────────────────────
# Keyed by environment so a warm container that already holds a devdb
# connection can NEVER serve a prod request against devdb (or vice versa).

_conns: dict[str, psycopg.Connection] = {}


def get_conn() -> psycopg.Connection:
    """Lazy-init connection for the active environment, recycle if dead."""
    env = _active_env
    conn = _conns.get(env)
    if conn is not None and not conn.closed:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            return conn
        except psycopg.OperationalError:
            log.warning("Stale %s connection, reconnecting", env)
    _conns[env] = psycopg.connect(
        ENVIRONMENTS[env]["dsn"], row_factory=dict_row, autocommit=False
    )
    return _conns[env]


# ─────────────────────────────────────────────────────────────────────────────
# Response helpers
# ─────────────────────────────────────────────────────────────────────────────

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
        "Access-Control-Allow-Origin": ENVIRONMENTS[_active_env]["origin"],
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


# ─────────────────────────────────────────────────────────────────────────────
# Validation utilities
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
# Email (SES)
# ─────────────────────────────────────────────────────────────────────────────
# The organizer's email is PII: it is used only to deliver the confirmation and
# is never logged. Sending is best-effort — a failure here must NOT fail or roll
# back the submission, so this is always called AFTER the DB transaction commits.

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
    return f"{ENVIRONMENTS[_active_env]['origin']}{CITIZEN_MANAGE_PATH}/{token}"


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


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic models
# ─────────────────────────────────────────────────────────────────────────────

Species = Literal["dog", "cat"]


class CitizenRegistration(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=200)]
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    county: Annotated[str, Field(pattern=r"^[A-Z]{1,2}$")]
    locality: Annotated[str, Field(min_length=1, max_length=200)]
    species: Annotated[list[Species], Field(min_length=1)]
    dog_count: Optional[int] = Field(default=None, ge=0, le=50, alias="dogCount")
    cat_count: Optional[int] = Field(default=None, ge=0, le=50, alias="catCount")
    gdpr_consent: Literal[True] = Field(alias="gdprConsent")
    turnstile_token: Annotated[str, Field(min_length=1, alias="turnstileToken")]

    model_config = {"populate_by_name": True, "str_strip_whitespace": True}

    @field_validator("phone")
    @classmethod
    def _valid_phone(cls, v):
        if v and not PHONE_RE.match(v):
            raise ValueError("invalid phone format")
        return v

    @model_validator(mode="after")
    def _phone_or_email(self):
        if not self.phone and not self.email:
            raise ValueError("phone or email required")
        return self


class CampaignSubmission(BaseModel):
    organization_name: Annotated[str, Field(min_length=1, max_length=200, alias="organizationName")]
    contact_email: EmailStr = Field(alias="contactEmail")
    contact_phone: Annotated[str, Field(min_length=7, max_length=20, alias="contactPhone")]
    phone_public: Annotated[str, Field(min_length=7, max_length=20, alias="phonePublic")]
    county: Annotated[str, Field(pattern=r"^[A-Z]{1,2}$")]
    locality: Annotated[str, Field(min_length=1, max_length=200)]
    address: Annotated[str, Field(min_length=1, max_length=500)]
    date_start: date = Field(alias="dateStart")
    date_end: Optional[date] = Field(default=None, alias="dateEnd")
    time_start: str = Field(alias="timeStart", pattern=r"^\d{2}:\d{2}$")
    time_end: str = Field(alias="timeEnd", pattern=r"^\d{2}:\d{2}$")
    species: Annotated[list[Species], Field(min_length=1)]
    slots_dogs: Optional[int] = Field(default=None, ge=1, le=10000, alias="slotsDogs")
    slots_cats: Optional[int] = Field(default=None, ge=1, le=10000, alias="slotsCats")
    doctor: Optional[Annotated[str, Field(max_length=200)]] = None
    gdpr_consent: Literal[True] = Field(alias="gdprConsent")
    turnstile_token: Annotated[str, Field(min_length=1, alias="turnstileToken")]

    model_config = {"populate_by_name": True, "str_strip_whitespace": True}

    @field_validator("contact_phone", "phone_public")
    @classmethod
    def _valid_phone(cls, v):
        if not PHONE_RE.match(v):
            raise ValueError("invalid phone format")
        return v

    @model_validator(mode="after")
    def _coherent(self):
        if self.date_start < date.today():
            raise ValueError("dateStart must be today or in the future")
        if self.date_end and self.date_end < self.date_start:
            raise ValueError("dateEnd must be >= dateStart")
        if self.date_end is None and self.time_end <= self.time_start:
            raise ValueError("timeEnd must be after timeStart")
        if "dog" in self.species and not self.slots_dogs:
            raise ValueError("slotsDogs required when species includes dog")
        if "cat" in self.species and not self.slots_cats:
            raise ValueError("slotsCats required when species includes cat")
        return self


def pydantic_errors_to_response(e: ValidationError) -> dict:
    """Map Pydantic errors to the docs' validation_failed shape."""
    errors = [
        {"field": ".".join(str(x) for x in err["loc"]), "message": err["msg"]}
        for err in e.errors()
    ]
    return err(400, "validation_failed", errors=errors)


# ─────────────────────────────────────────────────────────────────────────────
# Audit + token issuance helpers
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
# Locality / county resolution
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
# Request context helpers
# ─────────────────────────────────────────────────────────────────────────────

def client_ip(event: dict) -> Optional[str]:
    return event.get("requestContext", {}).get("http", {}).get("sourceIp")


def client_ua(event: dict) -> Optional[str]:
    return (event.get("headers") or {}).get("user-agent")


# ═════════════════════════════════════════════════════════════════════════════
# PUBLIC HANDLERS
# ═════════════════════════════════════════════════════════════════════════════

def handle_stats_map(event: dict) -> dict:
    """
    Combined country-wide stats for the /harta map page.

    Returns both cerere (registrations) and oferta (campaigns) per county.
    Filterable via ?view=cerere or ?view=oferta.

    Cache: 60s public, 300s shared.
    """
    qs = event.get("queryStringParameters") or {}
    view = (qs.get("view") or "").lower()
    if view and view not in ("cerere", "oferta"):
        return err(400, "validation_failed",
                   errors=[{"field": "view", "message": "must be 'cerere' or 'oferta'"}])

    include_cerere = view in ("", "cerere")
    include_oferta = view in ("", "oferta")

    conn = get_conn()
    by_county: dict[str, dict] = {}
    totals: dict[str, int] = {}

    with conn.cursor() as cur:

        # ── Cerere: aggregate citizen registrations by county ──────────────
        if include_cerere:
            cur.execute("""
                WITH per_locality AS (
                    SELECT c.county_code, l.name AS locality_name, COUNT(*) AS cnt
                    FROM citizens c
                    JOIN localities l ON l.id = c.locality_id
                    WHERE c.status = 'active'
                    GROUP BY c.county_code, l.name
                ),
                per_county AS (
                    SELECT
                        county_code,
                        SUM(cnt)::int AS total,
                        jsonb_object_agg(locality_name, cnt) AS localities
                    FROM per_locality
                    GROUP BY county_code
                ),
                per_species AS (
                    SELECT
                        ci.county_code,
                        cs.species_code,
                        COUNT(DISTINCT ci.id) AS cnt
                    FROM citizens ci
                    JOIN citizen_species cs ON cs.citizen_id = ci.id
                    WHERE ci.status = 'active'
                      AND cs.species_code IN ('dog', 'cat')
                    GROUP BY ci.county_code, cs.species_code
                ),
                species_by_county AS (
                    SELECT county_code, jsonb_object_agg(species_code, cnt) AS species
                    FROM per_species
                    GROUP BY county_code
                )
                SELECT
                    pc.county_code,
                    pc.total,
                    pc.localities,
                    COALESCE(sbc.species, '{}'::jsonb) AS species
                FROM per_county pc
                LEFT JOIN species_by_county sbc USING (county_code)
            """)
            for r in cur.fetchall():
                code = r["county_code"]
                by_county.setdefault(code, {})["cerere"] = {
                    "total": int(r["total"]),
                    "localities": {k: int(v) for k, v in (r["localities"] or {}).items()},
                    "species": {
                        "dog": int((r["species"] or {}).get("dog", 0)),
                        "cat": int((r["species"] or {}).get("cat", 0)),
                    }
                }

            cur.execute(
                "SELECT COUNT(*) AS n FROM citizens WHERE status = 'active'"
            )
            totals["registrations"] = int(cur.fetchone()["n"])

        # ── Oferta: approved + upcoming campaigns by county ────────────────
        if include_oferta:
            cur.execute("""
                SELECT
                    c.county_code,
                    c.public_id,
                    o.name        AS organization_name,
                    l.name        AS locality_name,
                    c.date_start,
                    c.date_end,
                    c.time_start,
                    c.time_end,
                    (
                        SELECT jsonb_object_agg(cs.species_code, cs.slots)
                        FROM campaign_species cs
                        WHERE cs.campaign_id = c.id
                    ) AS species
                FROM campaigns c
                JOIN organizers  o ON o.id = c.organizer_id
                JOIN localities  l ON l.id = c.locality_id
                WHERE c.status = 'approved'
                  AND (
                       (c.date_end IS NOT NULL AND c.date_end   >= CURRENT_DATE)
                    OR (c.date_end IS NULL     AND c.date_start >= CURRENT_DATE)
                  )
                ORDER BY c.county_code, c.date_start, l.name
            """)
            rows = cur.fetchall()

            # Group campaigns by county
            for r in rows:
                code = r["county_code"]
                county_bucket = by_county.setdefault(code, {})
                oferta = county_bucket.setdefault("oferta", {"total": 0, "campaigns": []})
                oferta["total"] += 1
                oferta["campaigns"].append({
                    "submissionId": str(r["public_id"]),
                    "organizationName": r["organization_name"],
                    "locality": r["locality_name"],
                    "dateStart": r["date_start"].isoformat() if r["date_start"] else None,
                    "dateEnd": r["date_end"].isoformat() if r["date_end"] else None,
                    "timeStart": str(r["time_start"]) if r["time_start"] else None,
                    "timeEnd": str(r["time_end"]) if r["time_end"] else None,
                    "species": r["species"] or {},
                })

            totals["campaigns"] = len(rows)

    resp = respond(200, {
        "byCounty": by_county,
        "totals": totals,
    })
    resp["headers"]["Cache-Control"] = "public, max-age=60, s-maxage=300"
    return resp


def handle_register(event: dict) -> dict:
    ip = client_ip(event)
    ua = client_ua(event)
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return err(400, "invalid_json")
    try:
        reg = CitizenRegistration.model_validate(body)
    except ValidationError as e:
        return pydantic_errors_to_response(e)

    if not verify_turnstile(reg.turnstile_token, ip):
        return err(400, "captcha_failed", "Verificarea captcha a eșuat.")

    phone_n = normalize_phone(reg.phone) if reg.phone else None

    conn = get_conn()
    try:
        with conn.transaction(), conn.cursor() as cur:
            locality_id = resolve_locality(cur, reg.county, reg.locality)
            if not locality_id:
                return err(400, "validation_failed",
                           errors=[{"field": "locality", "message": "unknown locality"}])

            # Dedupe — relies on partial unique indexes; race-safe via INSERT.
            # PII (name/phone/email) is stored only with explicit GDPR consent,
            # captured alongside consent IP/UA below for audit lawfulness.
            # The INSERT runs inside a SAVEPOINT (nested transaction) so a
            # UniqueViolation rolls back only this statement and leaves the outer
            # transaction usable — psycopg3 forbids an explicit conn.rollback()
            # inside a `with conn.transaction()` block.
            try:
                with conn.transaction():
                    cur.execute(
                        """
                        INSERT INTO citizens
                            (name, phone, phone_normalized, email, county_code, locality_id,
                             gdpr_consent, gdpr_consent_at, gdpr_consent_ip, gdpr_consent_ua, status)
                        VALUES (%s, %s, %s, %s, %s, %s, TRUE, now(), %s, %s, 'active')
                        RETURNING id, public_id
                        """,
                        (reg.name, reg.phone, phone_n, reg.email, reg.county,
                         locality_id, ip, ua),
                    )
                    row = cur.fetchone()
            except psycopg.errors.UniqueViolation:
                return err(409, "duplicate_registration",
                           "Ești deja înscris pentru această locație.")

            citizen_id = row["id"]

            for sp in reg.species:
                count = reg.dog_count if sp == "dog" else reg.cat_count
                cur.execute(
                    "INSERT INTO citizen_species (citizen_id, species_code, animal_count) "
                    "VALUES (%s, %s, %s)",
                    (citizen_id, sp, count),
                )

            manage_token = issue_token(
                cur, kind="citizen_manage", citizen_id=citizen_id, ttl=timedelta(days=365)
            )

            # Locality stats for the confirmation page
            cur.execute(
                """
                SELECT
                    COUNT(*) FILTER (WHERE locality_id = %s)        AS in_locality,
                    COUNT(*) FILTER (WHERE county_code = %s)        AS in_county
                FROM citizens
                WHERE status = 'active'
                """,
                (locality_id, reg.county),
            )
            stats = cur.fetchone()

            audit(cur, actor="self", action="citizen.register",
                  entity_type="citizen", entity_id=citizen_id,
                  ip=ip, ua=ua,
                  metadata={"county": reg.county, "locality": reg.locality})

        log.info("citizen registered", extra={"public_id": str(row["public_id"])})

        # Confirmation email (best-effort; only if the citizen gave an email).
        send_citizen_email(
            "registered",
            to_email=reg.email,
            name=reg.name,
            locality=reg.locality,
            manage_url=_citizen_manage_url(manage_token),
        )

        return respond(200, {
            "message": "Ești înscris, te anunțăm când apare o campanie.",
            "citizenId": str(row["public_id"]),
            "manageToken": manage_token,  # frontend stores this; emails it later via SES
            "stats": {
                "registeredInLocality": int(stats["in_locality"]),
                "registeredInCounty": int(stats["in_county"]),
            },
        })
    except Exception as e:
        log.exception("register failed: %s", type(e).__name__)
        return err(500, "internal_error")


def handle_campaign_submit(event: dict) -> dict:
    ip = client_ip(event)
    ua = client_ua(event)
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return err(400, "invalid_json")
    try:
        sub = CampaignSubmission.model_validate(body)
    except ValidationError as e:
        return pydantic_errors_to_response(e)

    if not verify_turnstile(sub.turnstile_token, ip):
        return err(400, "captcha_failed")

    contact_phone_n = normalize_phone(sub.contact_phone)

    conn = get_conn()
    try:
        with conn.transaction(), conn.cursor() as cur:
            locality_id = resolve_locality(cur, sub.county, sub.locality)
            if not locality_id:
                return err(400, "validation_failed",
                           errors=[{"field": "locality", "message": "unknown locality"}])

            # Upsert organizer by contact_email. Organizer PII (contact email/
            # phone) is processing-necessary to administer the campaign listing.
            cur.execute(
                """
                INSERT INTO organizers
                    (name, contact_email, contact_phone, contact_phone_normalized)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (contact_email) DO UPDATE
                    SET name = EXCLUDED.name,
                        contact_phone = EXCLUDED.contact_phone,
                        contact_phone_normalized = EXCLUDED.contact_phone_normalized,
                        updated_at = now()
                RETURNING id, public_id
                """,
                (sub.organization_name, sub.contact_email, sub.contact_phone, contact_phone_n),
            )
            organizer_row = cur.fetchone()
            organizer_id = organizer_row["id"]
            organizer_public_id = str(organizer_row["public_id"])

            # Insert campaign (partial unique index enforces dedupe). Runs inside
            # a SAVEPOINT so a UniqueViolation rolls back only this INSERT and the
            # outer transaction stays usable — psycopg3 forbids conn.rollback()
            # inside a `with conn.transaction()` block.
            try:
                with conn.transaction():
                    cur.execute(
                        """
                        INSERT INTO campaigns
                            (organizer_id, phone_public, county_code, locality_id, address,
                             date_start, date_end, time_start, time_end, doctor,
                             status, gdpr_consent, submitted_ip, submitted_ua)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                'pending', TRUE, %s, %s)
                        RETURNING id, public_id
                        """,
                        (organizer_id, sub.phone_public, sub.county, locality_id, sub.address,
                         sub.date_start, sub.date_end, sub.time_start, sub.time_end, sub.doctor,
                         ip, ua),
                    )
                    row = cur.fetchone()
            except psycopg.errors.UniqueViolation:
                # Savepoint rolled back; the outer transaction is still open, so we
                # can look up the existing campaign on the same cursor.
                cur.execute(
                    """
                    SELECT public_id FROM campaigns
                    WHERE locality_id = %s AND date_start = %s
                      AND organizer_id = %s
                      AND status IN ('pending', 'approved')
                    """,
                    (locality_id, sub.date_start, organizer_id),
                )
                existing = cur.fetchone()
                return err(409, "duplicate_submission",
                           "O campanie identică există deja pentru această locație și dată.",
                           existingSubmissionId=str(existing["public_id"]) if existing else None)

            campaign_id = row["id"]

            for sp in sub.species:
                slots = sub.slots_dogs if sp == "dog" else sub.slots_cats
                cur.execute(
                    "INSERT INTO campaign_species (campaign_id, species_code, slots) "
                    "VALUES (%s, %s, %s)",
                    (campaign_id, sp, slots),
                )

            cur.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM citizens
                     WHERE locality_id = %s AND status = 'active') AS in_locality,
                    (SELECT COUNT(*) FROM citizens
                     WHERE county_code = %s AND status = 'active') AS in_county
                """,
                (locality_id, sub.county),
            )
            stats = cur.fetchone()

            audit(cur, actor="self", action="campaign.submit",
                  entity_type="campaign", entity_id=campaign_id,
                  ip=ip, ua=ua,
                  metadata={"organizer_id": organizer_id, "county": sub.county})

            campaign_public_id = str(row["public_id"])

        # Transaction has committed here. Send confirmation best-effort: an email
        # failure must not undo the saved submission, so it lives outside the
        # transaction and send_campaign_email never raises.
        send_campaign_email(
            "submitted",
            to_email=sub.contact_email,
            organization_name=sub.organization_name,
            campaign_public_id=campaign_public_id,
            organizer_public_id=organizer_public_id,
            site_url=ENVIRONMENTS[_active_env]["origin"],
            details={
                "county_name": sub.county,  # county code; submit has no county name on hand
                "locality": sub.locality,
                "address": sub.address,
                "date_start": sub.date_start,
                "date_end": sub.date_end,
                "time_start": sub.time_start,
                "time_end": sub.time_end,
                "species": {sp: (sub.slots_dogs if sp == "dog" else sub.slots_cats)
                            for sp in sub.species},
            },
        )

        return respond(200, {
            "message": "Campaign submitted for review",
            "submissionId": campaign_public_id,
            "status": "pending",
            "stats": {
                "registeredInLocality": int(stats["in_locality"]),
                "registeredInCounty": int(stats["in_county"]),
            },
        })
    except Exception as e:
        log.exception("campaign submit failed: %s", type(e).__name__)
        return err(500, "internal_error")


def handle_list_campaigns(event: dict) -> dict:
    qs = event.get("queryStringParameters") or {}
    county = qs.get("county")
    if county and not re.match(r"^[A-Z]{1,2}$", county):
        return err(400, "validation_failed",
                   errors=[{"field": "county", "message": "invalid county code"}])

    conn = get_conn()
    with conn.cursor() as cur:
        if county:
            cur.execute(
                "SELECT * FROM v_public_campaigns WHERE county_code = %s ORDER BY date_start",
                (county,),
            )
        else:
            cur.execute("SELECT * FROM v_public_campaigns ORDER BY date_start")
        rows = cur.fetchall()

    resp = respond(200, {"campaigns": rows})
    resp["headers"]["Cache-Control"] = "public, max-age=60, s-maxage=300"
    return resp


def handle_get_campaign(event: dict, public_id: str) -> dict:
    try:
        UUID(public_id)
    except ValueError:
        return err(400, "invalid_id")

    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                c.public_id AS "submissionId",
                c.status AS "campaignStatus",
                o.name AS "organizationName",
                c.phone_public AS "phonePublic",
                c.county_code AS county,
                l.name AS locality,
                c.address, c.date_start AS "dateStart", c.date_end AS "dateEnd",
                c.time_start AS "timeStart", c.time_end AS "timeEnd",
                c.doctor, c.status, c.created_at AS "createdAt",
                (SELECT jsonb_object_agg(cs.species_code, cs.slots)
                 FROM campaign_species cs WHERE cs.campaign_id = c.id) AS species
            FROM campaigns c
            JOIN organizers o ON o.id = c.organizer_id
            JOIN localities l ON l.id = c.locality_id
            WHERE c.public_id = %s
            """,
            (public_id,),
        )
        row = cur.fetchone()
    if not row:
        return err(404, "not_found")
    return respond(200, row)


def handle_get_organizer(event: dict, public_id: str) -> dict:
    """
    Look up an organizer by their UUID public_id and return their campaigns with
    statuses. Keyed on public_id (not the serial id) so it is not enumerable.

    Data minimization: returns only the organization name and the campaign list
    needed for a status check — NOT the organizer's contact email/phone.
    """
    try:
        UUID(public_id)
    except ValueError:
        return err(400, "invalid_id")

    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, name FROM organizers WHERE public_id = %s",
            (public_id,),
        )
        org = cur.fetchone()
        if not org:
            return err(404, "not_found")

        cur.execute(
            """
            SELECT
                c.public_id  AS "submissionId",
                c.status,
                c.county_code AS county,
                l.name       AS locality,
                c.address,
                c.date_start AS "dateStart",
                c.date_end   AS "dateEnd",
                c.time_start AS "timeStart",
                c.time_end   AS "timeEnd",
                c.created_at AS "createdAt",
                (SELECT jsonb_object_agg(cs.species_code, cs.slots)
                 FROM campaign_species cs WHERE cs.campaign_id = c.id) AS species
            FROM campaigns c
            JOIN localities l ON l.id = c.locality_id
            WHERE c.organizer_id = %s
            ORDER BY c.date_start DESC
            """,
            (org["id"],),
        )
        campaigns = cur.fetchall()

    return respond(200, {
        "organizationName": org["name"],
        "campaigns": campaigns,
    })


def handle_get_citizen(event: dict, public_id: str) -> dict:
    """Returns minimal confirmation data — never PII via direct lookup."""
    try:
        UUID(public_id)
    except ValueError:
        return err(400, "invalid_id")

    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT c.public_id AS "citizenId", l.name AS locality,
                   co.name AS "countyName", c.status
            FROM citizens c
            JOIN localities l ON l.id = c.locality_id
            JOIN counties co ON co.code = c.county_code
            WHERE c.public_id = %s
            """,
            (public_id,),
        )
        row = cur.fetchone()
    if not row:
        return err(404, "not_found")
    return respond(200, row)


def handle_stats_locality(event: dict) -> dict:
    qs = event.get("queryStringParameters") or {}
    county = qs.get("county")
    locality_name = qs.get("locality")
    if not county or not locality_name:
        return err(400, "validation_failed",
                   errors=[{"field": "county/locality", "message": "both required"}])
    if not re.match(r"^[A-Z]{1,2}$", county):
        return err(400, "validation_failed",
                   errors=[{"field": "county", "message": "invalid code"}])

    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                COALESCE((SELECT COUNT(*) FROM citizens ci
                          JOIN localities l ON l.id = ci.locality_id
                          WHERE ci.status = 'active'
                            AND l.county_code = %s
                            AND LOWER(l.name) = LOWER(%s)), 0) AS in_locality,
                COALESCE((SELECT COUNT(*) FROM citizens
                          WHERE status = 'active' AND county_code = %s), 0) AS in_county
            """,
            (county, locality_name, county),
        )
        r = cur.fetchone()

    resp = respond(200, {
        "county": county,
        "locality": locality_name,
        "registeredInLocality": int(r["in_locality"]),
        "registeredInCounty": int(r["in_county"]),
    })
    resp["headers"]["Cache-Control"] = "public, max-age=60"
    return resp


def handle_list_counties(event: dict) -> dict:
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT code, name, slug FROM counties ORDER BY name")
        rows = cur.fetchall()
    resp = respond(200, {"counties": rows})
    resp["headers"]["Cache-Control"] = "public, max-age=86400"
    return resp


def handle_list_localities(event: dict, county_code: str) -> dict:
    if not re.match(r"^[A-Z]{1,2}$", county_code):
        return err(400, "invalid_county")

    qs = event.get("queryStringParameters") or {}
    q = (qs.get("q") or "").strip().lower()

    conn = get_conn()
    with conn.cursor() as cur:
        if q:
            cur.execute(
                """
                SELECT id, name FROM localities
                WHERE county_code = %s AND LOWER(name_simple) LIKE %s
                ORDER BY name LIMIT 50
                """,
                (county_code, f"{q}%"),
            )
        else:
            cur.execute(
                "SELECT id, name FROM localities WHERE county_code = %s ORDER BY name",
                (county_code,),
            )
        rows = cur.fetchall()

    resp = respond(200, {"localities": rows})
    resp["headers"]["Cache-Control"] = "public, max-age=86400"
    return resp


# ─── Magic-link handlers ─────────────────────────────────────────────────────

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


def handle_get_manage_token(event: dict, token: str) -> dict:
    conn = get_conn()
    with conn.cursor() as cur:
        tok = _load_token(cur, token, "citizen_manage")
        if not tok:
            return err(410, "token_invalid", "Linkul nu mai este valid.")

        cur.execute(
            """
            SELECT c.public_id AS "citizenId", c.name, l.name AS locality, c.status
            FROM citizens c JOIN localities l ON l.id = c.locality_id
            WHERE c.id = %s
            """,
            (tok["citizen_id"],),
        )
        citizen = cur.fetchone()
    if not citizen:
        return err(404, "not_found")
    return respond(200, {"valid": True, "citizen": citizen})


def handle_unsubscribe(event: dict, token: str, token_kind: str) -> dict:
    """Used by both /m/{token}/unsubscribe and /r/{token}/unsubscribe."""
    ip, ua = client_ip(event), client_ua(event)
    conn = get_conn()
    try:
        with conn.transaction(), conn.cursor() as cur:
            tok = _load_token(cur, token, token_kind)
            if not tok:
                return err(410, "token_invalid")

            cur.execute(
                """
                UPDATE citizens SET status = 'unsubscribed', unsubscribed_at = now()
                WHERE id = %s AND status IN ('active', 'pending_confirm')
                """,
                (tok["citizen_id"],),
            )
            cur.execute("UPDATE tokens SET used_at = now() WHERE id = %s", (tok["id"],))
            audit(cur, actor="self", action="citizen.unsubscribe",
                  entity_type="citizen", entity_id=tok["citizen_id"], ip=ip, ua=ua)
        return respond(200, {"message": "Te-am dezabonat. Datele tale au fost păstrate "
                                        "pentru audit dar nu te mai contactăm."})
    except Exception:
        log.exception("unsubscribe failed")
        return err(500, "internal_error")


def handle_erase(event: dict, token: str) -> dict:
    """GDPR Art. 17 — right to erasure. Nulls PII, keeps row for audit."""
    ip, ua = client_ip(event), client_ua(event)
    conn = get_conn()
    try:
        with conn.transaction(), conn.cursor() as cur:
            tok = _load_token(cur, token, "citizen_manage")
            if not tok:
                return err(410, "token_invalid")

            # Capture contact BEFORE we null it — we can't email them afterwards.
            cur.execute("SELECT email, name FROM citizens WHERE id = %s", (tok["citizen_id"],))
            crow = cur.fetchone() or {}
            erased_email, erased_name = crow.get("email"), crow.get("name")

            cur.execute("DELETE FROM citizen_species WHERE citizen_id = %s", (tok["citizen_id"],))
            cur.execute(
                """
                UPDATE citizens
                SET name = '[erased]', phone = NULL, phone_normalized = NULL,
                    email = NULL, gdpr_consent_ip = NULL, gdpr_consent_ua = NULL,
                    status = 'deleted', deleted_at = now()
                WHERE id = %s
                """,
                (tok["citizen_id"],),
            )
            # Revoke ALL outstanding tokens for this citizen
            cur.execute(
                "UPDATE tokens SET revoked_at = now() WHERE citizen_id = %s AND used_at IS NULL",
                (tok["citizen_id"],),
            )
            audit(cur, actor="self", action="citizen.erase",
                  entity_type="citizen", entity_id=tok["citizen_id"], ip=ip, ua=ua)

        # Committed. Final email to the address we captured above (best-effort).
        send_citizen_email("deleted", to_email=erased_email, name=erased_name)
        return respond(200, {"message": "Datele tale au fost șterse complet."})
    except Exception:
        log.exception("erase failed")
        return err(500, "internal_error")


def handle_refresh_confirm(event: dict, token: str) -> dict:
    """User clicked 'keep me on the list' after a campaign."""
    ip, ua = client_ip(event), client_ua(event)
    conn = get_conn()
    try:
        with conn.transaction(), conn.cursor() as cur:
            tok = _load_token(cur, token, "citizen_refresh")
            if not tok:
                return err(410, "token_invalid")
            cur.execute("UPDATE tokens SET used_at = now() WHERE id = %s", (tok["id"],))
            audit(cur, actor="self", action="citizen.refresh_confirm",
                  entity_type="citizen", entity_id=tok["citizen_id"], ip=ip, ua=ua)
        return respond(200, {"message": "Mulțumim, rămâi pe listă."})
    except Exception:
        log.exception("refresh confirm failed")
        return err(500, "internal_error")


# ═════════════════════════════════════════════════════════════════════════════
# ADMIN — auth + small helpers
# ═════════════════════════════════════════════════════════════════════════════

def _claims(event: dict) -> dict:
    """JWT claims injected by the API Gateway Cognito authorizer (HTTP API)."""
    return ((event.get("requestContext", {}) or {})
            .get("authorizer", {}).get("jwt", {}).get("claims", {})) or {}


def _groups(claims: dict) -> list:
    """cognito:groups arrives stringified on HTTP APIs ('[admins x]' or 'a,b')."""
    raw = claims.get("cognito:groups")
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(x) for x in raw]
    s = str(raw).strip().strip("[]")
    return [p for p in re.split(r"[,\s]+", s) if p]


def admin_email(event: dict) -> Optional[str]:
    return _claims(event).get("email")


def _valid_uuid(s: str) -> bool:
    try:
        UUID(s)
        return True
    except (ValueError, TypeError, AttributeError):
        return False


def _paging(qs: dict) -> tuple:
    try:
        page = max(1, int(qs.get("page", 1)))
    except (TypeError, ValueError):
        page = 1
    try:
        limit = int(qs.get("limit", DEFAULT_LIMIT))
    except (TypeError, ValueError):
        limit = DEFAULT_LIMIT
    limit = max(1, min(limit, MAX_LIMIT))
    return page, limit, (page - 1) * limit


def _admin_body(event: dict) -> Optional[dict]:
    try:
        return json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return None


# Shared "AdminCampaign" SELECT — identical shape for the campaigns list and an
# organizer's campaigns. Callers append WHERE / ORDER BY / LIMIT. WHERE clauses
# are assembled only from fixed fragments; all values are bound params.
_ADMIN_CAMPAIGN_SELECT = """
    SELECT
        c.public_id   AS "submissionId",
        o.name        AS "organizationName",
        c.county_code AS county,
        co.name       AS "countyName",
        l.name        AS locality,
        c.date_start  AS "dateStart",
        c.date_end    AS "dateEnd",
        c.status,
        c.created_at  AS "createdAt",
        c.reviewed_at AS "reviewedAt",
        c.reviewed_by AS "reviewedBy"
    FROM campaigns c
    JOIN organizers o ON o.id = c.organizer_id
    JOIN localities l ON l.id = c.locality_id
    JOIN counties  co ON co.code = c.county_code
"""


# ═════════════════════════════════════════════════════════════════════════════
# ADMIN — CAMPAIGNS
# ═════════════════════════════════════════════════════════════════════════════

def handle_admin_list_campaigns(event: dict) -> dict:
    qs = event.get("queryStringParameters") or {}
    page, limit, offset = _paging(qs)
    where, params = [], []
    status = qs.get("status")
    if status:
        if status not in CAMPAIGN_STATUSES:
            return err(400, "validation_failed",
                       errors=[{"field": "status", "message": "invalid status"}])
        where.append("c.status = %s"); params.append(status)
    county = qs.get("county")
    if county:
        if not COUNTY_RE.match(county):
            return err(400, "validation_failed",
                       errors=[{"field": "county", "message": "invalid county code"}])
        where.append("c.county_code = %s"); params.append(county)
    q = (qs.get("q") or "").strip()
    if q:
        where.append("(o.name ILIKE %s OR l.name ILIKE %s)")
        params += [f"%{q}%", f"%{q}%"]
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(f"""SELECT COUNT(*) AS n FROM campaigns c
                        JOIN organizers o ON o.id=c.organizer_id
                        JOIN localities l ON l.id=c.locality_id {where_sql}""", params)
        total = int(cur.fetchone()["n"])
        cur.execute(f"{_ADMIN_CAMPAIGN_SELECT} {where_sql} "
                    f"ORDER BY c.created_at DESC LIMIT %s OFFSET %s", params + [limit, offset])
        rows = cur.fetchall()
    return respond(200, {"campaigns": rows, "total": total})


def handle_admin_get_campaign(event: dict, public_id: str) -> dict:
    if not _valid_uuid(public_id):
        return err(400, "invalid_id")
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                c.public_id AS "submissionId", o.name AS "organizationName",
                c.county_code AS county, co.name AS "countyName", l.name AS locality,
                c.date_start AS "dateStart", c.date_end AS "dateEnd", c.status,
                c.created_at AS "createdAt", c.reviewed_at AS "reviewedAt",
                c.reviewed_by AS "reviewedBy", c.phone_public AS "phonePublic",
                c.address, c.time_start AS "timeStart", c.time_end AS "timeEnd", c.doctor,
                o.contact_email AS "contactEmail", o.contact_phone AS "contactPhone",
                c.rejection_reason AS "rejectionReason",
                c.submitted_ip AS "submittedIp", c.submitted_ua AS "submittedUa",
                (SELECT jsonb_object_agg(cs.species_code, cs.slots)
                 FROM campaign_species cs WHERE cs.campaign_id=c.id) AS species
            FROM campaigns c
            JOIN organizers o ON o.id=c.organizer_id
            JOIN localities l ON l.id=c.locality_id
            JOIN counties  co ON co.code=c.county_code
            WHERE c.public_id=%s""", (public_id,))
        row = cur.fetchone()
    if not row:
        return err(404, "not_found")
    row["species"] = row["species"] or {}
    return respond(200, row)


def handle_admin_approve_campaign(event: dict, public_id: str) -> dict:
    if not _valid_uuid(public_id):
        return err(400, "invalid_id")
    actor = admin_email(event); ip, ua = client_ip(event), client_ua(event)
    conn = get_conn()
    try:
        with conn.transaction(), conn.cursor() as cur:
            cur.execute("SELECT id, status FROM campaigns WHERE public_id=%s FOR UPDATE", (public_id,))
            row = cur.fetchone()
            if not row:
                return err(404, "not_found")
            if row["status"] != "pending":
                return err(409, "invalid_state", "Only pending campaigns can be approved.")
            cur.execute("""UPDATE campaigns SET status='approved', reviewed_at=now(),
                           reviewed_by=%s WHERE id=%s RETURNING reviewed_at""", (actor, row["id"]))
            reviewed_at = cur.fetchone()["reviewed_at"]
            audit(cur, actor=actor, action="campaign.approve", entity_type="campaign",
                  entity_id=row["id"], ip=ip, ua=ua)
            # Read the email payload while still in the transaction; send after commit.
            email_payload = fetch_campaign_email_payload(cur, row["id"])

            # Citizens to notify: active, with an email, in the campaign's locality.
            # Issue a fresh per-recipient manage token so each alert carries a
            # working unsubscribe link (raw tokens aren't recoverable — only their
            # hashes are stored). Tokens commit with the approval, so the links work.
            alert_recipients = []
            if email_payload:
                cur.execute(
                    """SELECT id, email FROM citizens
                       WHERE status = 'active' AND email IS NOT NULL AND locality_id = %s""",
                    (email_payload["locality_id"],),
                )
                for cz in cur.fetchall():
                    tok = issue_token(cur, kind="citizen_manage",
                                      citizen_id=cz["id"], ttl=timedelta(days=365))
                    alert_recipients.append((cz["email"], tok))

        # Transaction committed. All emails below are best-effort (never raise).
        if email_payload:
            site = ENVIRONMENTS[_active_env]["origin"]
            campaign_url = f"{site}/campanie/{email_payload['campaign_public_id']}"
            # 1) tell the organizer it's approved
            send_campaign_email(
                "approved",
                to_email=email_payload["contact_email"],
                organization_name=email_payload["organization_name"],
                campaign_public_id=str(email_payload["campaign_public_id"]),
                organizer_public_id=str(email_payload["organizer_public_id"]),
                site_url=site,
                details=email_payload,
            )
            # 2) alert citizens in the area (each with their own unsubscribe link)
            for cz_email, cz_tok in alert_recipients:
                send_citizen_email(
                    "campaign_alert",
                    to_email=cz_email,
                    locality=email_payload["locality"],
                    organization_name=email_payload["organization_name"],
                    details=email_payload,
                    campaign_url=campaign_url,
                    manage_url=_citizen_manage_url(cz_tok),
                )
            if alert_recipients:
                log.info("campaign alert fan-out", extra={"recipients": len(alert_recipients)})
        return respond(200, {"status": "approved", "reviewedAt": reviewed_at, "reviewedBy": actor})
    except Exception:
        log.exception("approve failed"); return err(500, "internal_error")


def handle_admin_reject_campaign(event: dict, public_id: str) -> dict:
    if not _valid_uuid(public_id):
        return err(400, "invalid_id")
    body = _admin_body(event)
    if body is None:
        return err(400, "invalid_json")
    reason = (body.get("reason") or "").strip()
    if not (1 <= len(reason) <= 500):
        return err(400, "validation_failed",
                   errors=[{"field": "reason", "message": "required, 1..500 chars"}])
    actor = admin_email(event); ip, ua = client_ip(event), client_ua(event)
    conn = get_conn()
    try:
        with conn.transaction(), conn.cursor() as cur:
            cur.execute("SELECT id, status FROM campaigns WHERE public_id=%s FOR UPDATE", (public_id,))
            row = cur.fetchone()
            if not row:
                return err(404, "not_found")
            if row["status"] != "pending":
                return err(409, "invalid_state", "Only pending campaigns can be rejected.")
            cur.execute("""UPDATE campaigns SET status='rejected', rejection_reason=%s,
                           reviewed_at=now(), reviewed_by=%s WHERE id=%s
                           RETURNING reviewed_at""", (reason, actor, row["id"]))
            reviewed_at = cur.fetchone()["reviewed_at"]
            audit(cur, actor=actor, action="campaign.reject", entity_type="campaign",
                  entity_id=row["id"], ip=ip, ua=ua, metadata={"reason": reason})
            email_payload = fetch_campaign_email_payload(cur, row["id"])

        # Transaction committed. Notify the organizer best-effort (never raises).
        if email_payload:
            send_campaign_email(
                "rejected",
                to_email=email_payload["contact_email"],
                organization_name=email_payload["organization_name"],
                campaign_public_id=str(email_payload["campaign_public_id"]),
                organizer_public_id=str(email_payload["organizer_public_id"]),
                site_url=ENVIRONMENTS[_active_env]["origin"],
                details=email_payload,
                reason=reason,
            )
        return respond(200, {"status": "rejected", "reviewedAt": reviewed_at, "reviewedBy": actor})
    except Exception:
        log.exception("reject failed"); return err(500, "internal_error")


def handle_admin_patch_campaign(event: dict, public_id: str) -> dict:
    """Optional: cancel/finish/edit via {status} / {doctor}."""
    if not _valid_uuid(public_id):
        return err(400, "invalid_id")
    body = _admin_body(event)
    if body is None:
        return err(400, "invalid_json")
    sets, params, changed = [], [], {}
    if "status" in body:
        if body["status"] not in CAMPAIGN_STATUSES:
            return err(400, "validation_failed",
                       errors=[{"field": "status", "message": "invalid status"}])
        sets.append("status=%s"); params.append(body["status"]); changed["status"] = body["status"]
    if "doctor" in body:
        sets.append("doctor=%s"); params.append(body["doctor"]); changed["doctor"] = body["doctor"]
    if not sets:
        return err(400, "validation_failed",
                   errors=[{"field": "body", "message": "no editable fields supplied"}])
    actor = admin_email(event); ip, ua = client_ip(event), client_ua(event)
    conn = get_conn()
    try:
        with conn.transaction(), conn.cursor() as cur:
            cur.execute("SELECT id FROM campaigns WHERE public_id=%s FOR UPDATE", (public_id,))
            row = cur.fetchone()
            if not row:
                return err(404, "not_found")
            cur.execute(f"UPDATE campaigns SET {', '.join(sets)} WHERE id=%s", params + [row["id"]])
            audit(cur, actor=actor, action="campaign.update", entity_type="campaign",
                  entity_id=row["id"], ip=ip, ua=ua, metadata={"changed": changed})
        return respond(200, {"status": changed.get("status", "updated")})
    except Exception:
        log.exception("patch campaign failed"); return err(500, "internal_error")


# ═════════════════════════════════════════════════════════════════════════════
# ADMIN — CITIZENS  (PII — minimize; list never returns raw phone/email)
# ═════════════════════════════════════════════════════════════════════════════

def handle_admin_list_citizens(event: dict) -> dict:
    qs = event.get("queryStringParameters") or {}
    page, limit, offset = _paging(qs)
    where, params = [], []
    status = qs.get("status")
    if status:
        if status not in CITIZEN_STATUSES:
            return err(400, "validation_failed",
                       errors=[{"field": "status", "message": "invalid status"}])
        where.append("c.status=%s"); params.append(status)
    county = qs.get("county")
    if county:
        if not COUNTY_RE.match(county):
            return err(400, "validation_failed",
                       errors=[{"field": "county", "message": "invalid county code"}])
        where.append("c.county_code=%s"); params.append(county)
    locality = (qs.get("locality") or "").strip()
    if locality:
        where.append("LOWER(l.name)=LOWER(%s)"); params.append(locality)
    q = (qs.get("q") or "").strip()
    if q:
        where.append("(c.name ILIKE %s OR l.name ILIKE %s)"); params += [f"%{q}%", f"%{q}%"]
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(f"""SELECT COUNT(*) AS n FROM citizens c
                        JOIN localities l ON l.id=c.locality_id {where_sql}""", params)
        total = int(cur.fetchone()["n"])
        # PII MINIMIZATION: only channel existence leaves the DB for list views.
        cur.execute(f"""
            SELECT c.public_id AS "citizenId", c.name, co.name AS "countyName",
                   l.name AS locality, c.status,
                   (c.phone IS NOT NULL) AS has_phone,
                   (c.email IS NOT NULL) AS has_email,
                   c.created_at AS "createdAt"
            FROM citizens c
            JOIN localities l ON l.id=c.locality_id
            JOIN counties  co ON co.code=c.county_code
            {where_sql}
            ORDER BY c.created_at DESC LIMIT %s OFFSET %s""", params + [limit, offset])
        rows = [{
            "citizenId": r["citizenId"], "name": r["name"], "countyName": r["countyName"],
            "locality": r["locality"], "status": r["status"],
            "channelMask": {"phone": bool(r["has_phone"]), "email": bool(r["has_email"])},
            "createdAt": r["createdAt"],
        } for r in cur.fetchall()]
    return respond(200, {"citizens": rows, "total": total})


def handle_admin_get_citizen(event: dict, public_id: str) -> dict:
    """Returns full PII. PII ACCESS IS AUDITED (citizen.view) before responding."""
    if not _valid_uuid(public_id):
        return err(400, "invalid_id")
    actor = admin_email(event); ip, ua = client_ip(event), client_ua(event)
    conn = get_conn()
    try:
        with conn.transaction(), conn.cursor() as cur:
            cur.execute("""
                SELECT c.id, c.public_id AS "citizenId", c.name, co.name AS "countyName",
                       l.name AS locality, c.status, c.phone, c.email, c.notes,
                       c.gdpr_consent_at AS "gdprConsentAt", c.created_at AS "createdAt"
                FROM citizens c
                JOIN localities l ON l.id=c.locality_id
                JOIN counties  co ON co.code=c.county_code
                WHERE c.public_id=%s""", (public_id,))
            row = cur.fetchone()
            if not row:
                return err(404, "not_found")
            internal_id = row.pop("id")
            cur.execute("SELECT species_code, animal_count FROM citizen_species WHERE citizen_id=%s",
                        (internal_id,))
            row["species"] = {r["species_code"]: r["animal_count"] for r in cur.fetchall()}
            row["channelMask"] = {"phone": row["phone"] is not None, "email": row["email"] is not None}
            audit(cur, actor=actor, action="citizen.view", entity_type="citizen",
                  entity_id=internal_id, ip=ip, ua=ua)
        return respond(200, row)
    except Exception:
        log.exception("get citizen failed"); return err(500, "internal_error")


def handle_admin_patch_citizen(event: dict, public_id: str) -> dict:
    """Body {notes?, status?}. Audited with a field-name diff (no free-text PII)."""
    if not _valid_uuid(public_id):
        return err(400, "invalid_id")
    body = _admin_body(event)
    if body is None:
        return err(400, "invalid_json")
    sets, params, changed = [], [], {}
    if "status" in body:
        if body["status"] not in CITIZEN_STATUSES:
            return err(400, "validation_failed",
                       errors=[{"field": "status", "message": "invalid status"}])
        sets.append("status=%s"); params.append(body["status"]); changed["status"] = body["status"]
    if "notes" in body:
        sets.append("notes=%s"); params.append(body["notes"]); changed["notes"] = "updated"
    if not sets:
        return err(400, "validation_failed",
                   errors=[{"field": "body", "message": "no editable fields supplied"}])
    actor = admin_email(event); ip, ua = client_ip(event), client_ua(event)
    conn = get_conn()
    try:
        with conn.transaction(), conn.cursor() as cur:
            cur.execute("SELECT id FROM citizens WHERE public_id=%s FOR UPDATE", (public_id,))
            row = cur.fetchone()
            if not row:
                return err(404, "not_found")
            cur.execute(f"UPDATE citizens SET {', '.join(sets)} WHERE id=%s", params + [row["id"]])
            audit(cur, actor=actor, action="citizen.update", entity_type="citizen",
                  entity_id=row["id"], ip=ip, ua=ua, metadata={"changed": changed})
        return respond(200, {"status": changed.get("status", "updated")})
    except Exception:
        log.exception("patch citizen failed"); return err(500, "internal_error")


def handle_admin_unsubscribe_citizen(event: dict, public_id: str) -> dict:
    if not _valid_uuid(public_id):
        return err(400, "invalid_id")
    actor = admin_email(event); ip, ua = client_ip(event), client_ua(event)
    conn = get_conn()
    try:
        with conn.transaction(), conn.cursor() as cur:
            cur.execute("SELECT id FROM citizens WHERE public_id=%s FOR UPDATE", (public_id,))
            row = cur.fetchone()
            if not row:
                return err(404, "not_found")
            cur.execute("UPDATE citizens SET status='unsubscribed', unsubscribed_at=now() WHERE id=%s",
                        (row["id"],))
            audit(cur, actor=actor, action="citizen.unsubscribe", entity_type="citizen",
                  entity_id=row["id"], ip=ip, ua=ua)
        return respond(200, {"status": "unsubscribed"})
    except Exception:
        log.exception("unsubscribe failed"); return err(500, "internal_error")


def handle_admin_erase_citizen(event: dict, public_id: str) -> dict:
    """GDPR Art.17: null PII, status=deleted, revoke tokens. Row retained for
    audit history + aggregate counts but no longer identifiable."""
    if not _valid_uuid(public_id):
        return err(400, "invalid_id")
    body = _admin_body(event)
    if body is None:
        return err(400, "invalid_json")
    reason = (body.get("reason") or "").strip()
    if not reason:
        return err(400, "validation_failed",
                   errors=[{"field": "reason", "message": "reason required"}])
    actor = admin_email(event); ip, ua = client_ip(event), client_ua(event)
    conn = get_conn()
    try:
        with conn.transaction(), conn.cursor() as cur:
            cur.execute("SELECT id, email, name FROM citizens WHERE public_id=%s FOR UPDATE",
                        (public_id,))
            row = cur.fetchone()
            if not row:
                return err(404, "not_found")
            cid = row["id"]
            erased_email, erased_name = row["email"], row["name"]  # capture before null
            cur.execute("DELETE FROM citizen_species WHERE citizen_id=%s", (cid,))
            cur.execute("""UPDATE citizens SET name='[erased]', phone=NULL, phone_normalized=NULL,
                           email=NULL, notes=NULL, status='deleted', deleted_at=now()
                           WHERE id=%s""", (cid,))
            cur.execute("UPDATE tokens SET revoked_at=now() WHERE citizen_id=%s AND used_at IS NULL",
                        (cid,))
            audit(cur, actor=actor, action="citizen.erase", entity_type="citizen",
                  entity_id=cid, ip=ip, ua=ua, metadata={"reason": reason})

        # Committed. Confirm deletion to the address captured above (best-effort).
        send_citizen_email("deleted", to_email=erased_email, name=erased_name)
        return respond(200, {"status": "deleted"})
    except Exception:
        log.exception("erase failed"); return err(500, "internal_error")


# ═════════════════════════════════════════════════════════════════════════════
# ADMIN — ORGANIZERS
# ═════════════════════════════════════════════════════════════════════════════

def handle_admin_list_organizers(event: dict) -> dict:
    qs = event.get("queryStringParameters") or {}
    page, limit, offset = _paging(qs)
    where, params = [], []
    q = (qs.get("q") or "").strip()
    if q:
        where.append("(o.name ILIKE %s OR o.contact_email ILIKE %s)"); params += [f"%{q}%", f"%{q}%"]
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) AS n FROM organizers o {where_sql}", params)
        total = int(cur.fetchone()["n"])
        cur.execute(f"""
            SELECT o.public_id AS "organizerId", o.name, o.contact_email AS "contactEmail",
                   o.contact_phone AS "contactPhone", COUNT(c.id) AS "campaignCount",
                   o.created_at AS "createdAt"
            FROM organizers o
            LEFT JOIN campaigns c ON c.organizer_id=o.id
            {where_sql}
            GROUP BY o.id ORDER BY o.created_at DESC LIMIT %s OFFSET %s""", params + [limit, offset])
        rows = cur.fetchall()
    for r in rows:
        r["campaignCount"] = int(r["campaignCount"])
    return respond(200, {"organizers": rows, "total": total})


def handle_admin_get_organizer(event: dict, public_id: str) -> dict:
    if not _valid_uuid(public_id):
        return err(400, "invalid_id")
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""SELECT id, public_id AS "organizerId", name,
                       contact_email AS "contactEmail", contact_phone AS "contactPhone",
                       notes, created_at AS "createdAt"
                       FROM organizers WHERE public_id=%s""", (public_id,))
        org = cur.fetchone()
        if not org:
            return err(404, "not_found")
        internal_id = org.pop("id")
        cur.execute(f"{_ADMIN_CAMPAIGN_SELECT} WHERE c.organizer_id=%s ORDER BY c.date_start DESC",
                    (internal_id,))
        org["campaigns"] = cur.fetchall()
    return respond(200, org)


def handle_admin_patch_organizer(event: dict, public_id: str) -> dict:
    """Optional: edit contact details / notes."""
    if not _valid_uuid(public_id):
        return err(400, "invalid_id")
    body = _admin_body(event)
    if body is None:
        return err(400, "invalid_json")
    field_map = {"name": "name", "contactEmail": "contact_email",
                 "contactPhone": "contact_phone", "notes": "notes"}
    sets, params, changed = [], [], []
    for api_field, col in field_map.items():
        if api_field in body:
            sets.append(f"{col}=%s"); params.append(body[api_field]); changed.append(api_field)
    if not sets:
        return err(400, "validation_failed",
                   errors=[{"field": "body", "message": "no editable fields supplied"}])
    actor = admin_email(event); ip, ua = client_ip(event), client_ua(event)
    conn = get_conn()
    try:
        with conn.transaction(), conn.cursor() as cur:
            cur.execute("SELECT id FROM organizers WHERE public_id=%s FOR UPDATE", (public_id,))
            row = cur.fetchone()
            if not row:
                return err(404, "not_found")
            cur.execute(f"UPDATE organizers SET {', '.join(sets)} WHERE id=%s", params + [row["id"]])
            audit(cur, actor=actor, action="organizer.update", entity_type="organizer",
                  entity_id=row["id"], ip=ip, ua=ua, metadata={"changed": changed})
        return respond(200, {"status": "updated"})
    except Exception:
        log.exception("patch organizer failed"); return err(500, "internal_error")


# ═════════════════════════════════════════════════════════════════════════════
# ADMIN — DASHBOARD + AUDIT
# ═════════════════════════════════════════════════════════════════════════════

def handle_admin_stats_overview(event: dict) -> dict:
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE status='pending')   AS pending,
                COUNT(*) FILTER (WHERE status='approved')  AS approved,
                COUNT(*) FILTER (WHERE status='rejected')  AS rejected,
                COUNT(*) FILTER (WHERE status='cancelled') AS cancelled,
                COUNT(*) FILTER (WHERE status='finished')  AS finished,
                COUNT(*) FILTER (
                    WHERE status='approved'
                      AND ((date_end IS NOT NULL AND date_end   >= CURRENT_DATE)
                        OR (date_end IS NULL     AND date_start >= CURRENT_DATE))
                ) AS approved_upcoming
            FROM campaigns""")
        c = cur.fetchone()
        cur.execute("""SELECT COUNT(*) FILTER (WHERE status='active') AS active,
                              COUNT(*) FILTER (WHERE created_at::date=CURRENT_DATE) AS today
                       FROM citizens""")
        z = cur.fetchone()
    return respond(200, {
        "pendingCampaigns": int(c["pending"]),
        "approvedUpcoming": int(c["approved_upcoming"]),
        "citizensActive": int(z["active"]),
        "registrationsToday": int(z["today"]),
        "byStatus": {"pending": int(c["pending"]), "approved": int(c["approved"]),
                     "rejected": int(c["rejected"]), "cancelled": int(c["cancelled"]),
                     "finished": int(c["finished"])},
    })


def handle_admin_list_audit(event: dict) -> dict:
    qs = event.get("queryStringParameters") or {}
    page, limit, offset = _paging(qs)
    where, params = [], []
    if qs.get("entityType"):
        where.append("entity_type=%s"); params.append(qs["entityType"])
    if qs.get("entityId"):
        try:
            params.append(int(qs["entityId"]))
        except (TypeError, ValueError):
            return err(400, "validation_failed",
                       errors=[{"field": "entityId", "message": "must be an integer"}])
        where.append("entity_id=%s")
    if qs.get("action"):
        where.append("action=%s"); params.append(qs["action"])
    if qs.get("actor"):
        where.append("actor=%s"); params.append(qs["actor"])
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) AS n FROM audit_log {where_sql}", params)
        total = int(cur.fetchone()["n"])
        cur.execute(f"""
            SELECT id, occurred_at AS "occurredAt", actor, action,
                   entity_type AS "entityType", entity_id AS "entityId",
                   ip_address AS "ipAddress", metadata
            FROM audit_log {where_sql}
            ORDER BY occurred_at DESC, id DESC LIMIT %s OFFSET %s""", params + [limit, offset])
        rows = cur.fetchall()
    return respond(200, {"entries": rows, "total": total})


# ═════════════════════════════════════════════════════════════════════════════
# ADMIN — REPORTS (CSV export)   GET /admin/reports/{type}
# Implemented in Python in THIS Lambda so the reports sit alongside the other
# /admin/** routes and reuse the same auth + audit path. (The handoff spec's
# "Node.js/TypeScript" assumed a standalone function; this codebase is one
# Python Lambda, so they live here.)
# ═════════════════════════════════════════════════════════════════════════════

ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Per-report status whitelist. citizens NEVER includes 'deleted' (GDPR Art.17:
# erased rows are never resurfaced). Empty set = status filter not used.
REPORT_STATUSES = {
    "campaigns":  {"pending", "approved", "rejected", "cancelled", "finished"},
    "citizens":   {"active", "pending_confirm", "unsubscribed"},
    "organizers": set(),
    "activity":   set(),
}


def _csv_cell(v) -> str:
    """RFC-4180 cell. None -> ''; quote if it contains ", comma, CR or LF."""
    if v is None:
        return ""
    s = str(v)
    if re.search(r'[",\r\n]', s):
        return '"' + s.replace('"', '""') + '"'
    return s


def to_csv(header: list, rows: list) -> str:
    """UTF-8 BOM + CRLF-terminated RFC-4180 CSV (Excel-friendly diacritics)."""
    lines = [",".join(_csv_cell(h) for h in header)]
    lines += [",".join(_csv_cell(c) for c in r) for r in rows]
    return "﻿" + "\r\n".join(lines) + "\r\n"


def _fmt_ts(dt) -> str:
    """Timestamp -> 'YYYY-MM-DD HH:MM' UTC; None -> ''."""
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M")


def _fmt_date(d) -> str:
    return d.isoformat() if d else ""


def csv_response(report_type: str, body_text: str) -> dict:
    today = datetime.now(timezone.utc).date().isoformat()
    headers = {
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": f'attachment; filename="raport-{report_type}-{today}.csv"',
        "Cache-Control": "no-store",
        **_cors_headers(),
    }
    return {"statusCode": 200, "headers": headers, "body": body_text}


# Per-report query builders → (header, rows). The "(%s::type IS NULL OR …)" idiom
# means an absent filter (None) adds no constraint. Param order is documented by
# the tuple passed to execute(); all values are bound, never interpolated.

def _report_campaigns(cur, frm, to, county, status):
    cur.execute(
        """
        SELECT c.public_id, o.name AS organization_name, c.county_code AS county,
               co.name AS county_name, l.name AS locality,
               c.date_start, c.date_end, c.status,
               c.created_at, c.reviewed_at, c.reviewed_by
        FROM campaigns c
        JOIN organizers o ON o.id = c.organizer_id
        JOIN counties   co ON co.code = c.county_code
        JOIN localities l  ON l.id = c.locality_id
        WHERE (%s::date IS NULL OR c.created_at >= %s::date)
          AND (%s::date IS NULL OR c.created_at < (%s::date + INTERVAL '1 day'))
          AND (%s::text IS NULL OR c.county_code = %s)
          AND (%s::text IS NULL OR c.status = %s::campaign_status)
        ORDER BY c.created_at DESC
        """,
        (frm, frm, to, to, county, county, status, status),
    )
    header = ["public_id", "organization_name", "county", "county_name", "locality",
              "date_start", "date_end", "status", "created_at", "reviewed_at", "reviewed_by"]
    rows = [[
        str(r["public_id"]), r["organization_name"], r["county"], r["county_name"],
        r["locality"], _fmt_date(r["date_start"]), _fmt_date(r["date_end"]), r["status"],
        _fmt_ts(r["created_at"]), _fmt_ts(r["reviewed_at"]), r["reviewed_by"] or "",
    ] for r in cur.fetchall()]
    return header, rows


def _report_citizens(cur, frm, to, county, status):
    # PII-minimized: presence-only has_phone/has_email; raw values never selected.
    # 'deleted' rows excluded by design (already nulled per GDPR Art.17).
    cur.execute(
        """
        SELECT c.public_id, c.name, co.name AS county_name, l.name AS locality, c.status,
               (c.phone IS NOT NULL) AS has_phone, (c.email IS NOT NULL) AS has_email,
               c.created_at
        FROM citizens c
        JOIN counties   co ON co.code = c.county_code
        JOIN localities l  ON l.id = c.locality_id
        WHERE (%s::date IS NULL OR c.created_at >= %s::date)
          AND (%s::date IS NULL OR c.created_at < (%s::date + INTERVAL '1 day'))
          AND (%s::text IS NULL OR c.county_code = %s)
          AND (%s::text IS NULL OR c.status = %s::citizen_status)
          AND c.status <> 'deleted'
        ORDER BY c.created_at DESC
        """,
        (frm, frm, to, to, county, county, status, status),
    )
    header = ["public_id", "name", "county_name", "locality", "status",
              "has_phone", "has_email", "created_at"]
    rows = [[
        str(r["public_id"]), r["name"], r["county_name"], r["locality"], r["status"],
        "da" if r["has_phone"] else "nu", "da" if r["has_email"] else "nu",
        _fmt_ts(r["created_at"]),
    ] for r in cur.fetchall()]
    return header, rows


def _report_organizers(cur, frm, to, county, status):
    # county/status ignored: organizers are not county- or status-scoped.
    # campaign_count counts ALL campaign statuses for the organizer.
    cur.execute(
        """
        SELECT o.public_id, o.name, o.contact_email, o.contact_phone,
               (SELECT COUNT(*) FROM campaigns c WHERE c.organizer_id = o.id) AS campaign_count,
               o.created_at
        FROM organizers o
        WHERE (%s::date IS NULL OR o.created_at >= %s::date)
          AND (%s::date IS NULL OR o.created_at < (%s::date + INTERVAL '1 day'))
        ORDER BY o.created_at DESC
        """,
        (frm, frm, to, to),
    )
    header = ["public_id", "name", "contact_email", "contact_phone",
              "campaign_count", "created_at"]
    rows = [[
        str(r["public_id"]), r["name"], r["contact_email"] or "", r["contact_phone"] or "",
        int(r["campaign_count"]), _fmt_ts(r["created_at"]),
    ] for r in cur.fetchall()]
    return header, rows


def _report_activity(cur, frm, to, county, status):
    # county/status ignored (audit rows have neither). entity_id is the internal
    # bigint reference — acceptable to expose to admins per spec. host() strips
    # the inet netmask so the IP renders cleanly.
    cur.execute(
        """
        SELECT occurred_at, actor, action, entity_type, entity_id,
               host(ip_address) AS ip_address
        FROM audit_log
        WHERE (%s::date IS NULL OR occurred_at >= %s::date)
          AND (%s::date IS NULL OR occurred_at < (%s::date + INTERVAL '1 day'))
        ORDER BY occurred_at DESC
        """,
        (frm, frm, to, to),
    )
    header = ["occurred_at", "actor", "action", "entity_type", "entity_id", "ip_address"]
    rows = [[
        _fmt_ts(r["occurred_at"]), r["actor"] or "", r["action"], r["entity_type"],
        "" if r["entity_id"] is None else r["entity_id"], r["ip_address"] or "",
    ] for r in cur.fetchall()]
    return header, rows


_REPORT_BUILDERS = {
    "campaigns":  _report_campaigns,
    "citizens":   _report_citizens,
    "organizers": _report_organizers,
    "activity":   _report_activity,
}


def handle_admin_report(event: dict, report_type: str) -> dict:
    # Unknown type -> 404 (the proxy also guards this; defend in depth).
    if report_type not in _REPORT_BUILDERS:
        return err(404, "not_found")

    qs = event.get("queryStringParameters") or {}
    frm = (qs.get("from") or "").strip() or None
    to = (qs.get("to") or "").strip() or None
    county = (qs.get("county") or "").strip() or None
    status = (qs.get("status") or "").strip() or None

    # Dates: must be YYYY-MM-DD; from <= to if both present (ISO strings compare
    # lexicographically as dates).
    if (frm and not ISO_DATE_RE.match(frm)) or (to and not ISO_DATE_RE.match(to)):
        return err(400, "validation_failed")
    if frm and to and frm > to:
        return err(400, "validation_failed")

    # county applies to campaigns + citizens only; ignored elsewhere.
    if county and not COUNTY_RE.match(county):
        return err(400, "validation_failed")
    eff_county = county if (county and report_type in ("campaigns", "citizens")) else None

    # status applies to campaigns + citizens only; validate against the set.
    eff_status = None
    if status and REPORT_STATUSES[report_type]:
        if status not in REPORT_STATUSES[report_type]:
            return err(400, "validation_failed")
        eff_status = status

    actor = admin_email(event)
    ip, ua = client_ip(event), client_ua(event)

    conn = get_conn()
    try:
        with conn.transaction(), conn.cursor() as cur:
            header, rows = _REPORT_BUILDERS[report_type](cur, frm, to, eff_county, eff_status)

            # Mandatory audit (the PII-access event for citizens). Log only the
            # filters actually applied; never the row data.
            applied = {}
            if frm:
                applied["from"] = frm
            if to:
                applied["to"] = to
            if eff_county:
                applied["county"] = eff_county
            if eff_status:
                applied["status"] = eff_status
            audit(cur, actor=actor, action="report.export", entity_type="report",
                  entity_id=None, ip=ip, ua=ua,
                  metadata={"type": report_type, "filters": applied, "row_count": len(rows)})

        return csv_response(report_type, to_csv(header, rows))
    except Exception:
        log.exception("report export failed: %s", report_type)
        return err(500, "server_error")


# ─────────────────────────────────────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────────────────────────────────────

# (method, regex, handler-name, path-arg names)
ROUTES = [
    # Public
    ("POST", re.compile(r"^/register$"),                          "register",         ()),
    ("GET",  re.compile(r"^/register/(?P<id>[\w-]+)$"),           "get_citizen",      ("id",)),
    ("POST", re.compile(r"^/campaigns/submit$"),                  "campaign_submit",  ()),
    ("GET",  re.compile(r"^/campaigns$"),                         "list_campaigns",   ()),
    ("GET",  re.compile(r"^/campaigns/(?P<id>[\w-]+)$"),           "get_campaign",     ("id",)),
    ("GET",  re.compile(r"^/organizer/(?P<id>[\w-]+)$"),           "get_organizer",    ("id",)),
    ("GET",  re.compile(r"^/stats/locality$"),                    "stats_locality",   ()),
    ("GET",  re.compile(r"^/stats/map$"),                         "stats_map",        ()),
    ("GET",  re.compile(r"^/counties$"),                          "list_counties",    ()),
    ("GET",  re.compile(r"^/counties/(?P<code>[A-Z]{1,2})/localities$"),
                                                                  "list_localities",  ("code",)),
    ("GET",  re.compile(r"^/m/(?P<token>[\w-]+)$"),               "get_manage_token", ("token",)),
    ("POST", re.compile(r"^/m/(?P<token>[\w-]+)/unsubscribe$"),   "unsubscribe_m",    ("token",)),
    ("POST", re.compile(r"^/m/(?P<token>[\w-]+)/erase$"),         "erase",            ("token",)),
    ("POST", re.compile(r"^/r/(?P<token>[\w-]+)/confirm$"),       "refresh_confirm",  ("token",)),
    ("POST", re.compile(r"^/r/(?P<token>[\w-]+)/unsubscribe$"),   "unsubscribe_r",    ("token",)),

    # Admin
    ("GET",   re.compile(r"^/admin/campaigns$"),                           "admin_list_campaigns",      ()),
    ("GET",   re.compile(r"^/admin/campaigns/(?P<id>[\w-]+)$"),            "admin_get_campaign",        ("id",)),
    ("POST",  re.compile(r"^/admin/campaigns/(?P<id>[\w-]+)/approve$"),    "admin_approve_campaign",    ("id",)),
    ("POST",  re.compile(r"^/admin/campaigns/(?P<id>[\w-]+)/reject$"),     "admin_reject_campaign",     ("id",)),
    ("PATCH", re.compile(r"^/admin/campaigns/(?P<id>[\w-]+)$"),            "admin_patch_campaign",      ("id",)),
    ("GET",   re.compile(r"^/admin/citizens$"),                           "admin_list_citizens",       ()),
    ("GET",   re.compile(r"^/admin/citizens/(?P<id>[\w-]+)$"),             "admin_get_citizen",         ("id",)),
    ("PATCH", re.compile(r"^/admin/citizens/(?P<id>[\w-]+)$"),             "admin_patch_citizen",       ("id",)),
    ("POST",  re.compile(r"^/admin/citizens/(?P<id>[\w-]+)/unsubscribe$"), "admin_unsubscribe_citizen", ("id",)),
    ("POST",  re.compile(r"^/admin/citizens/(?P<id>[\w-]+)/erase$"),       "admin_erase_citizen",       ("id",)),
    ("GET",   re.compile(r"^/admin/organizers$"),                         "admin_list_organizers",     ()),
    ("GET",   re.compile(r"^/admin/organizers/(?P<id>[\w-]+)$"),           "admin_get_organizer",       ("id",)),
    ("PATCH", re.compile(r"^/admin/organizers/(?P<id>[\w-]+)$"),           "admin_patch_organizer",     ("id",)),
    ("GET",   re.compile(r"^/admin/stats/overview$"),                     "admin_stats_overview",      ()),
    ("GET",   re.compile(r"^/admin/audit$"),                              "admin_list_audit",          ()),
    ("GET",   re.compile(r"^/admin/reports/(?P<type>[a-z]+)$"),            "admin_report",              ("type",)),
]


DISPATCH = {
    # Public
    "register":         handle_register,
    "get_citizen":      lambda e, id:    handle_get_citizen(e, id),
    "campaign_submit":  handle_campaign_submit,
    "list_campaigns":   handle_list_campaigns,
    "get_campaign":     lambda e, id:    handle_get_campaign(e, id),
    "get_organizer":    lambda e, id:    handle_get_organizer(e, id),
    "stats_locality":   handle_stats_locality,
    "stats_map":        handle_stats_map,
    "list_counties":    handle_list_counties,
    "list_localities":  lambda e, code:  handle_list_localities(e, code),
    "get_manage_token": lambda e, token: handle_get_manage_token(e, token),
    "unsubscribe_m":    lambda e, token: handle_unsubscribe(e, token, "citizen_manage"),
    "unsubscribe_r":    lambda e, token: handle_unsubscribe(e, token, "citizen_refresh"),
    "erase":            lambda e, token: handle_erase(e, token),
    "refresh_confirm":  lambda e, token: handle_refresh_confirm(e, token),

    # Admin
    "admin_list_campaigns":      handle_admin_list_campaigns,
    "admin_get_campaign":        lambda e, id: handle_admin_get_campaign(e, id),
    "admin_approve_campaign":    lambda e, id: handle_admin_approve_campaign(e, id),
    "admin_reject_campaign":     lambda e, id: handle_admin_reject_campaign(e, id),
    "admin_patch_campaign":      lambda e, id: handle_admin_patch_campaign(e, id),
    "admin_list_citizens":       handle_admin_list_citizens,
    "admin_get_citizen":         lambda e, id: handle_admin_get_citizen(e, id),
    "admin_patch_citizen":       lambda e, id: handle_admin_patch_citizen(e, id),
    "admin_unsubscribe_citizen": lambda e, id: handle_admin_unsubscribe_citizen(e, id),
    "admin_erase_citizen":       lambda e, id: handle_admin_erase_citizen(e, id),
    "admin_list_organizers":     handle_admin_list_organizers,
    "admin_get_organizer":       lambda e, id: handle_admin_get_organizer(e, id),
    "admin_patch_organizer":     lambda e, id: handle_admin_patch_organizer(e, id),
    "admin_stats_overview":      handle_admin_stats_overview,
    "admin_list_audit":          handle_admin_list_audit,
    "admin_report":              lambda e, t: handle_admin_report(e, t),
}


def lambda_handler(event, context):
    global _active_env

    method = (event.get("requestContext", {}).get("http", {}).get("method")
              or event.get("httpMethod"))
    path = event.get("rawPath") or event.get("path") or ""

    # Select environment from the incoming custom domain. Fail closed: an
    # unrecognized host is never defaulted to prod, so a misconfiguration
    # cannot silently route traffic at the wrong (prod) database.
    domain = (event.get("requestContext", {}) or {}).get("domainName", "")
    _active_env = DOMAIN_TO_ENV.get((domain or "").lower())
    if _active_env is None:
        log.warning("rejected unknown host", extra={"domain": domain})
        return {
            "statusCode": 403,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "unknown_host"}),
        }

    log.info("request", extra={"env": _active_env, "method": method, "path": path})

    if method == "OPTIONS":
        return respond(204)

    # Admin routes: the API Gateway Cognito JWT authorizer already validated the
    # token; here we enforce `admins` group membership and require an email claim
    # for the audit trail. Public routes (no /admin prefix) are unaffected.
    if path.startswith("/admin/") or path == "/admin":
        claims = _claims(event)
        email = claims.get("email")
        if not email or "admins" not in _groups(claims):
            log.warning("admin authz denied", extra={"env": _active_env, "path": path})
            return err(403, "forbidden", "Admin access required.")

    for route_method, pattern, name, arg_names in ROUTES:
        if route_method != method:
            continue
        m = pattern.match(path)
        if not m:
            continue
        args = [m.group(n) for n in arg_names]
        return DISPATCH[name](event, *args)

    return err(404, "route_not_found", f"{method} {path}")

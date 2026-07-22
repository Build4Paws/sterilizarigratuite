"""Environment config, per-environment selection, shared constants."""
import os
import re
import logging
from typing import Optional

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

# SMS (messengeros). Empty API key = SMS disabled (no-op), so this is safe to
# deploy before egress/keys are in place. messengeros is a third-party host, so
# sending needs real Lambda internet egress (NAT) — an SES VPC endpoint won't do.
MESSENGEROS_API_KEY = os.environ.get("MESSENGEROS_API_KEY")
MESSENGEROS_DELIVERY_PROVIDER = os.environ.get("MESSENGEROS_DELIVERY_PROVIDER")
MESSENGEROS_PROJECT = os.environ.get("MESSENGEROS_PROJECT")  # optional
MESSENGEROS_SMS_URL = os.environ.get("MESSENGEROS_SMS_URL", "https://inbound.messengeros.com/2.0/send")

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
    "api.sterilizari-gratuite.ro":     "prod",
    "dev.api.sterilizari-gratuite.ro": "dev",
    # Add the raw execute-api host here (mapped to "dev") if you want to test
    # via the d-xxxx.execute-api.* URL, which otherwise fails closed with 403.
}

# Request-scoped: set once per invocation in lambda_handler. Safe as a module
# global because a Lambda execution environment processes one event at a time.
_active_env: Optional[str] = None


def set_active_env(env):
    global _active_env
    _active_env = env


def current_env():
    return _active_env


def current_origin():
    """Allowed origin / public site URL for the active environment."""
    return ENVIRONMENTS[_active_env]["origin"]

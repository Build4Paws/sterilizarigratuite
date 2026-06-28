"""
Router + Lambda entry. Maps (method, path) → handler, selects the environment
from the request domain (fail-closed), and enforces the admin auth gate.

Route map (see the handler modules for behavior):
  Public:     /register, /campaigns(/submit|/{id}), /organizer/{id},
              /stats/{locality,map}, /counties(/{code}/localities)
  Magic-link: /m/{token}(/unsubscribe|/erase), /r/{token}(/confirm|/unsubscribe)
  Admin:      /admin/campaigns**, /admin/citizens**, /admin/organizers**,
              /admin/stats/overview, /admin/audit, /admin/reports/{type}
"""
import json
import re

from . import admin
from . import public_handlers as ph
from . import reports
from .config import DOMAIN_TO_ENV, log, set_active_env
from .helpers import err, respond

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
    "register":         ph.handle_register,
    "get_citizen":      lambda e, id:    ph.handle_get_citizen(e, id),
    "campaign_submit":  ph.handle_campaign_submit,
    "list_campaigns":   ph.handle_list_campaigns,
    "get_campaign":     lambda e, id:    ph.handle_get_campaign(e, id),
    "get_organizer":    lambda e, id:    ph.handle_get_organizer(e, id),
    "stats_locality":   ph.handle_stats_locality,
    "stats_map":        ph.handle_stats_map,
    "list_counties":    ph.handle_list_counties,
    "list_localities":  lambda e, code:  ph.handle_list_localities(e, code),
    "get_manage_token": lambda e, token: ph.handle_get_manage_token(e, token),
    "unsubscribe_m":    lambda e, token: ph.handle_unsubscribe(e, token, "citizen_manage"),
    "unsubscribe_r":    lambda e, token: ph.handle_unsubscribe(e, token, "citizen_refresh"),
    "erase":            lambda e, token: ph.handle_erase(e, token),
    "refresh_confirm":  lambda e, token: ph.handle_refresh_confirm(e, token),

    # Admin
    "admin_list_campaigns":      admin.handle_admin_list_campaigns,
    "admin_get_campaign":        lambda e, id: admin.handle_admin_get_campaign(e, id),
    "admin_approve_campaign":    lambda e, id: admin.handle_admin_approve_campaign(e, id),
    "admin_reject_campaign":     lambda e, id: admin.handle_admin_reject_campaign(e, id),
    "admin_patch_campaign":      lambda e, id: admin.handle_admin_patch_campaign(e, id),
    "admin_list_citizens":       admin.handle_admin_list_citizens,
    "admin_get_citizen":         lambda e, id: admin.handle_admin_get_citizen(e, id),
    "admin_patch_citizen":       lambda e, id: admin.handle_admin_patch_citizen(e, id),
    "admin_unsubscribe_citizen": lambda e, id: admin.handle_admin_unsubscribe_citizen(e, id),
    "admin_erase_citizen":       lambda e, id: admin.handle_admin_erase_citizen(e, id),
    "admin_list_organizers":     admin.handle_admin_list_organizers,
    "admin_get_organizer":       lambda e, id: admin.handle_admin_get_organizer(e, id),
    "admin_patch_organizer":     lambda e, id: admin.handle_admin_patch_organizer(e, id),
    "admin_stats_overview":      admin.handle_admin_stats_overview,
    "admin_list_audit":          admin.handle_admin_list_audit,
    "admin_report":              lambda e, t: reports.handle_admin_report(e, t),
}


def lambda_handler(event, context):
    # Scheduled (EventBridge) invocation: no HTTP request context. Drain the
    # quiet-hours citizen-alert queue instead of routing an HTTP request. The
    # drainer scopes itself per-environment (the scheduled event carries no
    # domain), so we don't set_active_env here.
    if event.get("source") == "aws.events" or event.get("detail-type") == "Scheduled Event":
        from .notifications import drain_pending_alerts
        log.info("scheduled drain tick")
        return {"ok": True, "drained": drain_pending_alerts()}

    method = (event.get("requestContext", {}).get("http", {}).get("method")
              or event.get("httpMethod"))
    path = event.get("rawPath") or event.get("path") or ""

    # Select environment from the incoming custom domain. Fail closed: an
    # unrecognized host is never defaulted to prod, so a misconfiguration
    # cannot silently route traffic at the wrong (prod) database.
    domain = (event.get("requestContext", {}) or {}).get("domainName", "")
    env_key = DOMAIN_TO_ENV.get((domain or "").lower())
    set_active_env(env_key)
    if env_key is None:
        log.warning("rejected unknown host", extra={"domain": domain})
        return {
            "statusCode": 403,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "unknown_host"}),
        }

    log.info("request", extra={"env": env_key, "method": method, "path": path})

    if method == "OPTIONS":
        return respond(204)

    # Admin routes: the API Gateway Cognito JWT authorizer already validated the
    # token; here we enforce `admins` group membership and require an email claim
    # for the audit trail. Public routes (no /admin prefix) are unaffected.
    if path.startswith("/admin/") or path == "/admin":
        claims = admin._claims(event)
        email = claims.get("email")
        if not email or "admins" not in admin._groups(claims):
            log.warning("admin authz denied", extra={"env": env_key, "path": path})
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

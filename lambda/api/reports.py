"""Admin CSV report handlers."""
import re
from datetime import datetime, timezone

from .config import COUNTY_RE, log
from .helpers import _cors_headers, err, client_ip, client_ua, get_conn, audit
from .admin import admin_email


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


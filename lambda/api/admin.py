"""Admin auth helpers + admin route handlers."""
import json
import re
from typing import Optional
from uuid import UUID

from .config import (
    CAMPAIGN_STATUSES, CITIZEN_STATUSES, COUNTY_RE, DEFAULT_LIMIT, MAX_LIMIT,
    current_origin, log,
)
from .helpers import (
    respond, err, client_ip, client_ua, get_conn, audit,
    fetch_campaign_email_payload, send_campaign_email, send_citizen_email,
)


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
            # Queue the citizen alert (alert_status='pending'). The fan-out is NOT
            # done here: approval can happen during quiet hours, so the scheduled
            # drainer (api/notifications.py) dispatches it inside the allowed send
            # window, applying the SMS-preferred channel rule.
            cur.execute("""UPDATE campaigns SET status='approved', reviewed_at=now(),
                           reviewed_by=%s, alert_status='pending' WHERE id=%s
                           RETURNING reviewed_at""", (actor, row["id"]))
            reviewed_at = cur.fetchone()["reviewed_at"]
            audit(cur, actor=actor, action="campaign.approve", entity_type="campaign",
                  entity_id=row["id"], ip=ip, ua=ua)
            # Read the email payload while still in the transaction; send after commit.
            email_payload = fetch_campaign_email_payload(cur, row["id"])

        # Transaction committed. Tell the organizer immediately — this is
        # transactional and is NOT subject to quiet hours. Best-effort (never raises).
        if email_payload:
            send_campaign_email(
                "approved",
                to_email=email_payload["contact_email"],
                organization_name=email_payload["organization_name"],
                campaign_public_id=str(email_payload["campaign_public_id"]),
                organizer_public_id=str(email_payload["organizer_public_id"]),
                site_url=current_origin(),
                details=email_payload,
            )
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
                site_url=current_origin(),
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



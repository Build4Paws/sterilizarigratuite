"""Public + magic-link route handlers."""
import json
import re
from datetime import timedelta
from uuid import UUID

import psycopg
from pydantic import ValidationError

from .config import current_origin, log
from .helpers import (
    respond, err, client_ip, client_ua, get_conn,
    verify_turnstile, normalize_phone, resolve_locality,
    audit, issue_token, _load_token, _citizen_manage_url,
    send_campaign_email, send_citizen_email,
    send_citizen_sms,
)
from .models import CitizenRegistration, CampaignSubmission, pydantic_errors_to_response


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

        # Confirmation (best-effort, per channel the citizen gave). Email if an
        # email exists; SMS if a phone exists — so phone-only registrants, who
        # previously got nothing, are now confirmed too.
        send_citizen_email(
            "registered",
            to_email=reg.email,
            name=reg.name,
            locality=reg.locality,
            manage_url=_citizen_manage_url(manage_token),
        )
        send_citizen_sms("registered", to_phone=reg.phone)

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
            site_url=current_origin(),
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
            # The long-lived manage link (citizen_manage) is a reusable account
            # credential — DON'T consume it here, or a citizen who unsubscribes
            # now can't come back later to erase (or re-manage). Only the one-time
            # refresh link (citizen_refresh, from the /r/ post-campaign flow) is
            # spent on use. The manage link dies only on erase (tokens revoked) or
            # at its 365-day expiry.
            if token_kind != "citizen_manage":
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



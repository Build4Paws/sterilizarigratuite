"""
Citizen campaign-alert fan-out + the scheduled (quiet-hours) drainer.

Approving a campaign does NOT alert citizens inline — approvals can land at any
hour. Instead the approve handler queues the alert by setting
`campaigns.alert_status = 'pending'`. A scheduled EventBridge tick invokes this
function's `drain_pending_alerts`, which dispatches pending alerts but ONLY
inside the allowed send window (see `within_send_window`). Outside the window it
is a no-op and retries on the next tick.

Channel rule (SMS-preferred): a citizen with a phone gets SMS only; email goes
only to citizens WITHOUT a phone. So each citizen receives at most one message.

Idempotency: the row is flagged 'sent' inside the transaction and the actual
sends happen AFTER commit. This favors no-spam (a crash mid-dispatch won't
re-blast on the next tick) over guaranteed delivery — consistent with the
best-effort philosophy of every send path in this codebase.
"""
from datetime import timedelta
from typing import Optional

from .config import ENVIRONMENTS, current_origin, log, set_active_env
from .helpers import (
    get_conn, issue_token, fetch_campaign_email_payload,
    send_citizen_email, send_citizens_sms_batch, _citizen_manage_url,
    within_send_window,
)


def _collect_campaign_alert(cur, campaign_internal_id: int) -> Optional[tuple]:
    """Inside a transaction: gather recipients (SMS-preferred) and mint a
    per-recipient manage token for each email recipient (so each alert carries a
    working unsubscribe link — raw tokens aren't recoverable). Returns
    (payload, email_recipients, sms_phones) to send AFTER commit, or None if the
    campaign payload can't be loaded."""
    payload = fetch_campaign_email_payload(cur, campaign_internal_id)
    if not payload:
        return None

    # SMS recipients: active, phone present, in the campaign's locality.
    cur.execute(
        """SELECT phone FROM citizens
           WHERE status = 'active' AND phone IS NOT NULL AND locality_id = %s""",
        (payload["locality_id"],),
    )
    sms_phones = [r["phone"] for r in cur.fetchall()]

    # Email recipients: active, NO phone (SMS-preferred), email present, same
    # locality. The `phone IS NULL` is what makes the channels mutually exclusive.
    cur.execute(
        """SELECT id, email FROM citizens
           WHERE status = 'active' AND phone IS NULL AND email IS NOT NULL
             AND locality_id = %s""",
        (payload["locality_id"],),
    )
    email_recipients = []
    for cz in cur.fetchall():
        tok = issue_token(cur, kind="citizen_manage",
                          citizen_id=cz["id"], ttl=timedelta(days=365))
        email_recipients.append((cz["email"], tok))

    return payload, email_recipients, sms_phones


def _send_campaign_alert(payload: dict, email_recipients: list, sms_phones: list) -> None:
    """After-commit best-effort sends. Never raises."""
    site = current_origin()
    campaign_url = f"{site}/campanie/{payload['campaign_public_id']}"

    for cz_email, cz_tok in email_recipients:
        send_citizen_email(
            "campaign_alert",
            to_email=cz_email,
            locality=payload["locality"],
            organization_name=payload["organization_name"],
            details=payload,
            campaign_url=campaign_url,
            manage_url=_citizen_manage_url(cz_tok),
        )

    send_citizens_sms_batch(
        "campaign_alert",
        phones=sms_phones,
        locality=payload["locality"],
        organization_name=payload["organization_name"],
        campaign_url=campaign_url,
    )
    log.info("campaign alert dispatched",
             extra={"emails": len(email_recipients), "sms": len(sms_phones)})


def drain_pending_alerts() -> dict:
    """Scheduled entrypoint. For EACH environment (the scheduled event is not
    domain-scoped, so we can't infer prod/dev from a request), if inside the
    send window, dispatch every campaign with alert_status='pending'."""
    summary = {}
    for env in ENVIRONMENTS:
        set_active_env(env)
        if not within_send_window():
            log.info("outside send window; deferring", extra={"env": env})
            summary[env] = "deferred"
            continue

        conn = get_conn()
        # Read candidate ids in autocommit (each gets its own short locked txn
        # below). FOR UPDATE SKIP LOCKED on the per-campaign re-check makes this
        # safe against overlapping ticks.
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id FROM campaigns
                   WHERE status = 'approved' AND alert_status = 'pending'"""
            )
            ids = [r["id"] for r in cur.fetchall()]

        sent = 0
        for cid in ids:
            to_send = None
            with conn.transaction(), conn.cursor() as cur:
                # Re-lock and re-check: another tick may have grabbed it.
                cur.execute(
                    """SELECT 1 FROM campaigns
                       WHERE id = %s AND alert_status = 'pending'
                       FOR UPDATE SKIP LOCKED""",
                    (cid,),
                )
                if not cur.fetchone():
                    continue
                to_send = _collect_campaign_alert(cur, cid)
                cur.execute(
                    "UPDATE campaigns SET alert_status = 'sent', alert_sent_at = now() WHERE id = %s",
                    (cid,),
                )
            # Committed: now send (best-effort, outside the transaction).
            if to_send:
                _send_campaign_alert(*to_send)
            sent += 1

        log.info("drain complete", extra={"env": env, "campaigns": sent})
        summary[env] = sent

    return summary

-- Migration: quiet-hours queue for citizen campaign alerts (lightweight option).
--
-- Why: approving a campaign must not blast SMS/email to citizens at night.
-- Approval now only QUEUES the alert (alert_status='pending'); a scheduled
-- drainer (api/notifications.py, invoked by EventBridge) dispatches it inside
-- the allowed send window and sets alert_status='sent'. Recipients are
-- re-derived at send time, so citizens who register between approval and the
-- next in-window tick are alerted too.
--
-- Channel rule lives in code (SMS-preferred); these columns are just the queue.
--
-- Values: NULL  = legacy / not queued (pre-existing approved campaigns are NULL,
--                  so the drainer never re-alerts them)
--         'pending' = approved, awaiting in-window dispatch
--         'sent'    = dispatched (best-effort) by the drainer
--
-- Apply on BOTH dev and prod (run from a host that can reach the DB, e.g. the
-- EC2 box). Idempotent: IF NOT EXISTS guards re-runs.

ALTER TABLE campaigns
  ADD COLUMN IF NOT EXISTS alert_status  text,
  ADD COLUMN IF NOT EXISTS alert_sent_at timestamptz;

-- Drainer scans for pending rows; keep that scan cheap.
CREATE INDEX IF NOT EXISTS idx_campaigns_alert_pending
  ON campaigns (id) WHERE alert_status = 'pending';

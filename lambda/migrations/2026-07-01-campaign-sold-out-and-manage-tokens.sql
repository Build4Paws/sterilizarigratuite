-- Migration: "Sold Out" flow — organizer-managed registration stop.
--
-- Adds:
--   1. campaigns.sold_out — the flag the organizer sets from their campaign
--      management magic link. A sold-out campaign stays status='approved' so it
--      REMAINS visible in v_public_campaigns (approved + upcoming); the frontend
--      hides the public phone and shows "⛔ Locuri ocupate. Mulțumim!" instead.
--      Because the campaign stays 'approved', the view needs no change — the read
--      handlers just expose c.sold_out alongside the view (JOIN on public_id).
--
--   2. tokens.campaign_id — lets a token reference a specific campaign, so the
--      approval email can carry a per-campaign management link (kind
--      'campaign_manage'). The tokens table already had citizen_id + organizer_id;
--      the management token sets BOTH organizer_id and campaign_id.
--
--   3. token_kind enum — the management tokens use new kind values. Postgres
--      rejects an unknown enum value at INSERT time, so these MUST be added or
--      the approval flow (which mints a 'campaign_manage' token) fails and rolls
--      back. ADD VALUE cannot be USED in the same transaction that adds it, so
--      run this file via psql (autocommit) rather than inside a BEGIN/COMMIT.
--
-- Apply on BOTH dev and prod databases (run from a host that can reach RDS, e.g.
-- the EC2 box) BEFORE deploying the Lambda that reads these columns. Idempotent.

ALTER TYPE token_kind ADD VALUE IF NOT EXISTS 'citizen_manage';
ALTER TYPE token_kind ADD VALUE IF NOT EXISTS 'campaign_manage';

ALTER TABLE campaigns
  ADD COLUMN IF NOT EXISTS sold_out boolean NOT NULL DEFAULT false;

ALTER TABLE tokens
  ADD COLUMN IF NOT EXISTS campaign_id bigint REFERENCES campaigns(id);

CREATE INDEX IF NOT EXISTS tokens_campaign_id_idx ON tokens(campaign_id);

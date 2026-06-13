-- Migration: let GDPR-erased citizens have NULL phone AND email.
--
-- Why: handle_erase (magic-link) and handle_admin_erase_citizen anonymize a row
-- by nulling phone, phone_normalized and email and setting status='deleted'.
-- The original CHECK constraint `citizens_phone_or_email` required phone OR email
-- on EVERY row, so the erase failed with:
--     psycopg.errors.CheckViolation:
--     new row for relation "citizens" violates check constraint "citizens_phone_or_email"
--
-- Fix: exempt deleted rows from the requirement — mirroring how the existing
-- gdpr_consent check is "TRUE unless deleted". Active/pending rows still must
-- have at least one contact channel. The partial unique indexes already exclude
-- deleted rows, so nulling is safe.
--
-- Apply on BOTH the dev and prod databases (run from a host that can reach RDS,
-- e.g. the EC2 box). Idempotent-ish: re-running the DROP errors if already
-- dropped — guard with the DO block below if you want to re-run safely.

ALTER TABLE citizens DROP CONSTRAINT IF EXISTS citizens_phone_or_email;

ALTER TABLE citizens
  ADD CONSTRAINT citizens_phone_or_email
  CHECK (status = 'deleted' OR phone IS NOT NULL OR email IS NOT NULL);

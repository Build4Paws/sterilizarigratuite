# Backend DB Schema (PostgreSQL)

> Canonical entity model from the backend team. Paste the block below into
> [dbdiagram.io](https://dbdiagram.io) to visualise. The frontend never touches
> the DB — this exists for **entity alignment** so our types and API mapping
> stay consistent with how the backend thinks about the domain.
> See `BACKEND-API.md` for the HTTP contract and `API-WIRING-PLAN.md` for wiring.

## Frontend-relevant notes (read first)

- **`counties`** carries `code` (2-letter auto), `name`, `name_simple`
  (diacritic-stripped), `slug`, `siruta_code`. Our local `judete.json` mirrors
  `code`/`name`/`slug`; we keep counties local (see plan) and source
  **localities** from `GET /counties/{code}/localities`.
- **`localities`** have a numeric `id` + `name`. The API returns `{ id, name }`,
  but citizen/campaign POSTs still send `locality` as the **name string** — the
  backend resolves it to `locality_id`. Don't switch the payload to ids.
- **`species`** is a reference table (`dog`/`cat`). Per-citizen counts live in
  `citizen_species.animal_count` (→ `dogCount`/`catCount`). Per-campaign slots
  live in `campaign_species.slots` — which is why `PublicCampaign.species` is an
  **object of slot counts** `{ dog: 20, cat: 30 }`, not an array.
- **`citizens.public_id`** = API `citizenId`. **`campaigns.public_id`** = API
  `submissionId`. Always the UUID, never the bigserial `id`.
- **`citizen_status`** = `pending_confirm | active | unsubscribed | deleted`;
  **`campaign_status`** = `pending | approved | rejected | cancelled | finished`.
  `/campaigns` only ever returns `approved` + upcoming, so the frontend doesn't
  need to branch on status for the public list.
- **`tokens`** (sha256, single-use, `citizen_manage`/`citizen_refresh`/
  `organizer_manage`) back the `/m` + `/r` magic-link flows — **deferred** on the
  frontend for now.
- `notifications` + `audit_log` are ops/GDPR tables — no frontend surface.

## dbdiagram source

```dbml
Project sterilizarigratuite {
  database_type: 'PostgreSQL'
  Note: 'Build4Paws — free animal sterilization campaigns platform (RO)'
}

// 1. Reference data
Table counties {
  code         char(2)  [pk, note: '2-letter auto code: AB, SV, IF…']
  name         text     [not null, unique, note: '"Alba", "București"']
  name_simple  text     [not null, note: 'diacritic-stripped: "alba"']
  slug         text     [not null, unique, note: 'URL slug: "bistrita-nasaud"']
  siruta_code  int      [unique]
}

Table localities {
  id           bigserial [pk]
  county_code  char(2)   [not null, ref: > counties.code]
  name         text      [not null]
  name_simple  text      [not null]
  siruta_code  int       [unique]
  latitude     "numeric(9,6)" [note: 'for future map view']
  longitude    "numeric(9,6)"

  indexes {
    (county_code, name) [unique]
    county_code
  }
}

Table species {
  code  text [pk, note: "'dog', 'cat'"]
  label text [not null, note: "'Câine', 'Pisică'"]
}

// 2. Citizens — notification subscribers
Enum citizen_status {
  pending_confirm
  active
  unsubscribed
  deleted [note: 'GDPR-erased; PII nulled, row kept for audit']
}

Table citizens {
  id                bigserial      [pk]
  public_id         uuid           [not null, unique, default: `gen_random_uuid()`]
  name              text           [not null]
  phone             text           [note: 'canonical +40712345678']
  phone_normalized  text           [note: 'digits-only for dedupe']
  email             citext
  county_code       char(2)        [not null, ref: > counties.code]
  locality_id       bigint         [not null, ref: > localities.id]
  gdpr_consent      boolean        [not null]
  gdpr_consent_at   timestamptz    [not null, default: `now()`]
  gdpr_consent_ip   inet
  gdpr_consent_ua   text
  status            citizen_status [not null, default: 'active']
  notes             text           [note: 'internal admin notes — no PII']
  created_at        timestamptz    [not null, default: `now()`]
  updated_at        timestamptz    [not null, default: `now()`]
  unsubscribed_at   timestamptz
  deleted_at        timestamptz

  indexes {
    (phone_normalized, locality_id) [unique, name: 'uq_citizens_phone_active', note: 'partial: status IN (active, pending_confirm)']
    (email, locality_id)            [unique, name: 'uq_citizens_email_active', note: 'partial: status IN (active, pending_confirm)']
    locality_id [note: 'partial: status = active']
    county_code [note: 'partial: status = active']
  }

  Note: 'CHECK: phone OR email required UNLESS deleted (erased rows are anonymized). CHECK: gdpr_consent = TRUE unless deleted.'
}

Table citizen_species {
  citizen_id   bigint [ref: > citizens.id]
  species_code text   [ref: > species.code]
  animal_count int    [note: 'optional "I have 2 cats" hint']

  indexes {
    (citizen_id, species_code) [pk]
  }
}

// 3. Organizers (NGOs / city halls)
Table organizers {
  id                       bigserial   [pk]
  public_id                uuid        [not null, unique, default: `gen_random_uuid()`]
  name                     text        [not null, note: '"ONG Patrupede" / "Primăria Bosanci"']
  contact_email            citext      [not null, unique, note: 'private — internal contact']
  contact_phone            text        [not null]
  contact_phone_normalized text        [not null]
  notes                    text
  created_at               timestamptz [not null, default: `now()`]
  updated_at               timestamptz [not null, default: `now()`]

  indexes {
    contact_phone_normalized
  }
}

// 4. Campaigns
Enum campaign_status {
  pending   [note: 'awaiting admin review']
  approved  [note: 'visible on /campanii']
  rejected
  cancelled
  finished  [note: 'end date passed']
}

Table campaigns {
  id               bigserial       [pk]
  public_id        uuid            [not null, unique, default: `gen_random_uuid()`, note: '"submissionId" in API']
  organizer_id     bigint          [not null, ref: > organizers.id]
  phone_public     text            [not null, note: 'shown on the campaign card']
  county_code      char(2)         [not null, ref: > counties.code]
  locality_id      bigint          [not null, ref: > localities.id]
  address          text            [not null]
  date_start       date            [not null]
  date_end         date            [note: 'NULL = single-day; else >= date_start']
  time_start       time            [not null]
  time_end         time            [not null]
  doctor           text            [note: 'optional vet name']
  status           campaign_status [not null, default: 'pending']
  gdpr_consent     boolean         [not null]
  submitted_ip     inet
  submitted_ua     text
  reviewed_at      timestamptz
  reviewed_by      text            [note: 'admin email; v2 → FK to admins table']
  rejection_reason text
  created_at       timestamptz     [not null, default: `now()`]
  updated_at       timestamptz     [not null, default: `now()`]

  indexes {
    (locality_id, date_start, organizer_id) [unique, name: 'uq_campaigns_dedupe', note: 'partial: status IN (pending, approved)']
    (status, date_end, date_start)          [name: 'idx_public_listing', note: 'partial: status = approved']
    (county_code, status)
    locality_id
  }

  Note: 'CHECK: date_end IS NULL OR date_end >= date_start. CHECK: single-day → time_end > time_start.'
}

Table campaign_species {
  campaign_id  bigint [ref: > campaigns.id]
  species_code text   [ref: > species.code]
  slots        int    [not null, note: 'CHECK slots > 0']

  indexes {
    (campaign_id, species_code) [pk]
  }
}

// 5. Magic-link tokens (/m/[token], /r/[token])
Enum token_kind {
  citizen_manage   [note: '/m/[token] — unsubscribe / GDPR erase']
  citizen_refresh  [note: '/r/[token] — keep on list post-campaign']
  organizer_manage [note: 'v2 — organizer dashboard']
}

Table tokens {
  id           bigserial   [pk]
  token_hash   bytea       [not null, unique, note: 'sha256(token) — never store raw']
  kind         token_kind  [not null]
  citizen_id   bigint      [ref: > citizens.id, note: 'exactly one subject set']
  organizer_id bigint      [ref: > organizers.id]
  issued_at    timestamptz [not null, default: `now()`]
  expires_at   timestamptz [not null]
  used_at      timestamptz [note: 'single-use: set on first use']
  revoked_at   timestamptz

  indexes {
    citizen_id   [note: 'partial: citizen_id NOT NULL']
    organizer_id [note: 'partial: organizer_id NOT NULL']
    expires_at   [note: 'partial: not yet used or revoked']
  }

  Note: 'CHECK: exactly one of citizen_id / organizer_id is set.'
}

// 6. Notifications log (SMS / email)
Enum notification_channel { sms email }
Enum notification_status { queued sent delivered failed bounced }

Table notifications {
  id              bigserial            [pk]
  citizen_id      bigint               [not null, ref: > citizens.id]
  campaign_id     bigint               [ref: > campaigns.id]
  channel         notification_channel [not null]
  status          notification_status  [not null, default: 'queued']
  provider_msg_id text                 [note: 'external ID from SES/SNS/Twilio']
  error_message   text
  queued_at       timestamptz          [not null, default: `now()`]
  sent_at         timestamptz
  delivered_at    timestamptz

  indexes {
    citizen_id
    campaign_id
    (status, queued_at) [note: 'partial: status = queued (worker poll)']
  }
}

// 7. Audit log — GDPR Art. 30 + admin actions
Table audit_log {
  id          bigserial   [pk]
  occurred_at timestamptz [not null, default: `now()`]
  actor       text        [note: 'admin email, "system", or "self"']
  action      text        [not null, note: '"citizen.register", "campaign.approve"…']
  entity_type text        [not null, note: '"citizen", "campaign", "organizer", "token"']
  entity_id   bigint
  ip_address  inet
  user_agent  text
  metadata    jsonb       [note: 'before/after diff, error codes, etc.']

  indexes {
    (entity_type, entity_id)
    occurred_at
  }
}

TableGroup reference { counties localities species }
TableGroup citizen_flow { citizens citizen_species }
TableGroup organizer_flow { organizers campaigns campaign_species }
TableGroup auth { tokens }
TableGroup ops { notifications audit_log }
```

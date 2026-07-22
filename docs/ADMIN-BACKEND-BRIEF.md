# Admin backend endpoints — brief for implementation

> Paste-ready brief to hand to an assistant (or the backend team) to implement
> the `/admin/**` Lambda endpoints. Self-contained: assumes no repo access.
> Companion to `ADMIN-PLAN.md` (design) and `BACKEND-API.md` (public contract).

---

## Context

Build4Paws — a platform matching Romanian citizens with free animal-sterilization
campaigns. Stack: **AWS API Gateway → Lambda → PostgreSQL** (region `eu-central-1`).
The public API already exists (`/register`, `/campaigns`, `/campaigns/submit`,
`/stats/*`, `/counties/*`). We now need an **authenticated admin API** under
`/admin/**` for staff to moderate campaigns, browse citizens (PII), manage
organizers, and view a dashboard + audit log.

A Nuxt frontend already proxies these: it sends each request to
`https://api.sterilizari-gratuite.ro/admin/...` with header
`Authorization: Bearer <Cognito idToken>`, and expects the **exact JSON shapes
below** (camelCase). Match them precisely.

## Auth

- An **Amazon Cognito User Pool** exists (`eu-central-1`), invite-only, with a
  group **`admins`** and TOTP MFA. App client uses a secret (handled by the frontend).
- Put a **Cognito User Pool authorizer** on every `/admin/**` route (the public
  routes keep their existing AWS_IAM/SigV4 auth — don't change those).
- From the validated JWT, read the **`email`** and **`cognito:groups`** claims.
  Reject if `admins` ∉ groups (403). Use `email` as `campaigns.reviewed_by` and as
  the `audit_log.actor` on every write.

## Database (relevant tables)

`campaigns` (public_id uuid = "submissionId", organizer_id, phone_public,
county_code, locality_id, address, date_start, date_end?, time_start, time_end,
doctor?, status [pending|approved|rejected|cancelled|finished], reviewed_at?,
reviewed_by?, rejection_reason?, submitted_ip?, submitted_ua?, created_at).
`campaign_species`(campaign_id, species_code, slots).
`citizens`(public_id uuid = "citizenId", name, phone?, phone_normalized?, email?,
county_code, locality_id, gdpr_consent_at, status [pending_confirm|active|
unsubscribed|deleted], notes?, created_at, unsubscribed_at?, deleted_at?).
`citizen_species`(citizen_id, species_code, animal_count?).
`organizers`(public_id uuid = "organizerId", name, contact_email, contact_phone,
notes?, created_at). `counties`(code, name). `localities`(id, name).
`species`(code [dog|cat], label). `audit_log`(occurred_at, actor, action,
entity_type, entity_id, ip_address, user_agent, metadata jsonb). `tokens`(...).

## Cross-cutting rules

- **IDs in all paths are the `public_id` UUID**, never the bigserial `id`.
- Timestamps: ISO-8601 UTC. Dates: `YYYY-MM-DD`. Times: `HH:MM`.
- **Pagination**: `?page=` (1-based) + `?limit=` (default 50). List responses
  return `total` (count before paging).
- **Every mutation writes `audit_log`**: actor=email claim, action (e.g.
  `campaign.approve`), entity_type, entity_id (bigserial), ip_address +
  user_agent from the request context, metadata jsonb (e.g. `{reason}` or before/after).
- **Error body**: `{ "error": "<code>", "message"?: "..." }`. Codes:
  `validation_failed` (400), `invalid_id` (400), `not_found` (404),
  `invalid_state` (409, e.g. approving a non-pending campaign), `internal_error` (500).
- County code → name via `counties`; locality id → name via `localities`;
  species slots/counts → `{ dog?: n, cat?: n }` objects.

---

## Endpoints

### Campaigns

**GET `/admin/campaigns`** — `?status=&county=&q=&page=&limit=` (all filters optional;
`q` matches organizer name/locality). →
```jsonc
{ "campaigns": [ {
  "submissionId": "uuid", "organizationName": "…", "county": "SV",
  "countyName": "Suceava", "locality": "Bosanci", "dateStart": "2026-06-20",
  "dateEnd": "2026-06-21",            // or null (single day)
  "status": "pending",               // pending|approved|rejected|cancelled|finished
  "createdAt": "2026-06-01T09:12:00Z",
  "reviewedAt": null, "reviewedBy": null
} ], "total": 42 }
```

**GET `/admin/campaigns/{id}`** → the same fields **plus**:
```jsonc
{ "phonePublic": "+40…", "address": "…", "timeStart": "09:00", "timeEnd": "17:00",
  "doctor": null, "species": { "dog": 20, "cat": 30 },
  "contactEmail": "…", "contactPhone": "+40…",   // organizer private contact
  "rejectionReason": null, "submittedIp": "…", "submittedUa": "…" }
```

**POST `/admin/campaigns/{id}/approve`** — only valid when `status=pending` (else
409 `invalid_state`). Sets status=approved, reviewed_at=now, reviewed_by=email.
Audit `campaign.approve`. → `{ "status": "approved", "reviewedAt": "…", "reviewedBy": "…" }`

**POST `/admin/campaigns/{id}/reject`** — body `{ "reason": "string 1..500" }`.
Sets status=rejected, rejection_reason, reviewed_*. Audit `campaign.reject`
(metadata `{reason}`). → `{ "status": "rejected", "reviewedAt": "…", "reviewedBy": "…" }`

*(Optional, nice-to-have) **PATCH `/admin/campaigns/{id}`** — partial edit incl.
`status` for cancel/finish.*

### Citizens (PII — minimize)

**GET `/admin/citizens`** — `?status=&county=&locality=&q=&page=&limit=`.
**The list must NOT return raw phone/email** — only whether each channel exists:
```jsonc
{ "citizens": [ {
  "citizenId": "uuid", "name": "…", "countyName": "Suceava", "locality": "Bosanci",
  "status": "active",                          // pending_confirm|active|unsubscribed|deleted
  "channelMask": { "phone": true, "email": false },
  "createdAt": "2026-05-30T08:00:00Z"
} ], "total": 1243 }
```

**GET `/admin/citizens/{id}`** → list fields **plus** the actual PII. **Write an
audit entry `citizen.view`** to log PII access.
```jsonc
{ "phone": "+40…" /*|null*/, "email": "…" /*|null*/,
  "species": { "dog": 1, "cat": 2 }, "gdprConsentAt": "…", "notes": null }
```

**PATCH `/admin/citizens/{id}`** — body `{ "notes"?, "status"? }`. Audit.

**POST `/admin/citizens/{id}/unsubscribe`** — status=unsubscribed,
unsubscribed_at=now. Audit `citizen.unsubscribe`. → `{ "status": "unsubscribed" }`

**POST `/admin/citizens/{id}/erase`** — body `{ "reason": "…" }`. **GDPR Art. 17**:
null name/phone/phone_normalized/email, status=deleted, deleted_at=now, revoke the
citizen's tokens. Audit `citizen.erase` (metadata `{reason}`). → `{ "status": "deleted" }`

### Organizers

**GET `/admin/organizers`** — `?q=&page=&limit=`. →
```jsonc
{ "organizers": [ {
  "organizerId": "uuid", "name": "…", "contactEmail": "…", "contactPhone": "+40…",
  "campaignCount": 3, "createdAt": "…"
} ], "total": 12 }
```

**GET `/admin/organizers/{id}`** → organizer fields **plus** `{ "notes": null,
"campaigns": [ <AdminCampaign as in the campaigns list> ] }`.

*(Optional) **PATCH `/admin/organizers/{id}`** — edit contact/notes.*

### Dashboard

**GET `/admin/stats/overview`** →
```jsonc
{ "pendingCampaigns": 4,        // status=pending
  "approvedUpcoming": 17,       // status=approved AND not past (date_end>=today, or single-day date_start>=today)
  "citizensActive": 1243,       // status=active
  "registrationsToday": 12,     // citizens created today
  "byStatus": { "pending": 4, "approved": 17, "rejected": 2, "cancelled": 1, "finished": 23 } }
```

### Audit log

**GET `/admin/audit`** — `?entityType=&entityId=&action=&actor=&page=&limit=`
(filters optional; newest first). →
```jsonc
{ "entries": [ {
  "id": 6, "occurredAt": "2026-06-02T15:00:00Z", "actor": "admin@…",
  "action": "campaign.approve", "entityType": "campaign", "entityId": 3,
  "ipAddress": "10.0.0.1", "metadata": { "reason": "…" }   // metadata optional/null
} ], "total": 318 }
```

---

## Deliverables requested

1. API Gateway route definitions for all `/admin/**` above with the Cognito
   authorizer + `admins` group check.
2. Lambda handlers implementing each, with the exact response shapes.
3. SQL for the non-trivial reads (campaign list with county/locality/organizer
   joins; citizen list with channelMask + minimization; overview aggregates).
4. The shared audit-log write helper, called on every mutation.

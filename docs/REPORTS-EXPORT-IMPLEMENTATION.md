# Reports Export — backend implementation spec (`/admin/reports/**`)

> **Self-contained handoff doc.** You do not need the rest of the repo to do this
> task — everything you need (contract, schema, SQL, CSV rules, security) is in
> here. This implements the **only missing half** of the admin reports feature:
> four `GET /admin/reports/{type}` endpoints that return CSV downloads.
>
> The frontend is **already built and shipped** (a Rapoarte page + a Nuxt proxy
> route). It calls these endpoints and streams whatever you return straight to
> the browser as a file download. Until these endpoints exist, the frontend gets
> a 404. **Do not change the contract below** — the frontend depends on it
> verbatim.

---

## 1. Context

Build4Paws (`sterilizari-gratuite.ro`) connects Romanian citizens with free animal
sterilization campaigns. There is an internal admin area (Cognito-gated) where
operators moderate campaigns, manage citizen registrations, etc. The **Rapoarte**
("Reports") page lets an admin pick a dataset, apply filters, and download a CSV.

**Stack for this task:**
- AWS API Gateway → Lambda (**Node.js / TypeScript**) → **PostgreSQL** (RDS).
- Cognito User Pool authorizer; only the `admins` group may call `/admin/**`.
- These four endpoints sit alongside the existing `/admin/**` routes (campaigns,
  citizens, organizers, audit, stats) and follow the same auth + audit pattern.

**Security note (org policy):** these reports touch PII. The `citizens` report in
particular is a PII-access event. Read §6 before writing the queries — data
minimization and audit logging are non-negotiable, not nice-to-haves.

---

## 2. How the frontend calls you (don't break this)

The browser never talks to API Gateway directly. A Nuxt server route proxies it:

```
Browser ──GET /api/admin/reports/{type}?from&to&county&status──▶ Nuxt proxy
Nuxt proxy ──GET /admin/reports/{type}?{whitelisted qs}─────────▶ YOU (API GW + Lambda)
            (adds Authorization: Bearer <Cognito idToken>, Accept: text/csv)
```

The proxy:
- **Whitelists exactly four query keys** before forwarding: `from`, `to`,
  `county`, `status`. Anything else is dropped — you will never receive other
  params. Trim/treat them as optional strings.
- Forwards the admin's Cognito **idToken** as `Authorization: Bearer <jwt>`.
- Forwards your `Content-Type` and `Content-Disposition` headers **verbatim** to
  the browser, and sets `cache-control: no-store`.
- If you respond non-2xx, it expects either a JSON error body or plain text; it
  surfaces a generic Romanian error to the user. Prefer a JSON error body shaped
  `{ "error": "<code>" }` (see §7).

So: **return real CSV bytes with the right headers on success, and a JSON error
with an appropriate status on failure.** That's the whole integration surface.

---

## 3. Endpoints

All four: method `GET`, **Cognito authorizer + `admins` group required**, same as
every other `/admin/**` route.

| Path | Dataset | PII level |
|------|---------|-----------|
| `GET /admin/reports/campaigns`  | Campaign submissions            | low |
| `GET /admin/reports/citizens`   | Citizen registrations (minimized) | **HIGH — minimized, audited** |
| `GET /admin/reports/organizers` | Organizers (NGOs / city halls)  | medium (internal contacts) |
| `GET /admin/reports/activity`   | Audit-log activity              | internal |

### Shared query params (all optional)

| Param | Meaning |
|-------|---------|
| `from` | Inclusive start date `YYYY-MM-DD`. Filters on `created_at` (campaigns/citizens/organizers) or `occurred_at` (activity). |
| `to` | Inclusive end date `YYYY-MM-DD`. Inclusive means: include the whole `to` day — use `< (to + 1 day)` or `<= to 23:59:59.999`, **not** a bare `<= to` against a timestamp. |
| `county` | 2-letter county code, e.g. `CJ`, `SV`, `B`. Filters on `county_code`. **Ignored by `activity`** (audit rows have no county). |
| `status` | Lifecycle status. Used **only** by `campaigns` (`campaign_status`) and `citizens` (`citizen_status`). Ignored by `organizers` and `activity`. |

- **No pagination.** A report returns the **full filtered set**. (Admin volumes
  are small; if a future dataset gets large, stream rather than buffer — see §8.)
- Validate `from`/`to` are `YYYY-MM-DD` and `from <= to` if both present;
  otherwise `400 validation_failed`. Validate `status` against the allowed set
  for that report; an unknown status → `400 validation_failed`. An unknown
  `{type}` → `404 not_found` (the proxy also guards this, but defend in depth).
- Unknown/empty params are simply not applied (no filter).

---

## 4. Database schema (only the tables you need)

PostgreSQL. **Output IDs are always `public_id` (UUID), never the bigserial `id`.**

```sql
counties     ( code char(2) PK, name text, name_simple text, slug text, siruta_code int )
localities   ( id bigserial PK, county_code char(2), name text, ... )
organizers   ( id bigserial PK, public_id uuid, name text,
               contact_email citext, contact_phone text, ...,
               created_at timestamptz )
campaigns    ( id bigserial PK, public_id uuid, organizer_id bigint→organizers.id,
               county_code char(2), locality_id bigint→localities.id,
               date_start date, date_end date NULL,
               status campaign_status,  -- pending|approved|rejected|cancelled|finished
               reviewed_at timestamptz NULL, reviewed_by text NULL,  -- admin email
               created_at timestamptz )
citizens     ( id bigserial PK, public_id uuid, name text,
               phone text NULL, email citext NULL,
               county_code char(2), locality_id bigint→localities.id,
               status citizen_status,   -- pending_confirm|active|unsubscribed|deleted
               created_at timestamptz )
audit_log    ( id bigserial PK, occurred_at timestamptz, actor text NULL,
               action text, entity_type text, entity_id bigint NULL,
               ip_address inet NULL, user_agent text NULL, metadata jsonb NULL )
```

Useful joins: `campaigns.organizer_id → organizers.id`,
`campaigns.county_code → counties.code` (for `county_name`),
`citizens.county_code → counties.code`, `citizens.locality_id → localities.id`.

`organizers` has no `county_code` column. If the `county` filter is passed to the
organizers report, the simplest correct behavior is to **ignore it** (organizers
aren't county-scoped). Document that choice in a comment.

`campaign_count` for organizers = `COUNT(campaigns)` for that organizer (count
**all** statuses unless you have reason otherwise; note your choice in a comment).

---

## 5. CSV format (exact)

- **UTF-8 with a leading BOM** (`﻿`). Excel needs the BOM to render Romanian
  diacritics (ă, â, î, ș, ț) correctly. Do not omit it.
- **First row = header** (the exact `snake_case` column names listed below, in
  order).
- **RFC-4180 quoting:** quote any field containing a comma, double-quote, CR, or
  LF; escape embedded `"` as `""`. Always quoting every field is also fine and
  simpler. Use `\r\n` as the line terminator.
- **Dates** as ISO: `YYYY-MM-DD`, or `YYYY-MM-DD HH:MM` (UTC) where a time matters
  (timestamps like `created_at`, `occurred_at`, `reviewed_at`).
- **Empty values = empty string**, never the literal `null`/`NULL`.

### Columns per report (exact order)

**`campaigns`**
```
public_id, organization_name, county, county_name, locality, date_start,
date_end, status, created_at, reviewed_at, reviewed_by
```
- `organization_name` ← `organizers.name`; `county` ← `county_code`;
  `county_name` ← `counties.name`; `locality` ← `localities.name`.
- `date_end` empty for single-day campaigns. `reviewed_at`/`reviewed_by` empty
  when not yet reviewed.

**`citizens`** ⚠️ **minimized — NO raw phone/email**
```
public_id, name, county_name, locality, status, has_phone, has_email, created_at
```
- `has_phone` / `has_email`: the strings **`da`** (phone/email present) or
  **`nu`** (absent) — presence only, matching the admin list view. Raw contact
  details are **deliberately excluded**. Do not add `phone`/`email` columns.
- **Exclude `status = 'deleted'` citizens entirely** (PII already nulled per GDPR
  Art. 17 — never resurrect erased data in a report).

**`organizers`**
```
public_id, name, contact_email, contact_phone, campaign_count, created_at
```

**`activity`** (from `audit_log`)
```
occurred_at, actor, action, entity_type, entity_id, ip_address
```
- `actor` is the admin email / `"system"` / `"self"`; may be empty.
- `entity_id` here is the audit row's referenced bigint id (it's an internal
  reference in the ops log, acceptable to expose to admins). `ip_address` may be
  empty.

---

## 6. Security & GDPR — non-negotiable

1. **Cognito `admins` gate** on all four, identical to the other `/admin/**`
   endpoints. Reject anything else with `401`/`403`.
2. **Every export writes an `audit_log` row**, even successful `campaigns`/
   `organizers` exports, and **especially `citizens`** (this is the PII-access
   event the frontend cannot record):
   ```
   actor       = admin email from the Cognito claim (e.g. token `email` claim)
   action      = "report.export"
   entity_type = "report"
   entity_id   = NULL
   ip_address  = caller IP (from API GW request context)
   metadata    = { "type": "<campaigns|citizens|organizers|activity>",
                   "filters": { "from": ..., "to": ..., "county": ..., "status": ... },
                   "row_count": <n> }   -- include only the filters that were set
   ```
   Write the audit row on success (after you know `row_count`). If you stream
   (§8) and can't know the count up front, write it after the stream completes,
   or omit `row_count` — but **the audit row itself is mandatory**.
3. **Data minimization (GDPR / NIS2 — RO/BG/HU/PL):** the `citizens` report
   excludes raw phone/email **by design**. If a future requirement ever needs
   them, add a separate, explicitly-audited opt-in param (e.g.
   `?includeContact=true` logged in `metadata`) — **do not** widen the default
   columns.
4. **`deleted` citizens are never exported** (see §5).
5. **IDs in output are always `public_id` (UUID)** for campaigns/citizens/
   organizers — never the bigserial `id`. (The `activity` report's `entity_id` is
   the one documented exception, since it's an internal ops reference.)
6. **No secrets in logs.** Don't log the JWT, DB connection string, or full row
   contents. Use parameterized SQL only (no string-interpolated filters).

---

## 7. Response contract

### Success (200)
```
Content-Type: text/csv; charset=utf-8
Content-Disposition: attachment; filename="raport-<type>-<YYYY-MM-DD>.csv"
```
Body = the BOM + CSV bytes. Use today's date (UTC) in the filename, e.g.
`raport-citizens-2026-06-02.csv`. The proxy forwards both headers to the browser
verbatim and uses the filename for the saved file.

### Errors (JSON body, so the frontend can map to Romanian copy)
Body shape: `{ "error": "<code>" }`. The frontend recognizes these codes:

| Status | `error` code | When |
|--------|--------------|------|
| 400 | `validation_failed` | bad date format, `from > to`, unknown `status` for the report |
| 401 | `unauthorized` | missing/expired/invalid session (also surfaces if Cognito rejects) |
| 404 | `not_found` | unknown `{type}` |
| 429 | `rate_limited` | rate limit hit (the proxy is capped at 20/min/IP; mirror server-side if you also limit) |
| 500 | `server_error` | anything unexpected |

Any unrecognized code falls back to a generic message client-side, so a sensible
default is fine, but prefer the codes above.

---

## 8. Implementation notes (Node.js / TypeScript)

**Suggested shape** — one handler that branches on `type`, each branch returning
`{ columns, rows }`, then a shared CSV serializer + audit write:

```ts
// Allowed report types and their per-report status whitelists.
const REPORTS = {
  campaigns:  { statuses: ['pending', 'approved', 'rejected', 'cancelled', 'finished'] },
  citizens:   { statuses: ['active', 'pending_confirm', 'unsubscribed'] }, // never 'deleted'
  organizers: { statuses: [] },
  activity:   { statuses: [] },
} as const
type ReportType = keyof typeof REPORTS

// --- RFC-4180 CSV serialization with UTF-8 BOM ---
const csvCell = (v: unknown): string => {
  const s = v === null || v === undefined ? '' : String(v)
  return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
}
const toCsv = (header: string[], rows: unknown[][]): string =>
  '﻿' + [header, ...rows].map(r => r.map(csvCell).join(',')).join('\r\n') + '\r\n'

// --- date helpers ---
const isISODate = (s: string) => /^\d{4}-\d{2}-\d{2}$/.test(s)
// 'to' is inclusive: compare against the start of the next day.
// SQL: created_at >= $from::date AND created_at < ($to::date + INTERVAL '1 day')
const fmtTs = (d: Date) =>
  d.toISOString().slice(0, 16).replace('T', ' ')   // 'YYYY-MM-DD HH:MM' (UTC)
```

**Parameterized SQL — `campaigns` example** (build the WHERE incrementally so
absent filters add no clause):

```sql
SELECT c.public_id,
       o.name           AS organization_name,
       c.county_code    AS county,
       co.name          AS county_name,
       l.name           AS locality,
       c.date_start, c.date_end, c.status,
       c.created_at, c.reviewed_at, c.reviewed_by
FROM campaigns c
JOIN organizers o ON o.id = c.organizer_id
JOIN counties   co ON co.code = c.county_code
JOIN localities l  ON l.id = c.locality_id
WHERE ($1::date IS NULL OR c.created_at >= $1::date)
  AND ($2::date IS NULL OR c.created_at < ($2::date + INTERVAL '1 day'))
  AND ($3::text IS NULL OR c.county_code = $3)
  AND ($4::text IS NULL OR c.status = $4::campaign_status)
ORDER BY c.created_at DESC;
```

`citizens` query: same date/county/status handling, plus
`AND c.status <> 'deleted'`, and select
`(c.phone IS NOT NULL) AS has_phone, (c.email IS NOT NULL) AS has_email` — then
map booleans to `da`/`nu` when serializing. **Do not select `phone`/`email`
values.**

`organizers`: filter only on `created_at` (date range); ignore `county`/`status`;
`campaign_count` via a `LEFT JOIN LATERAL` or correlated `COUNT`.

`activity`: from `audit_log`, filter `occurred_at` by date range; ignore
`county`/`status`; order `occurred_at DESC`.

**Format timestamps** (`created_at`, `reviewed_at`, `occurred_at`) as
`YYYY-MM-DD HH:MM` UTC; **dates** (`date_start`, `date_end`) as `YYYY-MM-DD`;
nulls → `''`.

**Size / streaming:** admin volumes are small, so buffering the CSV into one
string is fine for now. If a dataset could grow large, switch that report to a
server-side cursor and stream rows to the response (write the BOM + header first,
then chunk). Keep the audit write either way.

---

## 9. Acceptance criteria

- [ ] All four endpoints live, Cognito `admins`-gated, returning
      `text/csv; charset=utf-8` + `Content-Disposition` with a
      `raport-<type>-<YYYY-MM-DD>.csv` filename.
- [ ] CSV opens cleanly in Excel **and** Google Sheets with correct Romanian
      diacritics (BOM present, RFC-4180 quoting correct).
- [ ] Columns match §5 exactly (names + order) for each report.
- [ ] `from`/`to` filter inclusively; `county` filters campaigns/citizens/
      organizers-as-specified; `status` applies only to campaigns/citizens and is
      validated.
- [ ] `citizens` report: no raw phone/email (only `has_phone`/`has_email` =
      `da`/`nu`), and `deleted` citizens are excluded.
- [ ] Output IDs are `public_id` UUIDs (except `activity.entity_id`).
- [ ] **Every** successful export writes an `audit_log` row
      (`action = "report.export"`, actor = admin email, `metadata.type` +
      `metadata.filters`); the `citizens` export especially.
- [ ] Errors return the §7 JSON codes with matching HTTP status.
- [ ] SQL is fully parameterized; no secrets/PII in logs.

---

## Appendix — frontend reference (FYI, already built; do not modify)

- **Page:** `frontend/app/pages/admin/rapoarte/index.vue` — dataset picker, date
  presets (Today/7d/30d/this month/this year), county + conditional status
  filters, downloads via same-origin `fetch` → `Blob`.
- **Proxy:** `frontend/server/api/admin/reports/[type].get.ts` — gates on the
  admin session, validates `type ∈ {campaigns, citizens, organizers, activity}`
  (404 otherwise), whitelists `from/to/county/status`, streams your CSV back with
  `cache-control: no-store`, forwards your `Content-Disposition`.
- **Rate limit:** the proxy layer caps `/api/admin/reports` at ~20/min/IP.

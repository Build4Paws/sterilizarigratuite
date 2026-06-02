# Admin Reports — backend brief (`/admin/reports/**`)

> Handoff to the AWS backend team, mirroring `ADMIN-BACKEND-BRIEF.md`. Adds CSV
> report exports to the admin. **The frontend is already built and wired** to the
> routes below (Rapoarte page + `server/api/admin/reports/[type].get.ts` proxy);
> it returns 404 from the backend until these endpoints exist.
>
> See `ADMIN-PLAN.md` (auth + the rest of `/admin/**`) and `BACKEND-SCHEMA.md`
> (entities). Same Cognito authorizer + `admins` group gate as all `/admin/**`.

## Endpoints

All: **Cognito authorizer, group `admins` required.** Method `GET`. Respond with
**`Content-Type: text/csv; charset=utf-8`** and a
**`Content-Disposition: attachment; filename="..."`** header (the proxy forwards
both verbatim; if absent it falls back to `raport-{type}-YYYY-MM-DD.csv`).

| Path | Dataset |
|------|---------|
| `GET /admin/reports/campaigns` | Campaign submissions |
| `GET /admin/reports/citizens` | Citizen registrations (**PII — minimized**) |
| `GET /admin/reports/organizers` | Organizers |
| `GET /admin/reports/activity` | Audit-log activity |

### Shared query params (all optional)
| Param | Meaning |
|-------|---------|
| `from` | Inclusive start date `YYYY-MM-DD` (filters on `created_at` / `occurred_at`). |
| `to` | Inclusive end date `YYYY-MM-DD`. |
| `county` | 2-letter county code (e.g. `CJ`). Ignored by `activity`. |
| `status` | Lifecycle status. Only `campaigns` (`campaign_status`) and `citizens` (`citizen_status`) use it; ignored otherwise. |

The proxy whitelists exactly these four keys; anything else is dropped before the
request reaches you. No pagination — a report returns the **full filtered set**.

## CSV format

- **UTF-8 with a BOM** (`﻿`) so Excel renders Romanian diacritics correctly.
- First row = header. RFC-4180 quoting (quote fields containing `,` `"` newlines;
  escape `"` as `""`).
- Dates as ISO `YYYY-MM-DD` (or `YYYY-MM-DD HH:MM` where a time matters).
- Empty values = empty string, not `null`/`NULL`.

### Columns per report

**campaigns** — `public_id, organization_name, county, county_name, locality,
date_start, date_end, status, created_at, reviewed_at, reviewed_by`

**citizens** (⚠️ minimized — **no raw phone/email**) — `public_id, name,
county_name, locality, status, has_phone, has_email, created_at`
- `has_phone` / `has_email`: `da`/`nu` (presence only, matching the list view's
  `channelMask`). Raw contact details are deliberately excluded from the export.

**organizers** — `public_id, name, contact_email, contact_phone, campaign_count,
created_at`

**activity** — `occurred_at, actor, action, entity_type, entity_id, ip_address`

## Security / compliance (non-negotiable)

- **Every report generation writes `audit_log`** (actor = admin email from the
  Cognito claim, `action = "report.export"`, `entity_type = report`,
  `metadata = { type, filters }`). The **citizens** export is a PII-access event
  and MUST be audited — this is the gate the frontend can't enforce.
- **Data minimization (GDPR / NIS2, RO/BG/HU/PL):** the citizens report excludes
  raw phone/email by design. If a future requirement needs them, add a separate,
  explicitly-audited param (e.g. `?includeContact=true`) — don't widen the
  default columns.
- **`deleted` citizens:** exclude from the citizens export (PII already nulled per
  Art. 17); never resurrect erased data in a report.
- IDs in output are always `public_id` (UUID) — never the bigserial `id`, per the
  no-PII-in-URLs/IDs rule.

## Notes for the frontend side (already implemented)
- Proxy: `server/api/admin/reports/[type].get.ts` — gates on the admin session,
  validates `type ∈ {campaigns, citizens, organizers, activity}` (404 otherwise),
  forwards the whitelisted query, streams the CSV back with `cache-control: no-store`.
- Page: `app/pages/admin/rapoarte/index.vue` — type picker, date range, county,
  conditional status; downloads via a same-origin fetch → blob.
- Rate limit: `/api/admin/reports` capped at 20/min/IP (`server/middleware/rate-limit.ts`).

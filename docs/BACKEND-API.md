# Backend API Reference — v1.1.1

> Source of truth handed over by the backend team (SwaggerHub `Blitzcryp/v1.1.1`,
> OpenAPI 3.1.0). This file is the **canonical contract** the frontend wires
> against. If the live API and this file disagree, confirm with the backend team
> and update this file — don't silently work around it.
>
> See `BACKEND-SCHEMA.md` for the underlying PostgreSQL schema and
> `API-WIRING-PLAN.md` for how the frontend maps onto these endpoints.

## Base URLs

| Env | URL |
|-----|-----|
| Production | `https://api.sterilizarigratuite.ro` |
| AWS API Gateway | `https://cuk1b8z6w4.execute-api.eu-central-1.amazonaws.com` (`eu-central-1`) |
| Mock | `https://virtserver.swaggerhub.com/Blitzcryp/BackendStarter/1.0.0` |

The browser **never** calls these directly. Every call is proxied through a Nuxt
server route under `server/api/**` which signs the upstream request with AWS
SigV4 (`aws4fetch`, service `execute-api`). `AWS_API_BASE` overrides the base.

## Auth model

- **Public POST endpoints** (`/register`, `/campaigns/submit`): require an
  `hcaptchaToken` in the body. The server route verifies it against
  `https://api.hcaptcha.com/siteverify` before forwarding (empty secret = dev
  mode, skip).
- **Public GET endpoints**: no auth; cacheable (see `Cache-Control` per route).
- **Magic-link endpoints** (`/m/{token}`, `/r/{token}`): the token lives in the
  path (20–64 url-safe chars, `^[\w-]+$`), is hashed server-side, and is
  single-use. No API key / OAuth anywhere.

---

## Endpoints

### Citizens

#### `POST /register`
Subscribe a citizen for campaign notifications.

Request body (`CitizenRegistration`):
| field | type | required | notes |
|-------|------|----------|-------|
| `name` | string (1–200) | ✓ | |
| `phone` | string `^\+?[0-9\s\-]{7,15}$` | nullable | phone **or** email required |
| `email` | string (email) | nullable | phone **or** email required |
| `county` | string `^[A-Z]{1,2}$` | ✓ | auto code, e.g. `SV` |
| `locality` | string (1–200) | ✓ | locality **name** |
| `species` | `("dog"\|"cat")[]` (min 1) | ✓ | |
| `dogCount` | int (0–50) | nullable | |
| `catCount` | int (0–50) | nullable | |
| `gdprConsent` | boolean (must be `true`) | ✓ | |
| `hcaptchaToken` | string (min 1) | ✓ | stripped by server route before forward |

**200** → `{ message, citizenId (uuid), manageToken (string), stats: LocalityStats }`
Status codes: `200`, `400` (`validation_failed` \| `captcha_failed` \| `invalid_json`), `409` (`duplicate_registration`), `500` (`internal_error`).

#### `GET /register/{id}`
Look up a citizen by public UUID (confirmation data only — no PII beyond locality).
**200** → `{ citizenId (uuid), locality, countyName, status }` where `status ∈ {pending_confirm, active, unsubscribed, deleted}`.
Status codes: `200`, `400` (`invalid_id`), `404` (`not_found`).

### Campaigns

#### `POST /campaigns/submit`
Submit a campaign for admin review. Dedup by organizer + locality + dateStart.

Request body (`CampaignSubmission`):
| field | type | required | notes |
|-------|------|----------|-------|
| `organizationName` | string (1–200) | ✓ | |
| `contactEmail` | string (email) | ✓ | private |
| `contactPhone` | string `^\+?[0-9\s\-]{7,15}$` | ✓ | private |
| `phonePublic` | string `^\+?[0-9\s\-]{7,15}$` | ✓ | shown on the card |
| `county` | string `^[A-Z]{1,2}$` | ✓ | |
| `locality` | string (1–200) | ✓ | name |
| `address` | string (1–500) | ✓ | |
| `dateStart` | date `YYYY-MM-DD` | ✓ | |
| `dateEnd` | date `YYYY-MM-DD` | nullable | `null` = single day; else `>= dateStart` |
| `timeStart` | string `^\d{2}:\d{2}$` | ✓ | |
| `timeEnd` | string `^\d{2}:\d{2}$` | ✓ | |
| `species` | `("dog"\|"cat")[]` (min 1) | ✓ | |
| `slotsDogs` | int (1–10000) | nullable | required iff `dog` in species |
| `slotsCats` | int (1–10000) | nullable | required iff `cat` in species |
| `doctor` | string (max 200) | nullable | |
| `gdprConsent` | boolean (must be `true`) | ✓ | |
| `hcaptchaToken` | string (min 1) | ✓ | stripped by server route |

**200** → `{ message, submissionId (uuid), status: "pending", stats: LocalityStats }`
Status codes: `200`, `400` (`validation_failed` \| `captcha_failed`), `409` (`duplicate_submission`), `500` (`internal_error`).

> ⚠️ The old frontend proxied this as `POST /organizers` and read `campaignId`.
> v1.1.1 is `POST /campaigns/submit` returning **`submissionId`**.

#### `GET /campaigns?county=AB`
List **approved + upcoming** campaigns (backend filters status + end date).
Query: `county` optional `^[A-Z]{1,2}$`.
**200** → `{ campaigns: PublicCampaign[] }`. `Cache-Control: public, max-age=60, s-maxage=300`.
Status codes: `200`, `400` (invalid county).

#### `GET /campaigns/{id}`
Single campaign by UUID.
**200** → `PublicCampaign`. Status codes: `200`, `400` (`invalid_id`), `404` (`not_found`).

### Reference data

#### `GET /counties`
**200** → `{ counties: { code, name, slug }[] }`. `Cache-Control: public, max-age=86400`.

#### `GET /counties/{code}/localities?q=`
Query: `q` optional (max 50), diacritic-stripped **prefix** search, 50-result cap.
**200** → `{ localities: { id (int64), name }[] }`. Status codes: `200`, `400` (invalid county).

### Stats (public)

#### `GET /stats/locality?county=SV&locality=Bosanci`
Both query params required.
**200** → `{ county, locality, registeredInLocality (int), registeredInCounty (int) }`. `Cache-Control: public, max-age=60`.

#### `GET /stats/map?view=`
Query: `view ∈ {cerere, oferta}` optional.
**200** →
```jsonc
{
  "byCounty": {
    "SV": {
      "cerere": { "total": 35, "localities": { "Bosanci": 12 }, "species": { "dog": 20, "cat": 15 } },
      "oferta": [
        { "submissionId": "uuid", "organizationName": "...", "locality": "...",
          "dateStart": "2026-05-15", "dateEnd": null, "timeStart": "09:00",
          "timeEnd": "17:00", "species": { "dog": 20, "cat": 30 } }
      ]
    }
  },
  "totals": { "registrations": 1234, "campaigns": 56 }
}
```
`Cache-Control: public, max-age=60, s-maxage=300`.

### Magic-link (token-authenticated) — DEFERRED on the frontend

| Method | Path | 200 body | Errors |
|--------|------|----------|--------|
| GET | `/m/{token}` | `{ valid: true, citizen: { citizenId, name, locality, status } }` | `404` not_found, `410` `token_invalid` |
| POST | `/m/{token}/unsubscribe` | `{ message }` | `410` `token_invalid`, `500` |
| POST | `/m/{token}/erase` | `{ message }` (GDPR Art. 17 — nulls PII, revokes tokens) | `410` `token_invalid`, `500` |
| POST | `/r/{token}/confirm` | (no body) | `410` `token_invalid` |
| POST | `/r/{token}/unsubscribe` | (no body) | `410` `token_invalid` |

### Campaign management (organizer magic link)

Issued to the organizer in the **approval** email (`kind: campaign_manage`, 180-day
TTL, reusable — not consumed). Frontend page: `/gestionare-campanie/{token}`.

| Method | Path | 200 body | Errors |
|--------|------|----------|--------|
| GET | `/campaigns/manage/{token}` | `{ valid: true, campaign: { submissionId, organizationName, countyName, locality, address, dateStart, dateEnd, timeStart, timeEnd, status, soldOut } }` | `404` not_found, `410` `token_invalid` |
| POST | `/campaigns/manage/{token}/sold-out` | `{ soldOut, message }` — body `{ soldOut?: boolean }` (default `true`); sets `campaigns.sold_out` | `410` `token_invalid`, `400` `validation_failed`, `500` |

When `soldOut` is true the public phone is hidden across `/campanii`, `/harta` and
`/campanie/{id}`, replaced by "⛔ Locuri ocupate. Mulțumim!". The campaign stays
`approved` so it remains listed. Exposed on reads as `is_sold_out` (list) /
`isSoldOut` (detail). See `docs/SOLDOUT-FLOW-PLAN.md`.

---

## Component schemas

**`PublicCampaign`** — note `species` is an **object of slot counts**, not an array:
```ts
{
  submissionId: string         // uuid — frontend uses as `id`
  organizationName: string
  phonePublic: string
  county: string               // code
  countyName: string           // backend now resolves this
  locality: string
  address: string
  dateStart: string
  dateEnd: string | null
  timeStart: string
  timeEnd: string
  doctor: string | null
  species: Record<'dog' | 'cat', number>   // { dog: 20, cat: 30 } — value = slots
}
```

**`LocalityStats`** → `{ registeredInLocality: number, registeredInCounty: number }`

**Error base** → `{ error: string, message?: string }`
**Validation error** extends it with `errors: { field: string, message: string }[]`.

## Error codes (map in `app/utils/api-error.ts`)

`validation_failed`, `captcha_failed`, `invalid_json`, `invalid_id`,
`not_found`, `duplicate_registration`, `duplicate_submission`, `token_invalid`,
`internal_error`. (Legacy copy also keeps `rate_limited`, `server_error`.)

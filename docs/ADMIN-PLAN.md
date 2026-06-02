# Admin Plan — Build4Paws internal admin

> Internal, authenticated admin for staff. Lives at **`/admin/**`** inside this
> Nuxt app (noindex, separate auth from the public site). Covers campaign
> moderation, citizen browsing (PII), organizer/campaign management, and a
> dashboard + audit-log view.
>
> Split of work:
> - **Frontend (this repo):** `/admin` UI, auth session handling, and the
>   `server/api/admin/**` proxy routes. → my job.
> - **Backend (AWS team):** the `/admin/**` API Gateway + Lambda endpoints in
>   the [contract](#backend-contract--adminadmin-team-builds) below, behind a
>   **Cognito authorizer**. → handed to the backend team, mirroring how
>   `BACKEND-API.md` was handed to us.
>
> See `BACKEND-API.md` (public contract), `BACKEND-SCHEMA.md` (entities).

## ⚠️ Security & compliance (non-negotiable)

This admin exposes **citizen PII** (name, phone, email, IP) — the highest
sensitivity surface in the platform. Subject to GDPR / NIS2 across RO/BG/HU/PL.

- **Auth-gate everything.** No `/admin/**` page or `server/api/admin/**` route
  renders without a valid admin session. SSR pages check the session in
  `definePageMeta` middleware *and* the server route re-verifies — never trust
  the client.
- **Every mutation writes `audit_log`** (actor = admin email from the Cognito
  claim, action, entity, before/after in `metadata`, ip/ua). This is a backend
  responsibility but the contract below requires it.
- **Data minimization.** List endpoints return only what a row needs; full PII
  (phone/email) only on an explicit detail fetch, and detail views log access.
- **No PII in logs, no PII in URLs.** Use `public_id` (UUID) in paths, never the
  bigserial `id`, never name/phone/email in query strings.
- **GDPR actions** (citizen erase) null PII per Art. 17 and are irreversible —
  require a confirm step + reason, and audit them.
- Admin routes are `robots: false` and excluded from the sitemap.

## Auth — Amazon Cognito User Pool

Native AWS fit; preserves the existing boundary (the browser never holds AWS
creds — only an httpOnly session cookie it can't read).

### Setup (one-time, AWS console / IaC)
- **User Pool** `b4p-admins`, region `eu-central-1` (same as API Gateway).
  - Sign-up **disabled** (invite-only). Admins are created by an existing admin.
  - Group **`admins`** — membership is what authorizes API access.
  - **MFA = required (TOTP)**. Strongly recommended given PII exposure.
  - Password policy: 12+ chars, all classes.
  - App client `b4p-admin-web`: enable `ALLOW_USER_PASSWORD_AUTH` +
    `ALLOW_REFRESH_TOKEN_AUTH`. Use a client **with** a secret (kept server-side
    in Nuxt runtimeConfig) — the secret never reaches the browser.
  - Token validity: ID/access ~60 min, refresh ~8–12 h (a staff shift).
- **API Gateway**: attach a **Cognito User Pool authorizer** to all `/admin/**`
  routes (public routes keep their current AWS_IAM/SigV4 authorizer). The Lambda
  reads `email` and `cognito:groups` from the validated JWT claims; reject if
  `admins` ∉ groups (defense in depth — the authorizer already validates the JWT).

### Runtime flow
```
1. Admin → /admin/login  (custom RO form)
2. POST /api/admin/auth/login (Nuxt server route) — one route, several phases:
     → InitiateAuth USER_PASSWORD_AUTH (+ SECRET_HASH)
     → may cascade through challenges, each a round-trip to the same route:
         NEW_PASSWORD_REQUIRED  (first sign-in after invite — set own password)
         MFA_SETUP              (enroll TOTP: AssociateSoftwareToken → VerifySoftwareToken)
         SOFTWARE_TOKEN_MFA     (steady-state: enter 6-digit code)
     → tokens returned. Cognito `session` (+ TOTP secret on setup) round-trips to
       the client; tokens never appear in the response body.
3. Nuxt sets httpOnly, Secure, SameSite=Lax cookies:
     b4p_id (idToken), b4p_refresh (refreshToken)   [no token in JS-readable storage]
4. /admin/** page middleware verifies session (validates idToken: exp + signature
     via JWKS, or a light /api/admin/auth/me probe).
5. server/api/admin/** routes read b4p_id cookie → forward
     `Authorization: Bearer <idToken>` to API Gateway /admin/**.
6. On 401/near-exp → /api/admin/auth/refresh uses b4p_refresh to mint new tokens.
7. /api/admin/auth/logout clears cookies (+ optional Cognito GlobalSignOut).
```

New `runtimeConfig` (server-only, never `public.*`):
`cognitoUserPoolId`, `cognitoClientId`, `cognitoClientSecret`, `cognitoRegion`.

CSP `connect-src` may need `https://cognito-idp.eu-central-1.amazonaws.com` only
if we ever call Cognito from the browser — with the server-route flow above we
**don't**, so CSP is unchanged.

## Backend contract — `/admin/**` (backend team builds)

All routes: **Cognito authorizer**, group `admins` required. JSON in/out. Errors
use the existing base `{ error, message? }`. Every state change writes
`audit_log`. `id` in paths is always the **`public_id` UUID**.

### Campaigns — moderation & management
| Method | Path | Purpose | Body / query | 200 |
|--------|------|---------|--------------|-----|
| GET | `/admin/campaigns` | List/filter all statuses | `?status=&county=&q=&page=&limit=` | `{ campaigns: AdminCampaign[], total }` |
| GET | `/admin/campaigns/{id}` | Full detail incl. organizer contact + ip/ua | — | `AdminCampaignDetail` |
| POST | `/admin/campaigns/{id}/approve` | pending → approved | — | `{ status: "approved", reviewedAt, reviewedBy }` |
| POST | `/admin/campaigns/{id}/reject` | pending → rejected | `{ reason: string (1..500) }` | `{ status: "rejected", ... }` |
| PATCH | `/admin/campaigns/{id}` | Edit fields / cancel / finish | partial `AdminCampaignEdit` incl. `status` | `AdminCampaignDetail` |

`AdminCampaign` = `PublicCampaign` + `{ status, organizerName, createdAt,
reviewedAt, reviewedBy, rejectionReason }`. `AdminCampaignDetail` additionally
exposes `contactEmail`, `contactPhone`, `submittedIp`, `submittedUa`.

### Citizens (PII — minimize)
| Method | Path | Purpose | Body / query | 200 |
|--------|------|---------|--------------|-----|
| GET | `/admin/citizens` | List/search | `?status=&county=&locality=&q=&page=&limit=` | `{ citizens: AdminCitizenRow[], total }` |
| GET | `/admin/citizens/{id}` | Detail (logs PII access) | — | `AdminCitizenDetail` |
| PATCH | `/admin/citizens/{id}` | Edit `notes` / `status` | `{ notes?, status? }` | `AdminCitizenDetail` |
| POST | `/admin/citizens/{id}/unsubscribe` | status → unsubscribed | — | `{ status }` |
| POST | `/admin/citizens/{id}/erase` | GDPR Art. 17 — null PII, revoke tokens | `{ reason }` | `{ status: "deleted" }` |

`AdminCitizenRow` is **minimized**: `{ citizenId, name, countyName, locality,
status, channelMask: { phone: bool, email: bool }, createdAt }` — no raw
phone/email in the list. `AdminCitizenDetail` adds masked-by-default
phone/email + species counts + consent metadata.

### Organizers
| Method | Path | Purpose | 200 |
|--------|------|---------|-----|
| GET | `/admin/organizers` | List/search `?q=&page=&limit=` | `{ organizers: AdminOrganizer[], total }` |
| GET | `/admin/organizers/{id}` | Detail + their campaigns | `AdminOrganizerDetail` |
| PATCH | `/admin/organizers/{id}` | Edit contact / notes | `AdminOrganizerDetail` |

### Dashboard & audit
| Method | Path | Purpose | 200 |
|--------|------|---------|-----|
| GET | `/admin/stats/overview` | Tiles + recent activity | `{ pendingCampaigns, approvedUpcoming, citizensActive, registrationsToday, byStatus, ... }` |
| GET | `/admin/audit?entityType=&entityId=&action=&page=` | Audit log feed | `{ entries: AuditEntry[], total }` |

## Frontend structure (this repo)

```
app/pages/admin/
  login.vue                 # Cognito login (+ MFA step)
  index.vue                 # dashboard (tiles + recent activity)
  campanii/index.vue        # moderation queue (default filter status=pending)
  campanii/[id].vue         # detail + approve/reject/edit
  cetateni/index.vue        # citizen list (minimized)
  cetateni/[id].vue         # citizen detail (PII gated) + unsubscribe/erase
  organizatori/index.vue    # organizers list
  organizatori/[id].vue     # organizer detail + their campaigns
  audit/index.vue           # audit log feed
app/layouts/admin.vue        # admin chrome (nav, current user, logout) — separate from public layout
app/middleware/admin-auth.ts # route guard → redirect to /admin/login if no session
app/composables/useAdminAuth.ts, useAdminCampaigns.ts, useAdminCitizens.ts, ...
app/types/admin.ts           # AdminCampaign, AdminCitizenRow, ... (re-exported via ~/types)

server/api/admin/
  auth/login.post.ts  auth/refresh.post.ts  auth/logout.post.ts  auth/me.get.ts
  campaigns/index.get.ts  campaigns/[id].get.ts
  campaigns/[id]/approve.post.ts  campaigns/[id]/reject.post.ts  campaigns/[id]/index.patch.ts
  citizens/index.get.ts  citizens/[id].get.ts  citizens/[id]/index.patch.ts
  citizens/[id]/unsubscribe.post.ts  citizens/[id]/erase.post.ts
  organizers/index.get.ts  organizers/[id].get.ts  organizers/[id]/index.patch.ts
  stats/overview.get.ts  audit/index.get.ts
server/utils/admin-auth.ts   # requireAdminSession(event) → reads cookie, returns idToken; throws 401
```

Conventions reused: `server/utils/fetch-upstream.ts` (timeout→503), `extractApiError`
+ Romanian copy in `utils/api-error.ts` (add admin-specific codes), `<CampaignCard>`
for campaign rendering, design tokens in `main.css`, RO copy throughout.

`routeRules`: `'/admin/**': { robots: false, ssr: true }`. Exclude `/admin` from
the sitemap source. Add `/api/admin/**` to the rate-limit middleware LIMITS
(esp. `/api/admin/auth/login`).

## Phasing

1. **Auth foundation** — Cognito flow end-to-end: login (+MFA), session cookies,
   `requireAdminSession`, `admin-auth` middleware, `admin.vue` layout, login page.
   Verifiable as soon as the pool + one test user exist.
2. **Campaign moderation** (core value) — list/detail/approve/reject. Unblocks the
   long-deferred approval flow; makes the public `/campanii` curated.
3. **Dashboard** — overview tiles + recent activity.
4. **Citizens (PII)** — list (minimized) → detail (gated) → unsubscribe/erase.
5. **Organizers + campaign edit/cancel/finish.**
6. **Audit log view.**

Phases 2–6 each need their backend `/admin/**` endpoints live first; until then
the matching server route can be stubbed against the contract for UI dev.

## Open items for the backend team
- Confirm Cognito authorizer on `/admin/**` + group claim shape (`cognito:groups`).
- `reviewed_by` / audit `actor` populated from the JWT `email` claim.
- Pagination contract (`page`/`limit` vs cursor) — doc above assumes offset paging.
- Citizen list PII minimization (no raw phone/email in list payloads).

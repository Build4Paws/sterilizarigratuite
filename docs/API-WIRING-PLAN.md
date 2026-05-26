# API Wiring Plan — Backend v1.1.1

Wire the frontend onto the backend **v1.1.1** contract (`BACKEND-API.md`) and fix
the divergent legacy implementation. Entity model: `BACKEND-SCHEMA.md`.

**Audience:** the implementing agent (Sonnet). Execute **story by story, top to
bottom**. Each story is one PR-sized unit with explicit files + acceptance checks.
There is no test runner/linter — verify with `npm run typecheck` (strict) and a
manual `npm run dev` smoke of the touched flow. Don't claim "tests pass".

## Scope decisions (locked with the product owner)

1. **Location data — HYBRID.** Counties stay local (`assets/data/judete.json`)
   because they power synchronous SSR slug↔code↔name lookups on `/campanii` and
   `/harta`. **Localities** move to the API typeahead `GET /counties/{code}/localities`.
   `GET /counties` is *not* wired (optional future work). POST payloads keep
   sending `locality` as the **name string**.
2. **Magic-link / refresh pages — DEFERRED.** `/m/[token]` and `/r/[token]` stay
   placeholders; do **not** build their server routes or UI in this effort. The
   contract is documented for when we pick it up.

## Endpoint status matrix

| Endpoint | Current frontend state | Action |
|----------|------------------------|--------|
| `POST /register` | ✅ proxied (`register.post.ts`) | Keep proxy; fix response **type** (`citizenId`, `manageToken`). Story 1 |
| `POST /campaigns/submit` | ❌ proxies `POST /organizers`, reads `campaignId` | **Fix** path + `submissionId` + forward `stats`. Story 2 |
| `GET /campaigns` | ⚠️ proxied but consumer assumes `species` is an array | **Fix** mapping in `useCampaigns` (`species` object→array+slots). Story 3 |
| `GET /stats/locality` | ❌ proxies `/stats/registrations` + reshapes | **Switch** to dedicated endpoint. Story 4 |
| `GET /stats/map` | ❌ proxies `/stats/registrations` (old shape) | **Switch** to `/stats/map`, reshape at boundary. Story 5 |
| `GET /counties/{code}/localities` | ❌ not wired (local JSON) | **New** signed route + async combobox. Story 6 |
| `GET /register/{id}` | ❌ not wired, no consumer | Optional — skip (no page needs it). |
| `GET /campaigns/{id}` | ❌ not wired, no consumer | Optional — skip (no detail page). |
| `GET /counties` | ❌ not wired | Skip (counties stay local). |
| `/m/**`, `/r/**` | placeholders | **Deferred** — out of scope. |

---

## Story 0 — Types & error codes (unblocker, do first)

**Files:** `app/types/citizen.ts`, `app/types/organizer.ts`, `app/types/campaign.ts`, `app/types/map.ts`, `app/utils/api-error.ts`

1. `citizen.ts` — `CitizenRegistrationResponse` add `citizenId: string` and
   `manageToken: string`. Relax `RegistrationStats` so the register `stats`
   (just `registeredInLocality` + `registeredInCounty`, per `LocalityStats`)
   validates — make `county`/`locality` optional.
2. `organizer.ts` — rename `CampaignSubmissionResponse.campaignId` →
   **`submissionId`**.
3. `campaign.ts` — add a wire type matching `PublicCampaign` exactly (note
   `species: Partial<Record<Species, number>>`, `dateEnd: string | null`,
   `countyName: string`, `submissionId`). Keep the existing `Campaign`/
   `CampaignCardData` shapes for the UI; the mapping lives in Story 3.
   `CampaignStatus`: the public list is always approved+upcoming, so a default
   of `'APPROVED'` is fine; don't rely on a wire `status` field (PublicCampaign
   has none).
4. `map.ts` — add the new `MapStats` wire shape (`byCounty[code].{cerere,oferta}`
   + `totals`). Keep `CountyStats` (Story 5 reshapes into it).
5. `api-error.ts` — add codes: `invalid_json`, `invalid_id`, `not_found`,
   `token_invalid`, `internal_error` (map `internal_error` to the same copy as
   `server_error`). Keep existing entries. Re-export new types from
   `types/index.ts`.

**Accept:** `npm run typecheck` clean after each consuming story; barrel exports updated.

## Story 1 — `POST /register` response

**Files:** `server/api/register.post.ts` (proxy is correct — no change needed), `app/components/forms/CitizenForm.vue`, `app/composables/useCitizenSession.ts`

- The proxy passes JSON through, so `citizenId`/`manageToken` already arrive.
- Optionally stash `manageToken` + `citizenId` in `useCitizenSession` for a
  future "manage your subscription" link (magic-link UI is deferred, so this is
  just persistence — no UI). Low priority; keep if cheap.
- `dogCount`/`catCount` already sent by the form and accepted by the spec — no change.

**Accept:** registration flow still reaches `/confirmare`; `response.stats` renders rank copy.

## Story 2 — Fix `POST /campaigns/submit`

**Files:** `server/api/campaigns/submit.post.ts`, `app/types/organizer.ts` (done in Story 0), `app/components/forms/CampaignForm.vue`, `app/composables/useOrganizerSubmission.ts`, `app/pages/confirmare-campanie.vue`

1. `submit.post.ts`: change upstream from `${baseUrl}/organizers` →
   `${baseUrl}/campaigns/submit`. Parse the upstream response and return
   `{ message, submissionId, status, stats }` — read **`submissionId`** (not
   `campaignId`) and **forward `stats`** (currently dropped). Drop the
   `crypto.randomUUID()` fallback; the spec guarantees `submissionId`.
2. `CampaignForm.vue` (~line 600): `response.campaignId` → `response.submissionId`.
3. `useOrganizerSubmission.ts`: rename the session field `campaignId` →
   `submissionId`.
4. `confirmare-campanie.vue` (~line 45): `session.campaignId` → `session.submissionId`.

**Accept:** submitting a campaign in dev reaches `/confirmare-campanie`, the ID renders, and the "X persoane așteaptă" stats block shows (stats no longer dropped).

## Story 3 — Fix `GET /campaigns` mapping (`/campanii` + `/harta`)

**Files:** `app/composables/useCampaigns.ts` (+ `app/types/campaign.ts` from Story 0). `campanii.vue`/`harta.vue` should need no change if the composable keeps returning `Campaign[]`.

The bug: `PublicCampaign.species` is an **object of slot counts**
(`{ dog: 20, cat: 30 }`), but `Campaign.species` is `Species[]` and
`useCampaigns` filters with `c.species.includes(sp)` — which throws on an object.
Add a normalizer in `useCampaigns` that maps each `PublicCampaign` → `Campaign`:
- `id` ← `submissionId`
- `species` (array) ← `Object.keys(p.species)` filtered to `'dog'|'cat'`
- `slotsDogs` ← `p.species.dog`, `slotsCats` ← `p.species.cat`
- `dateEnd` ← `p.dateEnd ?? undefined`
- carry `countyName` through (backend now provides it) — `campanii.vue`'s
  `toCardData` can prefer `p.countyName` over `countyCodeToNameSync`, with the
  local lookup as fallback.
- `status` ← `'APPROVED'` default; `createdAt` ← `''` (unused by the card).

**Accept:** `/campanii` lists cards, the species filter (`?specie=caine`) works without errors, slot counts render; `/harta` "Ofertă" still tallies per county.

## Story 4 — Switch `GET /stats/locality` to the dedicated endpoint

**Files:** `server/api/stats/locality.get.ts`

Replace the `/stats/registrations?county=` call + `byLocality[locality]`
reshaping with a direct signed call to
`${baseUrl}/stats/locality?county=<c>&locality=<l>` and pass the response through
(it already returns `{ county, locality, registeredInLocality, registeredInCounty }`).
Keep the required-param 400 guard and `Cache-Control: public, max-age=60`.
`useLocalityWaitingCount` and its consumers (`CampaignForm`, `/confirmare`)
need no change — same response shape.

**Accept:** picking a locality in the campaign form shows the live waiting count; `/confirmare` fallback count still resolves.

## Story 5 — Switch country stats to `GET /stats/map`

**Files:** rename `server/api/stats/registrations.get.ts` → `server/api/stats/map.get.ts`; `app/composables/useRegistrationStats.ts`; `app/types/map.ts` (Story 0)

- New route calls `${baseUrl}/stats/map` (pass an optional `view` query through).
- **Reshape at the boundary** into the existing `RegistrationsCountryResponse`
  so `/harta` stays stable: `byCounty[code] = mapStats.byCounty[code].cerere`
  (which already has `total`/`localities`/`species`), and
  `totalRegistrations = mapStats.totals.registrations`. Keep the
  `Cache-Control` header. The Ilfov `"Ilfov"→"IF"` guard can be dropped once the
  backend confirms 2-letter codes everywhere — keep it defensively for now.
- `useRegistrationStats`: change the fetch URL `/api/stats/registrations` →
  `/api/stats/map`; the rest (localStorage cache, getCachedData) is unchanged
  since the reshaped payload matches the old type.
- **Optional follow-up (note, don't block):** the new `byCounty[code].oferta`
  array + `totals.campaigns` could replace `/harta`'s client-side oferta
  derivation from `/api/campaigns`. Leave that as a later refinement; `/harta`
  still fetches campaigns for the per-county side-panel detail.

**Accept:** `/harta` "Cerere" choropleth + top-10 + per-county localities render exactly as before.

## Story 6 — New localities typeahead (hybrid)

**Files:** `server/api/counties/[code]/localities.get.ts` (new); `app/composables/useLocationData.ts` (extend) or new `useLocalities.ts`; `app/components/ui/Combobox.vue` (verify/extend); `app/components/forms/CitizenForm.vue`, `app/components/forms/CampaignForm.vue`

1. **Server route** — copy the SigV4 GET shape from `campaigns/index.get.ts`.
   Read `code` from the path (validate `^[A-Z]{1,2}$`), forward `?q=` (trim, cap
   50). Proxy `${baseUrl}/counties/{code}/localities?q=...`, return `{ localities }`
   pass-through. Cache `public, max-age=86400` (localities rarely change).
2. **Composable** — add `searchLocalities(countyCode, q)` returning
   `{ id, name }[]`, debounced (~250ms). Counties keep using the existing local
   indexes — only the locality list becomes remote.
3. **Combobox** — inspect `components/ui/Combobox.vue`. If it only takes a static
   `:options` list, add an async path: a `@search`/`update:query` event +
   `:loading` state so the parent can feed remote results. Keep the value =
   locality **name** (the POST contract is unchanged).
4. **Forms** — `CitizenForm` + `CampaignForm`: replace the local
   `useLocationData().localities` source for the locality field with the async
   search. On county change, reset locality. On API error, fall back to the
   local `judete.json` locality list (graceful degradation) and/or allow free
   text so submission isn't blocked.

**Accept:** typing in the locality field queries the API (debounced, diacritic-insensitive), selecting sets the name, and citizen + campaign submits still send the locality name. Counties unchanged. Network failure degrades gracefully.

## Story 7 — Docs & comment cleanup

**Files:** `CLAUDE.md`, `docs/FRONTEND-PLAN.md`, stale code comments

Update the stale notes now that wiring is done:
- `CLAUDE.md` "Security boundary": backend submit route is `POST /campaigns/submit`
  (not `/organizers`); `/campaigns`, `/stats/locality`, `/stats/map`, and
  `/counties/{code}/localities` are now wired.
- `CLAUDE.md` "Known mocks/stubs": `stats/locality` is no longer a mock (it was
  already a proxy); update accordingly. `/campanii` is live (not a placeholder).
- `CampaignForm.vue` comment "(mocked at /api/stats/locality)" → remove "mocked".
- Note magic-link `/m`,`/r` remain deferred and `GET /counties`,
  `/register/{id}`, `/campaigns/{id}` are available-but-unused.

**Accept:** docs match the shipped behavior; no comment still calls a live route "mocked".

---

## Cross-cutting checks

- **SigV4 pattern:** every new server route reads creds from `useRuntimeConfig()`
  (server-only), signs with `aws4fetch` service `execute-api`, normalizes
  `awsApiBase` to an absolute URL, and forwards upstream error bodies as `data`
  on `createError(...)` so `extractApiError` maps the code. Copy
  `campaigns/index.get.ts` (GET) or `register.post.ts` (POST + hCaptcha).
- **CSP:** browser only talks to same-origin `/api/**`; `connect-src` already
  allows `https://api.sterilizarigratuite.ro` for the server side. No change.
- **No new captcha** on GET routes.
- After each story: `npm run typecheck` (strict) + manual `npm run dev` smoke of
  the touched page. Node 24+ (`node -v`).

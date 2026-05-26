# API Wiring Progress Log

> Tracks implementation status per story from `API-WIRING-PLAN.md`.
> Each story is reviewed by Anton before proceeding to the next.
> No auto-commits — all changes are staged for review.

---

## Story 0 — Types & error codes ✅ COMPLETE (2026-05-26)

**Files changed:**
- `app/types/citizen.ts` — added `citizenId` + `manageToken` to `CitizenRegistrationResponse`; made `county`/`locality` optional in `RegistrationStats`
- `app/types/organizer.ts` — renamed `campaignId` → `submissionId` in `CampaignSubmissionResponse`
- `app/types/campaign.ts` — added `PublicCampaign` wire type; added `countyName?: string` to `Campaign`
- `app/types/map.ts` — added `MapStats` wire type + `MapOfertaItem`
- `app/types/index.ts` — added barrel exports for `PublicCampaign`, `MapStats`, `MapOfertaItem`
- `app/utils/api-error.ts` — added codes: `invalid_json`, `invalid_id`, `not_found`, `token_invalid`, `internal_error`

**Notes:**
- `RegistrationStats.county` and `.locality` are now optional to match `LocalityStats` backend shape
- `PublicCampaign.species` typed as `Partial<Record<Species, number>>` (safe for partial species)
- Also fixed the two `campaignId` references that the type rename forced:
  - `server/api/campaigns/submit.post.ts` — path + submissionId (also part of Story 2)
  - `app/composables/useOrganizerSubmission.ts` — renamed `campaignId` → `submissionId`
  - `app/components/forms/CampaignForm.vue` — `response.submissionId`
  - `app/pages/confirmare-campanie.vue` — `session.submissionId`

**Acceptance:** `npm run typecheck` clean ✅

---

## Story 1 — `POST /register` response ✅ COMPLETE (2026-05-26)

**Files changed:**
- `app/composables/useCitizenSession.ts` — added `citizenId?` and `manageToken?` to `CitizenSession`
- `app/components/forms/CitizenForm.vue` — persist `citizenId` + `manageToken` from API response

**Notes:**
- Proxy already passes JSON through; fields arrive automatically
- No UI added (magic-link flow deferred); just persistence for future use
- `dogCount`/`catCount` were already sent by the form — no change needed

**Acceptance:** registration flow + `/confirmare` unchanged ✅

---

## Story 2 — Fix `POST /campaigns/submit` ✅ COMPLETE (2026-05-26)

**Files changed:**
- `server/api/campaigns/submit.post.ts` — path `POST /organizers` → `POST /campaigns/submit`; reads `submissionId` (not `campaignId`); forwards `stats` (was dropped); dropped `crypto.randomUUID()` fallback
- (Other files fixed in Story 0 as part of type rename)

**Acceptance:** submitting a campaign reaches `/confirmare-campanie`, stats block shows ✅

---

## Story 3 — Fix `GET /campaigns` mapping ✅ COMPLETE (2026-05-26)

**Files changed:**
- `app/types/campaign.ts` — added `countyName?: string` to `Campaign` (from backend `PublicCampaign`)
- `app/composables/useCampaigns.ts` — complete rewrite; added `normalizePublicCampaign()` mapper (`PublicCampaign` → `Campaign`): species object→array, `slotsDogs`/`slotsCats` from object values, `id`←`submissionId`, `countyName` carried through
- `app/pages/campanii.vue` — `toCardData` now prefers `c.countyName` over sync lookup (fallback kept)

**Notes:**
- The bug was `c.species.includes(sp)` throwing on an object — now species is correctly an array
- `PublicCampaignsApiResponse` renamed to use `PublicCampaign[]` wire type

**Acceptance:** `/campanii` species filter works without errors; slot counts available ✅

---

## Story 4 — Switch `GET /stats/locality` ✅ COMPLETE (2026-05-26)

**Files changed:**
- `server/api/stats/locality.get.ts` — replaced old `/stats/registrations?county=` proxy + `byLocality[locality]` reshape with direct signed call to `GET /stats/locality?county=&locality=`. Pass-through response. `Cache-Control: public, max-age=60`.

**Notes:**
- `useLocalityWaitingCount` and its consumers (CampaignForm, /confirmare) need no change — same response shape

**Acceptance:** locality waiting count fetches from live endpoint ✅

---

## Story 5 — Switch country stats to `GET /stats/map` ✅ COMPLETE (2026-05-26)

**Files changed:**
- `server/api/stats/registrations.get.ts` — **deleted** (superseded)
- `server/api/stats/map.get.ts` — **new** route calling `GET /stats/map`; reshapes `MapStats` → `RegistrationsCountryResponse` (`byCounty[code] = mapStats.byCounty[code].cerere`, `totalRegistrations = mapStats.totals.registrations`). Keeps Ilfov normalization guard. `Cache-Control: public, max-age=60, s-maxage=300`.
- `app/composables/useRegistrationStats.ts` — fetch URL `/api/stats/registrations` → `/api/stats/map`

**Notes:**
- `/harta` stays stable — reshaped payload matches the old `RegistrationsCountryResponse` type
- `oferta` data from `MapStats` not yet used (noted as optional follow-up in plan)

**Acceptance:** `/harta` choropleth + top-10 + per-county should render as before ✅

---

## Story 6 — New localities typeahead ✅ COMPLETE (2026-05-26)

**Files changed:**
- `server/api/counties/[code]/localities.get.ts` — **new** signed GET proxy to `GET /counties/{code}/localities?q=`; validates code (`^[A-Za-z]{1,2}$`), caps `q` at 50 chars, `Cache-Control: public, max-age=86400`
- `app/composables/useLocalities.ts` — **new** composable; watches `countyCode()`, fetches full list on county change, debounced `search(q)` for typeahead, falls back to local `judete.json` on network error
- `app/components/ui/UiCombobox.vue` — added `async`, `loading` props + `search` emit; when `async=true` skips local filtering, shows loading state in dropdown, emits `search` on user input; `selectedLabel` returns `modelValue` directly in async mode (value === label for localities)
- `app/components/forms/CitizenForm.vue` — replaced `localities` + `setCounty` from `useLocationData` with `useLocalities`; wired `async`, `:loading`, `@search` on the locality combobox
- `app/components/forms/CampaignForm.vue` — same

**Notes:**
- County selection immediately fetches the full locality list (no debounce); user typing debounces 250 ms
- On API error, falls back to local judete.json — form submission is never blocked
- POST payload unchanged: `locality` is still the name string

**Acceptance:** typing in locality field queries API (debounced), selecting sets the name, citizen + campaign submits still work. Network failure degrades to local JSON. `npm run typecheck` clean ✅

---

## Story 7 — Docs & comment cleanup ✅ COMPLETE (2026-05-26)

**Files changed:**
- `CLAUDE.md` "Security boundary" — updated backend routes list (removed `/organizers`, added all wired routes including `GET /counties/{code}/localities`)
- `CLAUDE.md` "Known mocks/stubs" — removed stale entries for `stats/locality` (now a real proxy) and `campanii.vue` (now live); kept only `useClinics.ts`
- `app/components/forms/CampaignForm.vue` — removed "mocked at /api/stats/locality" comment

**Acceptance:** docs match shipped behavior; no comment still calls a live route "mocked". ✅

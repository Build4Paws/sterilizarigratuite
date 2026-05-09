# `/campanii` — Public Campaign Listing Plan

The page that answers a citizen's first question off Google/Facebook:
**"Unde și când pot steriliza gratuit acum?"**

This is the public, SEO-critical view. Read-only. Citizens contact the
organizer directly — we don't proxy reservations.

---

## 1. Goals & non-goals

**Goals**
- One scannable list of upcoming, approved campaigns from across the country.
- Two-tap filtering: județ + specie, with results visible without scrolling.
- A direct, prominent **call** CTA per card (mobile-first — most traffic is
  phone).
- Indexable filtered URLs (`/campanii?judet=alba`) so Google can rank
  per-county queries like *"sterilizare gratuită alba"*.

**Non-goals (now)**
- No reservation/booking flow.
- No campaign detail page (`/campanii/[id]`) — defer to v2 unless we discover
  card UX is too cramped.
- No map view.
- No pagination at MVP — list is short enough for the foreseeable future.
  Add when total approved+upcoming exceeds ~30.
- No "subscribe" CTA inline on the page (homepage already owns that).

---

## 2. Backend contract

```
GET https://api.sterilizarigratuite.ro/campaigns
GET https://api.sterilizarigratuite.ro/campaigns?county=AB
```

The endpoint returns **only campaigns that are approved and not finished
yet** — no client-side `status` or date filtering required. We trust the
backend's filter.

**Param shape:** always the 2-letter `auto` code (`AB`, `SV`, `IF`, …) —
matches what `POST /organizers` already stores. The earlier
`county=Ilfov` example was a bad sample; ignore it.

**Single-filter only:** the endpoint supports `?county=...` and nothing
else for now. No `species` query param. Species filtering is therefore
**client-side only** (see §5.2).

Expected response shape (matches `Campaign` in `app/types/campaign.ts`):

```ts
type CampaignsResponse = {
  campaigns: Campaign[]
  // Optional fields the backend may add later — accept gracefully:
  // total?: number
}
```

---

## 3. URL & query schema

User-facing URL uses the **full județ name as a slug** (Romanian, for SEO):

| Query param | Values | Notes |
|---|---|---|
| `judet` | full county name slug (`alba`, `cluj`, `bistrita-nasaud`, `bucuresti`) or omitted | Resolved to 2-letter code before hitting the backend. |
| `specie` | `caine` \| `pisica` \| omitted | **Client-side filter only** — never sent to API. |

- Default state (no params) = whole country, no API filter applied.
- Selecting a județ triggers a **new API call** with `?county={code}`.
- Selecting a specie filters the already-fetched list **without** a
  refetch (API doesn't support combined filters).
- Selecting both = API call filtered by județ, then in-memory filter by
  specie.
- Filters are reflected in the URL via `router.replace` (no history spam
  on every dropdown change).
- Slug = `judete.json` entry's `simplu` (or `nume` if `simplu` is absent),
  lowercased, spaces and `ş ț ă â î` normalized to `s t a a i`, joined by
  `-` (so "Bistrița-Năsăud" → `bistrita-nasaud`). The slug ↔ code map
  belongs in `useLocationData` (§5.3).

**Why the full name as slug, not the code:** `/campanii?judet=alba` is
what people actually type into Google ("sterilizare gratuită alba") —
the URL surfaces the search term we want to rank for. `?judet=AB` would
rank for nothing.

---

## 4. Page layout

```
┌────────────────────────────────────────────────────────────────┐
│  Hero (compact, navy)                                          │
│  ─────────────────                                             │
│  H1: "Campanii de sterilizare gratuită"                        │
│  Sub: "Găsește o campanie aproape de tine. Sună direct la      │
│        organizator pentru programare."                         │
│                                                                │
│  [ Județ ▾ toate județele ]   [ Specie ▾ toate ]   ↺ Resetează │
│  ─────────────────                                             │
│  📅 Campanii viitoare  ·  N campanii (în Alba)                 │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ <CampaignCard>                          [📞 Sună acum] │  │
│  │   Pianu · ALBA                                          │  │
│  │   12 mai 2026 · 09:00–17:00                            │  │
│  │   Organizator: ONG Patrupede                           │  │
│  │   🐶 30 locuri  🐱 50 locuri                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  ...                                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### 4.1 Hero

Compact (~`var(--space-2xl)` top/bottom). Navy bg, no curved divider —
this is a utility page, not a landing. H1 + 1-line subtitle. Filters live
on a sticky-ish bar **just below** the hero (not inside) so they're always
near the list.

### 4.2 Filters

- **Județ** — reuse `<UiCombobox>` (already searchable, used in forms),
  options from `useLocationData().counties` plus a synthetic
  "Toate județele" entry at top with `value: ''`.
- **Specie** — `<UiSelect>` with three options: `Toate`, `Câini`, `Pisici`.
- **Resetează** — small `<UiButton variant="ghost">` visible only when at
  least one filter is set. Clears query params.

Active filters show as a count next to the section heading
("**N campanii** în **Alba** pentru **câini**") so the user always knows
what they're seeing.

### 4.3 Card

Reuse the existing `<CampaignCard variant="default">`. **One change:** add
an optional, prominent CTA button to the footer next to the existing
`tel:` link — "Sună organizatorul" — full-width on mobile.

Add a new variant `'listing'` (or a `showCallCta` prop) so the card stays
unchanged on the organizer preview/confirmation pages. Inside the card:

```html
<a class="campaign-card__cta" :href="`tel:${campaign.phonePublic}`">
  <Phone /> Sună organizatorul
</a>
```

Styling: orange (`--color-accent`) bg, white text, full width on
`max-width: 540px`. Keep the existing inline `tel:` link too (for the
`copy phone number` use case) but it becomes a secondary text link.

### 4.4 Empty / loading / error states

- **Loading** — 3 skeleton cards (CSS shimmer, no extra dep).
- **Empty (no filters)** — *"Nu sunt campanii programate momentan.
  Înscrie-te pe pagina principală și te anunțăm când apare una în zona
  ta."* + button to `/`.
- **Empty (filtered)** — *"Nu sunt campanii viitoare în {județ} pentru
  {specie}."* + a "Vezi toate campaniile" link that clears the filters.
- **Error** — `<UiAlert kind="error">` with retry button. Use
  `extractApiError`.

---

## 5. Frontend pieces to add/change

### 5.1 Server proxy: `server/api/campaigns/index.get.ts` (new)

Copy the SigV4 pattern from `register.post.ts` (without hCaptcha — this is
public read). Forwards `?county=` to `${awsApiBase}/campaigns?county=...`,
parses, returns. Cache hint: `setResponseHeader('cache-control',
'public, max-age=60, s-maxage=300')` — pairs well with the existing
`routeRules['/campanii'].swr: 300`.

### 5.2 Composable: `useCampaigns(filters)` (new)

```ts
function useCampaigns(filters: { county?: Ref<string>; species?: Ref<Species | ''> })
  → { campaigns, loading, error }
```

- Wraps `useFetch('/api/campaigns', { query: { county } })` so SSR works
  and Nuxt handles dedupe.
- The API call is **re-issued only when `county` changes** (watch the
  county ref). When `county === ''` we hit `/api/campaigns` with no query
  param and get the whole country.
- `species` is applied as a **computed filter** over the fetched list —
  it never triggers a refetch. This matches the backend's single-filter
  capability.
- Returned `campaigns` ref is the post-species-filter view; expose
  `total` (pre-filter count) too so the heading can read
  *"3 din 12 campanii pentru pisici"*.

### 5.3 `useLocationData` — add slug helpers

Add to the composable so URL ↔ code conversion lives in one place:

```ts
slugToCountyCode('alba') // → 'AB'
countyCodeToSlug('AB')   // → 'alba'
```

Slug = lowercased `simplu` (or `nume` if `simplu` missing) with `ș/ț/ă/â/î`
stripped via the existing diacritic-safe normalize used by the combobox.

### 5.4 `<CampaignCard>` — add `showCallCta?: boolean`

Default `false` so existing call sites are unaffected. When `true`, render
the orange button described in §4.3.

### 5.5 `app/pages/campanii.vue` — full rewrite

- Reads `judet` and `specie` from `useRoute().query`.
- `watch` query → re-runs `useCampaigns`.
- Filter changes → `router.replace({ query: ... })` (omitting empty
  values).
- Renders hero, filter bar, list, empty/error states.
- `useSeoMeta` is dynamic per filter (see §6).

---

## 6. SEO

### 6.1 Per-filter meta

When `judet` is set:
```
title:       Campanii de sterilizare gratuită în {județul Alba} — Sterilizări Gratuite
description: Vezi campaniile de sterilizare gratuită programate în {Alba}.
             Câini și pisici. Sună direct la organizator.
```

When no filter:
```
title:       Campanii de sterilizare gratuită — toate județele
description: Toate campaniile de sterilizare gratuită active în România.
             Filtrează după județ și sună direct la organizator.
```

### 6.2 Canonical + indexing

- All `?judet=...` URLs are indexable and **self-canonical** (we want
  Google to rank them).
- `?specie=...` URLs are `noindex, follow` and canonical to the no-specie
  version. Reason: avoids duplicate content (`?judet=alba` and
  `?judet=alba&specie=caine` show overlapping results) and we don't have
  unique copy for the specie axis.

### 6.3 Structured data

JSON-LD per campaign using `Event` schema:
```json
{
  "@context": "https://schema.org",
  "@type": "Event",
  "name": "Campanie sterilizare gratuită — Pianu",
  "startDate": "2026-05-12T09:00",
  "endDate":   "2026-05-12T17:00",
  "eventStatus": "https://schema.org/EventScheduled",
  "location": { "@type": "Place", "name": "Pianu", "address": "..." },
  "organizer": { "@type": "Organization", "name": "ONG Patrupede" },
  "isAccessibleForFree": true
}
```

Plus a single `BreadcrumbList` (Acasă → Campanii → {Județ} when filtered).

### 6.4 Routing/render

- Already configured in `nuxt.config.ts` as `routeRules['/campanii'].swr: 300`. Keep.
- Confirm SSR output renders the full card list (view-source check).

---

## 7. IP-based default județ

Marked **deferred** — adds complexity for marginal UX gain.

Options when we do add it:
- Cloudflare's `cf-ipcity`/`cf-ipcountry` headers if we end up behind CF.
- A free service like `ipapi.co` called from the Nuxt server route on
  first visit, county slug stored in a cookie.
- Privacy: never persist beyond a same-site cookie; show a "Schimbă
  județul" affordance prominently.

Decision: ship without IP detection. Default = "toate județele". Revisit
once we have analytics on filter usage.

---

## 8. Edge cases

- **Phone `tel:` on desktop** — links still work, opens default app
  (FaceTime / Skype etc.). Keep — costs us nothing.
- **Duplicate campaigns same locality+date** — backend's job to dedupe;
  frontend renders whatever it gets.
- **Campaign starts today** — show a small "Astăzi" badge. (Cheap; can be
  added in story #5 polish.)
- **County code in API differs from `judete.json`** — log a console
  warning in dev and fall back to showing the raw code in the card.
- **Long organization names** — already handled by `<CampaignCard>`'s
  flex layout; sanity-check at the longest org name we have.

---

## 9. Story breakdown

Sized so each lands in one PR. Order is dependency order.

| # | Title | Dep |
|---|-------|-----|
| 1 | Add `slugToCountyCode` / `countyCodeToSlug` helpers in `useLocationData` | — |
| 2 | Add `server/api/campaigns/index.get.ts` proxy (SigV4, no captcha) | — |
| 3 | Add `useCampaigns(filters)` composable using `useFetch` over the proxy | #2 |
| 4 | Extend `<CampaignCard>` with `showCallCta` prop + button styling | — |
| 5 | Rebuild `pages/campanii.vue`: hero, filter bar, list, empty/error/loading | #1, #3, #4 |
| 6 | Wire dynamic `useSeoMeta` + `Event` JSON-LD per card | #5 |
| 7 | QA pass: mobile, no-results, error, slow network, SSR view-source | all |

**Out of scope for this batch:** detail page, IP geolocation,
pagination, "Astăzi"/"Mâine" relative date badges (nice-to-haves once #1–#8
are merged).

---

## 10. Definition of done

- A user landing on `/campanii?judet=alba` from Google sees a list of
  Alba campaigns server-rendered, with a tappable phone CTA on each card,
  in under 1 second on a mid-tier phone (Lighthouse mobile perf ≥ 85).
- Empty/error states are reachable (force via dev tools) and look
  intentional.
- `view-source` shows full HTML for the campaign list (not just the
  hydration shell) and includes JSON-LD blocks.
- The county filter changes the URL slug, the URL slug changes the list,
  and refreshing the page restores the same view (filter persistence
  through the URL).
- No regressions on `/organizatori` preview or `/confirmare-campanie`
  (the `<CampaignCard>` change is opt-in via `showCallCta`).

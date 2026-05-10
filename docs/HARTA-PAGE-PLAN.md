# `/harta` — Interactive Romania Map Plan

The page that answers two questions at a glance, on one screen:

- *"Unde sunt cei mai mulți oameni care așteaptă o campanie?"* (organizer-facing)
- *"Unde se desfășoară campanii chiar acum?"* (citizen-facing)

A single SVG-backed map, three view modes, an always-visible side panel. No
third-party map library, no tiles, no Leaflet/MapLibre — just inline SVG +
Vue events + CSS variables.

This page **replaces `/despre`** (currently a stub at
`app/pages/despre.vue`, linked from `TopNav.vue:39` and `Footer.vue:27`).
There is no separate "About" page in v1; the brand context lives on `/`.

---

## 1. Goals & non-goals

**Goals**
- One scannable map of Romania showing per-județ activity.
- Three view modes, switchable in-place: **Cerere**, **Ofertă**, **Istoric**.
- Hover a județ → see the number for the active view.
- Click a județ → side panel deep-dives that județ. Click again / Esc /
  outside / different județ swaps it.
- Side panel **always visible** (~25–30% width on desktop) — never hidden,
  never overlay-modal. When nothing is selected, it shows the top 10 by the
  active view's metric so the page is informative on first paint.
- Server-rendered, indexable, fast on mobile.

**Non-goals (now)**
- No zoom/pan/tiles. SVG `viewBox` gives us pinch-zoom on mobile for free
  and we don't need more.
- No "draw your own polygon" / radius search.
- No clustering, no markers — județul **is** the unit.
- No Istoric data v1 (the backend doesn't expose past-campaigns aggregates
  yet). The view's tab exists but renders an "în curând" placeholder.

**Why no map library:** Leaflet/MapLibre are 100–200 KB, expect tile servers
(Mapbox/OSM costs at scale), and don't help us — we render 42 fixed
polygons that never change. A static SVG with `<path>` per județ is ~25 KB
gzipped, themeable via CSS tokens, fully SSR'd, and gives us native DOM
events without a wrapper.

---

## 2. The three views

Each view is a different metric layered on the same map. Switching the view
swaps:
- The number rendered on hover (per județ).
- The default-state panel content (top 10 list).
- The selected-state panel content (per-județ breakdown).
- The page title / meta description.

| View | Active for | Hover metric | Default panel | Selected-județ panel |
|---|---|---|---|---|
| **Cerere** | organizers | Citizens registered in județ | Top 10 județe după cerere | Total + species breakdown + top localities + CTA *"Organizează o campanie aici"* → `/organizatori` |
| **Ofertă** | citizens | Active (approved + upcoming) campaigns in județ | Top 10 județe după ofertă | Total + list of upcoming campaigns (date, locality, organizer) + CTA *"Vezi toate campaniile"* → `/campanii?judet={slug}` |
| **Istoric** | both | Past campaigns in județ | "În curând — nu avem încă date istorice." | Same placeholder. Tab visible but disabled-styled. |

Default view = **Cerere**. Rationale: organizers are the lower-volume,
higher-signal traffic — the page's job is to show them where the demand is.
Citizens already have `/` and `/campanii`; they get the **Ofertă** view as
the natural next click.

---

## 3. Backend contracts

### 3.1 Cerere — `GET /stats/registrations` (no params)

Same upstream the `/api/stats/locality` proxy already calls. **Without**
`?county=` it returns the country-wide aggregate:

```ts
type RegistrationsCountryResponse = {
  byCounty: Record<string, {
    total: number
    localities: Record<string, number>
    species: Record<'dog' | 'cat', number>
  }>
  totalRegistrations: number
}
```

**Ilfov normalization (important).** Today the response includes one
non-conforming key: `"Ilfov"` instead of `"IF"`. Backend is migrating to
strict 2-letter codes; until then the frontend proxy normalizes
defensively:

```ts
// server/api/stats/registrations.get.ts
if (data.byCounty.Ilfov && !data.byCounty.IF) {
  data.byCounty.IF = data.byCounty.Ilfov
  delete data.byCounty.Ilfov
}
```

This isolates the quirk to one place. Once backend is fixed the normalize
becomes a no-op and we delete it.

### 3.2 Ofertă — `GET /campaigns` (no params)

The endpoint planned in `CAMPANII-PAGE-PLAN.md §2`. Returns
`{ campaigns: Campaign[] }` for **all** approved-and-upcoming campaigns.
The map view derives its per-județ counts client-side from this single
list — no new backend endpoint required:

```ts
const counts = groupBy(campaigns, c => c.county.toUpperCase())
const offertaMetric = mapValues(counts, list => list.length)
```

This means **Ofertă view depends on the `/api/campaigns` proxy from
`CAMPANII-PAGE-PLAN.md §5.1`**. If that proxy isn't merged yet, ship `/harta`
with Cerere only and add Ofertă in a follow-up story.

### 3.3 Istoric — deferred

No endpoint exists. Tab renders a placeholder with copy
*"Statisticile campaniilor încheiate vor apărea aici curând."*
Add the proxy + view when the backend exposes the aggregate.

---

## 4. URL & query schema

| Param | Values | Effect |
|---|---|---|
| `view` | `cerere` \| `oferta` \| `istoric` \| omitted | Active view tab. Omitted = `cerere`. |
| `judet` | full county slug (`alba`, `cluj`, `bucuresti`, …) \| omitted | Selected county; drives the side panel. Reuses the slug ↔ code helpers from `CAMPANII-PAGE-PLAN.md §5.3`. |

Examples:
- `/harta` → Cerere view, no județ selected, panel shows top 10.
- `/harta?view=oferta` → Ofertă view, panel shows top 10 by campaign count.
- `/harta?judet=alba` → Cerere view, Alba selected.
- `/harta?view=oferta&judet=alba` → Ofertă view, Alba selected.

URL writes use `router.replace` (no history spam on every hover-then-click).

**Why slug not code in the URL:** consistency with `/campanii?judet=alba`
and SEO. *"sterilizare gratuită alba"* matters; *"AB"* doesn't.

---

## 5. Page layout

```
┌──────────────────────────────────────────────────────────────────────┐
│  Hero (compact, navy)                                                │
│  H1: "Harta sterilizărilor gratuite din România"                     │
│  Sub: "Vezi unde e cea mai mare cerere și unde se țin campanii."     │
│                                                                      │
│  [ Cerere ] [ Ofertă ] [ Istoric ]   ← tabs                          │
│  ─────────────────────────────────────────────────────────────────── │
│                                                                      │
│  ┌─────────────────────────────────────────┐  ┌────────────────────┐ │
│  │                                         │  │                    │ │
│  │           ROMANIA SVG                   │  │   SIDE PANEL       │ │
│  │           (70–75% width)                │  │   (25–30% width)   │ │
│  │                                         │  │                    │ │
│  │   counties shaded by metric             │  │   default:         │ │
│  │   hover → tooltip with number           │  │     top 10 list    │ │
│  │   click → highlight + populate panel    │  │   selected:        │ │
│  │                                         │  │     full breakdown │ │
│  └─────────────────────────────────────────┘  └────────────────────┘ │
│                                                                      │
│  Footer note: "Date actualizate la {timestamp}. Sursa: Build4Paws."  │
└──────────────────────────────────────────────────────────────────────┘
```

### 5.1 Tabs

`<UiTabs>` (build if missing — three buttons w/ active state, ARIA
`role="tablist"`). Tab change writes `?view=` and re-derives metrics. No
network call needed when switching between Cerere/Ofertă if both datasets
are already loaded — both fetch in parallel on first paint.

### 5.2 Map (left)

- Inline SVG, `viewBox="0 0 1000 600"` (or whatever the source uses), CSS
  `width: 100%; height: auto`.
- One `<path>` per județ, `id="RO-AB"`, `data-code="AB"`, `class="county"`.
- Fill computed from the active metric via a CSS custom property:
  ```html
  <path :style="{ '--fill': fillFor(code) }" class="county" />
  ```
  ```css
  .county { fill: var(--fill, var(--color-surface-2)); transition: fill 120ms; }
  .county:hover, .county.is-selected { fill: var(--color-accent); }
  ```
- `fillFor(code)` returns a 5-step ramp based on the metric's percentile
  (quintile bins, not linear — Bucharest dwarfs everything else and a
  linear ramp would wash the rest of the country to one shade).
- Tooltip is a small `<div>` positioned at cursor on `mousemove`, showing
  `{Județ} — {N} {unit}` where `unit` is "înscrieri" / "campanii" /
  "campanii încheiate".
- `tabindex="0"` on each path; Enter/Space selects. Outline ring on
  `:focus-visible` so keyboard users see where they are.

### 5.3 Side panel (right)

Always visible. Two states:

**Default (no județ selected)**
- Heading: e.g. *"Top județe după cerere"*.
- List of top 10 județe, each row: rank, name, value, mini horizontal bar
  (CSS only). Click a row = same as clicking the județ on the map.
- Footer link: *"Vezi datele complete →"* expands to all 42 (still in
  panel, scrollable).

**Selected (a județ is set)**
- Header: județ name, X close button (clears `?judet=`).
- Big number for the active view's metric.
- View-specific content per the table in §2.
- A footer area with cross-view stats: *"În acest județ: X înscrieri ·
  Y campanii active"* — single source of context regardless of which tab
  is active.

### 5.4 Mobile (< 768px)

Stack vertically. Map first (full-width, `aspect-ratio: 4/3`), tabs above
map, panel below — same content, full-width. Tap a județ on the map →
smooth-scroll to panel. Tap-and-hold = tooltip without selecting (long
press triggers tooltip, release without movement triggers select).

---

## 6. Map source & accessibility

### 6.1 Source SVG

Wikimedia Commons: `Romania_counties_blank.svg` (CC-BY-SA 3.0, by user
TUBSEnEs). Pull once, run through SVGO with:
- `removeMetadata`, `removeTitle`, `removeDesc`, `cleanupNumericValues`
  (precision: 2), `mergePaths: false` (we need one path per județ).
- Manually rename each path's `id` to `RO-{ISO 2-letter code}` (script:
  read existing `inkscape:label` / Romanian name, map to ISO code via
  `judete.json`, write back).
- Drop the `<style>` block — styling is in the component.

Result lands at `app/assets/maps/romania-counties.svg` (~20–30 KB).
**License attribution** in the page footer:
*"Hartă bazată pe Romania counties blank (Wikimedia, CC BY-SA 3.0)."*

### 6.2 Why not GeoJSON + d3-geo

We'd save zero bytes (GeoJSON of 42 polygons + d3-geo bundle is bigger
than the SVG), gain the ability to project at runtime (which we don't
need), and add a build-time projection step. Skip.

### 6.3 Accessibility

- Each `<path>`: `role="button"`, `tabindex="0"`,
  `aria-label="Județul Alba — 20 înscrieri"` (recomputed when metric
  changes).
- Tab order = alphabetical by județ name (override via explicit
  `tabindex` rebind if needed; default DOM order from the SVG file is
  fine if we sort paths during the prep step).
- Live region (`aria-live="polite"`) on the side panel header so screen
  readers announce "Alba selectat" when a click happens.
- Color is **never the only signal** — the panel always shows numbers in
  text. The map is a navigation aid, not the data.

---

## 7. Frontend pieces to add/change

### 7.1 `server/api/stats/registrations.get.ts` (new)

Country-wide proxy (no `?county=`). Same SigV4 / `awsApiBase` pattern as
`server/api/stats/locality.get.ts`, no hCaptcha (public read). Returns
the `RegistrationsCountryResponse` shape (§3.1) with the Ilfov
normalization applied. Cache header: `cache-control: public, max-age=60,
s-maxage=300`.

### 7.2 `useRegistrationStats()` composable (new)

```ts
function useRegistrationStats(): {
  byCounty: Ref<Record<string, CountyStats>>
  totalRegistrations: Ref<number>
  loading: Ref<boolean>
  error: Ref<Error | null>
}
```

Wraps `useFetch('/api/stats/registrations')`. SSR-safe.

### 7.3 `useCampaignStats()` derived from `useCampaigns()`

When `/api/campaigns` lands (per `CAMPANII-PAGE-PLAN.md`), derive Ofertă
counts client-side:

```ts
const { campaigns } = useCampaigns({ /* unfiltered */ })
const byCounty = computed(() =>
  campaigns.value.reduce<Record<string, number>>((acc, c) => {
    const code = c.county.toUpperCase()
    acc[code] = (acc[code] ?? 0) + 1
    return acc
  }, {})
)
```

No new backend route, no new server proxy — reuse the campaign list.

### 7.4 `<MapRomania />` component (new)

`app/components/map/Romania.vue`. Auto-imported as `<MapRomania />`.

Props:
```ts
{
  /** code → number; missing codes render with the empty-state fill */
  metric: Record<string, number>
  /** unit string for tooltip + a11y label, e.g. "înscrieri" */
  unit: string
  /** currently selected 2-letter code (no RO- prefix) */
  selected?: string
  /** quintile vs linear; default 'quintile' */
  scale?: 'quintile' | 'linear'
}
```

Emits:
```ts
{
  hover: (code: string | null) => void  // null on mouseleave
  select: (code: string) => void
}
```

The component is **stateless** about the data — the parent owns the metric
map, selected code, and panel. The component owns: the SVG, the tooltip
DOM, hover/focus visuals, keyboard handling.

### 7.5 `<MapSidePanel />` component (new)

`app/components/map/SidePanel.vue`. Renders default-vs-selected branches
described in §5.3. Driven by props:

```ts
{
  view: 'cerere' | 'oferta' | 'istoric'
  selected?: string                          // county code
  countyData?: CountyStats                   // for Cerere selected state
  countyCampaigns?: Campaign[]               // for Ofertă selected state
  topTen: Array<{ code: string; value: number }>
}
```

Emits `select(code)` (clicking a row in the top-10 list) and
`clear()` (× button when selected).

### 7.6 `app/pages/harta.vue` (new)

- Reads `view`, `judet` from `useRoute().query`.
- In parallel: `useRegistrationStats()` always; `useCampaigns()` when view
  is `oferta` or to keep the cross-view footer line accurate (§5.3).
- Computes `metric` for the active view.
- Renders hero + tabs + two-column layout (map + panel).
- Wires emits: tab change / map click / panel row click → `router.replace`.
- `useSeoMeta` per view (§9).

### 7.7 Delete `/despre`, point links at `/harta`

- Delete `app/pages/despre.vue`.
- `TopNav.vue:39` — change `{ to: '/despre', label: 'Despre noi' }` to
  `{ to: '/harta', label: 'Harta' }`.
- `Footer.vue:27` — change `<NuxtLink to="/despre">Despre noi</NuxtLink>`
  to `<NuxtLink to="/harta">Harta</NuxtLink>`.
- `nuxt.config.ts` `routeRules` — add `'/despre': { redirect: '/harta' }`
  so any external/old links 301 to the new page. Add
  `'/harta': { swr: 300 }` matching `/campanii`.

---

## 8. Data shape & normalization

```ts
// app/types/map.ts (new)
export type CountyMetric = 'cerere' | 'oferta' | 'istoric'

export interface CountyStats {
  total: number
  localities: Record<string, number>
  species: Record<'dog' | 'cat', number>
}

export interface RegistrationsCountryResponse {
  byCounty: Record<string, CountyStats>   // 2-letter codes only
  totalRegistrations: number
}
```

Re-export from `app/types/index.ts`.

The 2-letter code is the **canonical key** everywhere internal — slug
conversion happens only at the URL boundary, name conversion only at the
render boundary (using `useLocationData`).

---

## 9. SEO

### 9.1 Per-view meta

Cerere (default):
```
title:       Harta sterilizărilor gratuite din România — cerere
description: Vezi în ce județe sunt cei mai mulți oameni care așteaptă o
             campanie de sterilizare gratuită.
```

Ofertă:
```
title:       Harta campaniilor de sterilizare gratuită în România
description: Vezi pe hartă unde se desfășoară campanii de sterilizare
             gratuită chiar acum.
```

Istoric: `noindex` while placeholder; meta updated when data lands.

### 9.2 Indexing

- `/harta` and `/harta?view=oferta` are indexable, self-canonical.
- `?judet=...` URLs canonical to the same view without a județ — they're
  navigation states, not unique pages.
- `/despre` 301-redirects to `/harta` (any backlinks pass equity).

### 9.3 Structured data

`Dataset` JSON-LD listing the per-județ counts for the active view. Helps
Google understand the page is a data visualization. Skip if it's
flagged as thin during testing.

---

## 10. Edge cases

- **Județ has no data** — render with the lowest-quintile fill, tooltip
  shows *"0 {unit}"*, panel selected-state shows zero values without
  errors. Don't hide the județ.
- **Backend returns Ilfov as full name** — proxy normalization handles it
  (§3.1). Log a console warning in dev mode so we know when backend ships
  the fix.
- **Backend returns an unknown 2-letter code** — log + skip. Never crash
  the map.
- **`useCampaigns` errors but `useRegistrationStats` succeeds** — Ofertă
  view shows an inline error in the panel; Cerere view still works.
- **All metrics are zero** (cold start, no users registered) — tooltip
  still shows "0 înscrieri", panel shows *"Niciun județ înregistrat
  încă"* in the top-10 slot.
- **Mobile pinch-zoom on SVG** — works natively via CSS `touch-action`.
  Don't override.
- **Bucharest (B) inside Ilfov (IF)** — both are separate paths in the
  SVG; B sits inside IF visually. Make sure z-index has B rendering
  above IF (path order in the source SVG). Hover on B doesn't trigger
  IF's tooltip.

---

## 11. Story breakdown

Sized for one PR each. Order is dependency order.

| # | Title | Dep |
|---|-------|-----|
| 1 | Source + prep `romania-counties.svg`: SVGO pass, rename ids to `RO-XX`, sort paths alphabetically by județ name, commit to `app/assets/maps/` | — |
| 2 | Add `<MapRomania />` component: inline SVG, hover tooltip, click/keyboard select, fill via `--fill` CSS var, quintile scale | #1 |
| 3 | Add `server/api/stats/registrations.get.ts` (country-wide, SigV4, Ilfov normalize, cache headers) | — |
| 4 | Add `useRegistrationStats()` composable | #3 |
| 5 | Add `<MapSidePanel />` component (default top-10 + selected breakdown) — Cerere shape only in this story | — |
| 6 | Build `app/pages/harta.vue` with Cerere view only, two-column layout, tabs (Ofertă/Istoric disabled), URL sync | #2, #4, #5 |
| 7 | Replace `/despre`: delete page, update `TopNav` + `Footer`, add 301 redirect rule, add `/harta` swr rule | — |
| 8 | Wire Ofertă view: derive metric from `useCampaigns`, extend `<MapSidePanel />` with campaign-list selected state, enable the tab | #6, **CAMPANII-PAGE-PLAN #2/#3** |
| 9 | SEO: per-view dynamic `useSeoMeta`, `Dataset` JSON-LD, `noindex` on `/harta?view=istoric` | #6 |
| 10 | Mobile pass: stack layout, tap-and-hold tooltip behavior, smooth-scroll to panel on select | #6 |
| 11 | A11y pass: `aria-label` per path, live region on panel, focus ring, keyboard nav verification | #6 |
| 12 | QA pass: SSR view-source check, slow network, SVG render at 320px wide, screen reader smoke test | all |

**Out of scope this batch:** Istoric data + view, IP-based default județ
preselect, animated transitions between views, choropleth legend
component (the side panel's bar chart is the legend).

---

## 12. Definition of done

- A user landing on `/harta` from Google sees the Cerere view, full map
  rendered server-side, side panel showing the top 10 județe — under 1.5s
  on a mid-tier phone.
- Hover any județ → tooltip with the number for the active view.
- Click any județ → side panel updates with that județ's full breakdown +
  CTA appropriate to the active view.
- Switching tabs (Cerere ↔ Ofertă) updates the map fill, the tooltip
  numbers, the panel — without a page reload, with `?view=` in the URL.
- `/despre` returns a 301 to `/harta`. No nav/footer link points to
  `/despre` anywhere in the codebase.
- `view-source` shows the SVG inline (not a hydration shell) and the
  panel's top-10 already populated — JS-disabled visitors and Googlebot
  see the same data.
- No new runtime dependencies in `package.json`.
- Lighthouse mobile: perf ≥ 85, a11y ≥ 95.

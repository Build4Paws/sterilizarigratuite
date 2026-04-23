# Frontend Action Plan — Sterilizări Gratuite

## Context

Build4Paws needs a platform to centralize free animal sterilization campaigns in Romania. The frontend is a lightweight Nuxt 3 + TypeScript app that displays data from AWS APIs and handles form submissions. No heavy logic lives in the frontend — it's a thin presentation + routing layer optimized for SEO.

---

## Phase 1: Project Scaffolding & Core Setup

### 1.1 Initialize Nuxt 3 project
- `npx nuxi@latest init` with TypeScript enabled
- Configure `nuxt.config.ts`:
  - SSR enabled (default) — critical for SEO
  - `routeRules` for static/ISR pages where applicable
  - HTML lang set to `ro`
  - Meta defaults (charset, viewport, og tags)
- Install minimal dependencies:
  - `@nuxtjs/seo` (meta, sitemap, robots, og)
  - `@vueuse/nuxt` (composables for form state, intersection observer, etc.)
  - `@hcaptcha/vue3-hcaptcha` (invisible captcha on forms)

### 1.2 Project structure
```
frontend/
├── assets/           # CSS/SCSS, fonts, static images
├── components/
│   ├── ui/           # Buttons, inputs, dropdowns, badges (design system)
│   ├── forms/        # CitizenForm, CampaignForm
│   ├── campaign/     # CampaignCard, CampaignList, CampaignFilters
│   └── layout/       # TopNav, Footer, HeroBanner
├── composables/      # useLocationData, useApi, useFormValidation
├── layouts/          # default.vue (nav + footer)
├── pages/            # File-based routing (see Phase 2)
├── plugins/          # hCaptcha plugin
├── public/           # favicon, robots.txt
├── server/           # Nuxt server routes (proxy to AWS API if needed)
├── types/            # TypeScript interfaces (Campaign, Citizen, Organizer, etc.)
└── utils/            # formatDate, phone formatting, etc.
```

### 1.3 API integration layer
- Create `composables/useApi.ts` — thin wrapper around `useFetch` / `$fetch` pointing to AWS API Gateway base URL
- Environment-based API URL (`NUXT_PUBLIC_API_BASE`)
- TypeScript interfaces in `types/` for all API responses:
  - `Campaign`, `Citizen`, `Organizer`
  - `LocationData` (județ + localitate lists)
- **No backend logic** — all data shaping happens in the API, frontend just renders

### 1.4 Location data composable
- `composables/useLocationData.ts` — fetches județe list, then localități filtered by selected județ
- Handles București → sector mapping
- Source: API endpoint (backed by the județe/localități dataset)
- Cached on client after first load (or SSR-hydrated)

---

## Phase 2: Pages & Routing

### 2.1 Homepage (`/` — `pages/index.vue`)
- **Hero section**: headline + citizen registration form (inline, not a separate page)
  - CTA: *"Te anunțăm când se organizează sterilizare gratuită în zona ta"*
  - Form fields: Nume, Telefon SAU Email, Județ, Localitate, Specii (checkboxes + count), GDPR checkbox
  - Invisible hCaptcha on submit
  - On success → redirect to `/confirmare` with query params or store state
- **Bottom band** (below fold):
  - Link to `/campanii`: *"Vezi campaniile active acum →"*
  - Link to `/organizatori`: *"Ești ONG/primărie? Anunță o campanie"*
- SEO: `<title>`, `<meta description>`, structured data (Organization, WebSite)

### 2.2 Campaigns page (`/campanii` — `pages/campanii.vue`)
- Public, read-only, SSR-rendered (critical for SEO)
- **Upcoming approved campaigns** listed
- **Filter**: județ dropdown (updates URL query param for shareable links)
- Each campaign rendered as a card: localitate, date, species, phone (or "Sold Out" badge), organizer name
- Structured data: `Event` schema for each campaign
- Pagination or "load more" if list grows

### 2.3 Organizer landing (`/organizatori` — `pages/organizatori.vue`) ✅ Built
- Hero (navy bg, orange `Megaphone` icon, curved divider) + elevated form-card overlapping the hero
- "Cum funcționează" 3-step row (`FilePlus2` / `ShieldCheck` / `Send`) with numbered badges
- FAQ section using native `<details>` (5 questions: who can publish, cost, notification flow, edits, public data)
- Embeds `<FormsCampaignForm />`:
  - Two-step wizard — **fill** then **preview** (renders the real `<CampaignCard variant="pending">`)
  - Inline "X persoane așteaptă" pill via `useLocalityWaitingCount` (mocked at `GET /api/stats/locality`)
  - Same checkbox to reuse contact phone as public phone (default checked)
  - Multi-day checkbox; end-time validation only enforced for single-day campaigns
- On submit → `POST /api/campaigns/submit` (proxied through Nuxt server route — currently mocked, see `docs/CAMPAIGNS-FLOW-PLAN.md` §5) → session stored in `useOrganizerSubmission` → redirect to `/confirmare-campanie`
- See `docs/CAMPAIGNS-FLOW-PLAN.md` for full type/contract/story breakdown

### 2.4 Citizen confirmation (`/confirmare` — `pages/confirmare.vue`)
- Post-submit page with:
  - Confirmation message: *"Ești înscris, te anunțăm pe [SMS/email]"*
  - Context: *"Mai sunt X persoane din [județ] care așteaptă"* (fetched from API)
  - Link to sterilization guide
  - Magic link display (for managing subscription)
- `noindex` meta (no SEO value, private confirmation)

### 2.5 Organizer confirmation (`/confirmare-campanie` — `pages/confirmare-campanie.vue`) ✅ Built
- Hydrates from `useOrganizerSubmission` (sessionStorage); redirects to `/organizatori` if no session
- Header: green `CircleCheck` + "Mulțumim, {organizationName}!" + lead text mentioning the 24h SLA and the contact email
- Preview block: re-renders the `<CampaignCard variant="pending">` so the organizer sees what they submitted
- Stats block (only when `stats` is present): "X persoane din {localitate} … încă Y din restul județului așteaptă o campanie"
- Meta block: submission ID (in `<code>`), submit timestamp formatted in `ro-RO`, status pill ("În așteptarea aprobării")
- `noindex, nofollow`

### 2.6 Citizen management (`/m/[token]` — `pages/m/[token].vue`)
- Magic link page, no login required
- MVP: two buttons — "Dezabonare" and "Șterge complet datele (GDPR)"
- Token validated by API
- `noindex`

### 2.7 Refresh confirmation (`/r/[token]` — `pages/r/[token].vue`)
- Post-campaign refresh page
- Two options: *"Da, ține-mă pe listă"* / *"Nu, dezabonează-mă"*
- `noindex`

---

## Phase 3: Shared Components & Forms

### 3.1 UI components (design-system-ready)
Build with **minimal styling first** (semantic HTML + basic CSS), then apply design system when PDF arrives:
- `UiButton` — primary/secondary/ghost variants
- `UiInput` — text, tel, email with label + error state
- `UiSelect` — dropdown (județ, localitate, species counts)
- `UiCheckbox` — GDPR, species, multi-day toggle
- `UiBadge` — sold out, pending, approved statuses
- `UiCard` — campaign card wrapper
- `UiAlert` — success/error/info messages

### 3.2 Form components
- `CitizenForm` — used on homepage, handles all citizen registration logic
  - Phone OR email validation (at least one required)
  - Conditional species count fields
  - hCaptcha integration
  - Client-side validation with clear Romanian error messages
- `CampaignForm` — used on `/organizatori`
  - Multi-step: fill → preview → submit
  - "X persoane așteaptă" counter fetched on localitate selection
  - Conditional multi-day fields
  - Conditional species slot counts

### 3.3 Layout components
- `TopNav` — responsive nav: Acasă / Campanii / Organizatori / Despre noi
- `Footer` — links, legal, GDPR policy link
- `HeroBanner` — homepage hero with embedded form

---

## Phase 4: SEO & Performance

### 4.1 SEO setup
- `@nuxtjs/seo` module configured:
  - Auto-generated `sitemap.xml` (include `/`, `/campanii`, `/organizatori`)
  - `robots.txt` (disallow `/m/`, `/r/`, `/confirmare*`)
  - OG tags per page (title, description, image)
- Structured data (JSON-LD):
  - Homepage: `Organization` + `WebSite` with `SearchAction`
  - `/campanii`: `ItemList` + individual `Event` per campaign
  - Per campaign: `Event` with location, date, organizer
- Semantic HTML throughout (`<main>`, `<article>`, `<nav>`, `<section>`, headings hierarchy)
- Romanian `<html lang="ro">`, proper `hreflang` if bilingual later

### 4.2 Performance
- Minimal client JS — most pages are SSR, forms hydrate on client
- No heavy UI libraries (no Vuetify, no Tailwind UI — keep bundle small)
- Lazy-load below-fold components (`<LazyComponent>`)
- Image optimization via `<NuxtImg>` if images are used
- Font strategy: system fonts or single self-hosted font (from design system)
- Target: Lighthouse 90+ on all core pages

---

## Phase 5: Design System Integration

> **Blocked until:** design system PDF is provided (~2026-04-15)

### 5.1 Apply design tokens
- Extract from PDF: colors, typography, spacing, border-radius, shadows
- Create `assets/css/variables.css` (CSS custom properties)
- Apply to all UI components

### 5.2 Refine components
- Match exact visual spec from design system
- Responsive breakpoints per design
- Interaction states (hover, focus, disabled, error)

---

## Phase 6: Integration & Polish

### 6.1 Connect to real API
- Replace any mock/placeholder data with real AWS API Gateway calls
- Error handling: friendly Romanian messages for network/API errors
- Loading states on all data-fetching pages

### 6.2 Form edge cases
- Deduplication flow: display "already registered" message when API returns conflict
- Rate limit feedback (if API returns 429)
- hCaptcha error handling

### 6.3 Accessibility
- Keyboard navigation on all forms
- ARIA labels on interactive elements
- Focus management after form submit
- Color contrast per WCAG AA

### 6.4 Testing & Launch prep
- Manual testing of all flows (citizen registration, campaign submit, magic links)
- Lighthouse audit on all pages
- Check all meta tags / OG previews
- Verify SSR output (view-source on key pages)
- 404 page with helpful navigation

---

## Out of Scope (Backend)
- SMS/email sending (Lambda)
- Admin approval flow
- hCaptcha server-side verification
- Rate limiting logic
- DynamoDB operations
- Token generation
- Bounce detection
- Cron jobs (refresh post-campanie, cleanup)

---

## v2 — Deferred Features
- **Cabinete permanente** — `/cabinete-permanente` landing page + registration form + display on `/campanii` and `/confirmare`
- Organizer profiles & dashboard (magic link auth, campaign history, public profile)
- Sold Out toggle for campaigns
- Citizen self-service editing (phone, email, localitate, specii)
- Web check-in ("Am sterilizat animalul")
- WhatsApp as notification channel
- Bilingual support (RO + EN)

### Open questions for organizer flow v2
- Edit/withdraw flow for an `pending` submission without going through email
- Magic-link login for organizers so they can see all their past campaigns
- Notification preferences (which channels to use when announcing the campaign to citizens)
- Should organizers be able to upload a logo / cover image on the campaign card?

---

## Execution Order Summary

| Step | Phase | Depends on |
|------|-------|------------|
| 1 | Scaffolding + config | Nothing |
| 2 | Pages + routing (with placeholder content) | Phase 1 |
| 3 | Components + forms (with client validation) | Phase 1 |
| 4 | SEO + performance | Phases 2-3 |
| 5 | Design system application | PDF delivery |
| 6 | API integration + polish | API availability + Phase 2-4 |

Phases 2, 3, and 4 can be worked on in parallel once scaffolding is done. Phase 5 is independent and slots in whenever the design PDF arrives.

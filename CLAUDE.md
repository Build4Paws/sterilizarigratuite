# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Build4Paws platform connecting Romanian citizens with free animal sterilization campaigns ("Campanii de sterilizare"). Two MVP flows:

- **Citizen** — register on `/` to be notified by SMS/email when a campaign appears in their locality.
- **Organizer** — ONGs/primării submit a campaign on `/organizatori` for admin approval.

Romanian-only for MVP. SEO is a top priority — the site is SSR-rendered and structured-data-aware. The frontend is intentionally a thin presentation/routing layer; data shaping lives in the backend (AWS API Gateway + Lambda + DynamoDB).

The full plan and 14-story breakdown for the organizer flow lives in `docs/CAMPAIGNS-FLOW-PLAN.md`. The broader frontend roadmap is in `docs/FRONTEND-PLAN.md`. **Read these before re-deriving design decisions from code.**

## Commands

All commands run from `frontend/`. Requires **Node 24+** (Windows nvm has a quirk where `nvm use 24` doesn't always persist — verify with `node -v` before running).

```bash
npm run dev         # Nuxt dev server
npm run build       # Production build
npm run generate    # Static generation (only homepage is prerendered)
npm run preview     # Preview the production build
npm run typecheck   # Type-check via nuxi (strict mode is on)
```

There is no test runner, no linter, no formatter configured. Don't claim "tests pass" — say so explicitly when verification isn't possible.

## Architecture

### Repo layout

```
frontend/              Nuxt 4 app (THE codebase — everything below is inside it)
├── app/               Nuxt 4 srcDir — pages, components, composables, types, utils
│   ├── pages/         File-based routes (index, campanii, organizatori, confirmare*, m/[token], r/[token])
│   ├── components/    ui/, forms/, campaign/, layout/  (auto-imported, prefix = directory: <FormsCampaignForm/>)
│   ├── composables/   Auto-imported via Nuxt
│   ├── types/         Re-exported from types/index.ts; import as `from '~/types'`
│   ├── utils/         validators.ts, format.ts, api-error.ts (auto-imported)
│   └── assets/        css/main.css holds ALL design tokens (CSS custom properties)
├── server/api/        Nuxt server routes — proxy AWS API + sign requests (see "Security boundary")
└── nuxt.config.ts     runtimeConfig + routeRules + SEO config
docs/                  Planning docs — CAMPAIGNS-FLOW-PLAN.md, FRONTEND-PLAN.md
```

Note: this is **Nuxt 4** (`compatibilityVersion: 4`), so source lives under `app/` not the project root. Don't put new pages/components at `frontend/pages/` — they won't resolve.

### Security boundary: server routes proxy AWS

The browser never talks to AWS API Gateway directly. The pattern in `server/api/register.post.ts` and `server/api/campaigns/submit.post.ts` is the canonical shape — copy it for any new endpoint:

1. Read AWS creds + `awsApiBase` from `useRuntimeConfig()` (server-only — never `public.*`).
2. If `hcaptchaSecretKey` is set, verify the `hcaptchaToken` from the request body against `https://api.hcaptcha.com/siteverify`. Empty secret = dev mode, skip verify.
3. Sign the upstream request with `aws4fetch` (`AwsClient`, service `execute-api`).
4. Forward error bodies back as `data` on a `createError({ statusCode, statusMessage, data })` so `extractApiError` on the client can map backend error codes (`duplicate_submission`, `validation_failed`, `captcha_failed`, etc.) to Romanian copy.

The base URL defaults to `https://api.sterilizarigratuite.ro` and is overridable via `AWS_API_BASE`. Backend routes currently in use: `POST /register`, `POST /organizers` (campaign submit). Backend has also exposed `GET /organizers/{id}` and `GET /campaigns?county=...` — frontend wiring for these is pending.

### Known mocks/stubs (don't ship to prod assuming these are real)

- `server/api/stats/locality.get.ts` — full mock with deterministic pseudo-random counts. No backend `/stats/locality` route exists yet. Replace using the SigV4 pattern when it does.
- `app/composables/useClinics.ts` — returns `[]`; v2 work for permanent clinics.
- `app/pages/campanii.vue` — placeholder; `GET /campaigns` is now available but not wired up.

### Form pattern (CitizenForm + CampaignForm)

Both forms follow the same UX rule: **submit-only validation**. Errors are stored in an `errors` map but only rendered when `submitted === true`. `useFormValidation` is available but the campaign/citizen forms compute errors inline since they have cross-field rules (phone-or-email, multi-day, conditional species slots).

`CampaignForm` is a two-step inline wizard (no route change) — `step === 1` is fill, `step === 2` is preview that renders a real `<CampaignCard variant="pending">`. The parent page listens to `@step-change` to swap hero copy/icon. On submit it stores the result in `useOrganizerSubmission` (sessionStorage) and navigates to `/confirmare-campanie`, which hydrates from that session and redirects to `/organizatori` if missing.

`useCitizenSession` follows the same shape for the citizen flow and `/confirmare`.

### Component reuse

- `<CampaignCard>` is the **single source of truth** for how a campaign renders — used by the organizer preview step *and* (eventually) `/campanii`. It accepts `CampaignCardData` (county code already resolved to county name by the caller).
- Phones use `<UiPhoneInput>` and the `+40 xxx xxx xxx` format. `stripPhone` + `PHONE_RE` in `utils/validators.ts` are the canonical normalize/validate pair — prefer these over re-deriving.
- Date/time inputs are `<UiInput type="date|time" />` (extended in story #1) — don't introduce a separate date-picker component.

### SEO + routing rules

- `nuxt.config.ts` `routeRules` controls per-route behavior: `/` is prerendered, `/campanii` is SWR 300s, `/confirmare*` and `/m/**`/`/r/**` are `robots: false`. `/confirmare` is also `ssr: false` because it relies on sessionStorage hydration.
- `useSeoMeta` is set per page; magic-link and confirmation pages add `robots: 'noindex, nofollow'`.

## Conventions worth knowing

- **Component import prefix follows the directory.** `<FormsCampaignForm />` resolves to `app/components/forms/CampaignForm.vue`. Same for `<UiButton/>`, `<CampaignCard/>`, `<LayoutFooter/>`.
- **Always import types from `~/types`** (the barrel file in `app/types/index.ts`), not the individual files.
- **All user-facing strings are in Romanian.** When writing copy, match the tone of existing pages — friendly, second-person ("Te anunțăm…", "Mulțumim, …!").
- **Design tokens live only in `app/assets/css/main.css`** — colors, spacing, font sizes, radii are CSS custom properties (`--color-primary`, `--space-md`, etc.). Don't hardcode hex values in component `<style scoped>` blocks; use the tokens.
- **Backend error codes** (`duplicate_submission`, `validation_failed`, `captcha_failed`, `rate_limited`, `server_error`, `duplicate_registration`) have Romanian copy in `utils/api-error.ts`. If the backend adds a new code, map it there rather than hand-rolling a message in a component.

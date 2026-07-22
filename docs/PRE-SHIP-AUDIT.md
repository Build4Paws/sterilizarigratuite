# Pre-Ship Audit — sterilizari-gratuite.ro MVP

> Audit date: 2026-05-10
> Auditor: deep code review across Vue 3 / Nuxt 4 / AWS proxy / SEO best practices.
> Scope: `frontend/` Nuxt 4 app + `server/api/` proxy routes + nuxt config + deployment posture.

This document is structured as a backlog of self-contained tasks. Each task includes:
- **Problem** — what is wrong and why it matters.
- **Where** — exact file paths and line numbers.
- **Recommended solution** — concrete steps a coding agent can execute.
- **Acceptance** — how to verify the fix works.

You can hand a single task to Claude Sonnet (or any agent) by copy/pasting one section.

---

## Table of contents

**Ship-blockers (do before launch)**
1. [Broken link to non-existent `/campanie/[id]` page](#1-broken-link-to-non-existent-campanieid-page)
2. [Missing sitemap source endpoint `/api/__sitemap__/urls`](#2-missing-sitemap-source-endpoint-apisitemap_urls)
3. [hCaptcha "fail-open" when secret is empty](#3-hcaptcha-fail-open-when-secret-is-empty)
4. [Decide and document AWS credential strategy for production](#4-decide-and-document-aws-credential-strategy-for-production)
5. [JSON-LD `</script>` injection vector in inline structured data](#5-json-ld-script-injection-vector-in-inline-structured-data)
6. [Invalid TypeScript version pin (`^6.0.2`)](#6-invalid-typescript-version-pin-602)
7. [Suspicious `lucide-vue-next: ^1.0.0` version](#7-suspicious-lucide-vue-next-100-version)

**Security & abuse hardening**
8. [No security response headers](#8-no-security-response-headers)
9. [No rate limiting on Nuxt server proxy](#9-no-rate-limiting-on-nuxt-server-proxy)
10. [`v-html` on user-derivable strings](#10-v-html-on-user-derivable-strings)
11. [Unsigned-fetch fallback in stats endpoints](#11-unsigned-fetch-fallback-in-stats-endpoints)
12. [No upstream timeouts on AWS / hCaptcha calls](#12-no-upstream-timeouts-on-aws--hcaptcha-calls)
13. [Deprecated `process.dev` usage](#13-deprecated-processdev-usage)

**SEO**
14. [Decide whether to enable OG images](#14-decide-whether-to-enable-og-images)
15. [Add canonical links on every indexable page](#15-add-canonical-links-on-every-indexable-page)
16. [Tidy redundant robots disallow entries](#16-tidy-redundant-robots-disallow-entries)
17. [Use ISO 3166-2 codes for `addressRegion` in Schema.org](#17-use-iso-3166-2-codes-for-addressregion-in-schemaorg)
18. [Don't hardcode site URL in JSON-LD](#18-dont-hardcode-site-url-in-json-ld)
19. [Self-host Google Fonts via `@nuxt/fonts` for LCP](#19-self-host-google-fonts-via-nuxtfonts-for-lcp)
20. [Add `error.vue` for branded 404/500](#20-add-errorvue-for-branded-404500)

**Vue/Nuxt patterns**
21. [Remove dead-code `useFormValidation` composable](#21-remove-dead-code-useformvalidation-composable)
22. [Move module-level state into `useState`](#22-move-module-level-state-into-usestate)
23. [Standardize on `withDefaults(defineProps())`](#23-standardize-on-withdefaultsdefineprops)
24. [Fix heading hierarchy (skipping H2)](#24-fix-heading-hierarchy-skipping-h2)
25. [Add explicit keys to `useFetch` calls](#25-add-explicit-keys-to-usefetch-calls)
26. [Add `rel="noopener"` to `target="_blank"` NuxtLinks](#26-add-relnoopener-to-targetblank-nuxtlinks)

**Production readiness**
27. [Pin `nitro.preset` for the deploy target](#27-pin-nitropreset-for-the-deploy-target)
28. [Add structured server logging](#28-add-structured-server-logging)
29. [Drop unused heavy dependencies](#29-drop-unused-heavy-dependencies)
30. [Decide on `useClinics` stub: ship data or remove section](#30-decide-on-useclinics-stub-ship-data-or-remove-section)
31. [Add minimal CI (typecheck + smoke test)](#31-add-minimal-ci-typecheck--smoke-test)
32. [Wrap forms in `<NuxtErrorBoundary>`](#32-wrap-forms-in-nuxterrorboundary)

---

## Ship-blockers (do before launch)

### 1. Broken link to non-existent `/campanie/[id]` page

**Problem.** After an organizer submits a campaign, the confirmation page renders a CTA labeled "Vezi pagina campaniei tale" that links to `/campanie/${session.campaignId}`. There is no such route in the project — `app/pages/campanie/` does not exist. Every organizer who submits and clicks the CTA will see a 404. This is the worst possible last impression for a paying-attention-and-actively-clicking user.

**Where.**
- `frontend/app/pages/confirmare-campanie.vue:54` — the broken `NuxtLink`.
- `frontend/app/pages/` — no `campanie/[id].vue` file.

**Recommended solution.** Pick one of the following:

**Option A — Remove the CTA for MVP.** Delete the entire `confirmare__cta` block (`frontend/app/pages/confirmare-campanie.vue:53-62`). The user already sees the campaign preview card on this page; the CTA is redundant for now.

**Option B — Build the public campaign detail page.** Create `frontend/app/pages/campanie/[id].vue` that:
1. Reads `id` from `route.params`.
2. Calls a new `/api/campaigns/[id].get.ts` server route that signs a `GET /campaigns/{id}` request to AWS API Gateway (mirror the pattern from `frontend/server/api/campaigns/index.get.ts`).
3. Renders a `<CampaignCard>` for the returned campaign, plus an "În așteptare" status badge if not approved yet.
4. Sets `useSeoMeta({ robots: 'noindex, nofollow' })` while pending; flip to `index, follow` once approved.
5. Adds 404 handling (`createError({ statusCode: 404, fatal: true })`) when the API returns 404.

For MVP, **prefer Option A**. The detail page is on the v1.5 roadmap.

**Acceptance.** Submit a campaign in dev and confirm either (A) no broken link is visible on `/confirmare-campanie`, or (B) clicking the CTA loads a working page that renders the campaign.

---

### 2. Missing sitemap source endpoint `/api/__sitemap__/urls`

**Problem.** `nuxt.config.ts` declares a dynamic sitemap source, but the corresponding server route does not exist. The `@nuxtjs/sitemap` module silently falls back to auto-discovered static routes only, so dynamic county-faceted URLs (`/campanii?judet=alba`, `/harta?view=oferta&judet=cluj`, etc.) will never appear in `sitemap.xml`. For an SEO-priority site, this is a wasted distribution channel.

**Where.**
- `frontend/nuxt.config.ts:60-62` — `sitemap.sources: ['/api/__sitemap__/urls']`.
- `frontend/server/api/__sitemap__/` — directory does not exist.

**Recommended solution.**

Create `frontend/server/api/__sitemap__/urls.get.ts`:
```ts
import judete from '~/assets/data/judete.json'

interface SitemapUrl {
  loc: string
  lastmod?: string
  changefreq?: 'daily' | 'weekly' | 'monthly'
  priority?: number
}

export default defineEventHandler((): SitemapUrl[] => {
  const urls: SitemapUrl[] = []

  // One URL per county for /campanii
  for (const j of judete.judete) {
    const slug = j.nume
      .normalize('NFD').replace(/[̀-ͯ]/g, '')
      .toLowerCase().replace(/\s+/g, '-')
    urls.push({
      loc: `/campanii?judet=${slug}`,
      changefreq: 'daily',
      priority: 0.8,
    })
    urls.push({
      loc: `/harta?judet=${slug}`,
      changefreq: 'weekly',
      priority: 0.6,
    })
  }

  return urls
})
```

If `judete.json` import doesn't work directly in a server route, replicate the load via `await import('~/assets/data/judete.json')` and `.default`.

**Acceptance.**
- `npm run dev`, then `curl http://localhost:3000/sitemap.xml | head -50` lists `/campanii?judet=...` URLs for all 42 counties.
- Run a sitemap validator (Google Search Console "Test Sitemap") in staging.

---

### 3. hCaptcha "fail-open" when secret is empty

**Problem.** Both `register.post.ts` and `campaigns/submit.post.ts` skip captcha verification entirely when `HCAPTCHA_SECRET_KEY` is empty. This is intentional for local dev — but it's also exactly what happens if someone forgets to set the env var in production. The frontend widget still renders (because the public site key is set), so the form looks protected, but submissions go through unverified. Result: silent spam vector.

**Where.**
- `frontend/server/api/register.post.ts:31` — `if (secret) { ... }` guard.
- `frontend/server/api/campaigns/submit.post.ts:37` — same guard.
- `frontend/.env` — `HCAPTCHA_SECRET_KEY=` (empty in current local env).

**Recommended solution.**

Add a startup-time guard so the server fails loudly if production lacks the secret. Easiest place is a Nitro plugin:

Create `frontend/server/plugins/check-env.ts`:
```ts
export default defineNitroPlugin(() => {
  const config = useRuntimeConfig()
  const isProd = !import.meta.dev

  if (isProd) {
    const required = ['hcaptchaSecretKey', 'awsAccessKeyId', 'awsSecretAccessKey', 'awsApiBase']
    const missing = required.filter(k => !config[k as keyof typeof config])
    if (missing.length) {
      throw new Error(`[startup] Missing required env: ${missing.join(', ')}`)
    }
  }
})
```

Also harden the runtime guards. In both `register.post.ts:31` and `campaigns/submit.post.ts:37`, replace:
```ts
if (secret) { ... }
```
with:
```ts
if (!secret && !import.meta.dev) {
  throw createError({ statusCode: 500, statusMessage: 'Captcha not configured.' })
}
if (secret) { ... }
```

**Acceptance.**
- `NODE_ENV=production npm run preview` with empty `HCAPTCHA_SECRET_KEY` → server fails to start with a clear error.
- `NODE_ENV=production` with the key set → server starts; submitting without a captcha token returns 400.
- `npm run dev` with empty key → continues to work as before (skips verify).

---

### 4. Decide and document AWS credential strategy for production

**Problem.** Local `.env` contains STS temporary credentials (`AWS_ACCESS_KEY_ID=ASIA...` + `AWS_SESSION_TOKEN=...`). These expire (usually within hours) and are unsuitable for prod. There is no documented production credential plan. Three concrete risks:
1. If the deploy uses long-lived `AKIA...` keys committed to a CI secret, leakage = direct API Gateway access.
2. If the deploy reuses STS tokens, the site silently breaks when they expire.
3. Without IAM scoping, the credentials grant blanket `execute-api:Invoke` on every API in the account, not just `api.sterilizari-gratuite.ro`.

**Where.**
- `frontend/.env` — current local STS tokens (already in `.gitignore`, good).
- `frontend/nuxt.config.ts:64-74` — `runtimeConfig` reads from env.
- `frontend/server/api/*` — all use `AwsClient`.

**Recommended solution.**

Pick one of these three strategies and document it in `docs/DEPLOY.md`:

**Strategy A — IAM Role (preferred if hosting on AWS).**
- Deploy the Nuxt SSR server to AWS (ECS Fargate, App Runner, or Lambda via `nitro.preset = 'aws-lambda'`).
- Attach an IAM role with a single statement: `execute-api:Invoke` on `arn:aws:execute-api:eu-central-1:<account>:<api-id>/*/*/*`.
- Don't set `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` env vars at all — `aws4fetch` will pick up the SDK chain via instance metadata. Update `register.post.ts` etc. to allow falling back to the SDK default credential chain.

**Strategy B — Static IAM user with scoped policy (Vercel/Netlify/etc.).**
- Create an IAM user `sterilizarigratuite-frontend-prod`.
- Attach a policy with **only** `execute-api:Invoke` on the specific API ARN (no `*`).
- Generate `AKIA...` access key, store in Vercel/Netlify env, never log.
- Rotate every 90 days (calendar reminder).
- Do NOT set `AWS_SESSION_TOKEN` (only used for STS).

**Strategy C — Cognito Identity Pool / OIDC (advanced).**
- Skip for MVP.

**Acceptance.**
- `docs/DEPLOY.md` exists and names the strategy.
- The IAM policy JSON is committed to the repo (e.g. `infra/iam-policy.json`) for reproducibility.
- Production deploy works for >24h without manual intervention (rules out STS).
- An attacker stealing the prod env vars cannot list/modify other AWS services.

---

### 5. JSON-LD `</script>` injection vector in inline structured data

**Problem.** Several pages emit JSON-LD via `useHead({ script: [{ type: 'application/ld+json', innerHTML: JSON.stringify(...) }] })`. `JSON.stringify` does NOT escape `</`. If any user-controlled string in the structured data (most importantly `organizationName` for campaigns) contains the literal substring `</script>`, an attacker can break out of the JSON-LD `<script>` block and inject arbitrary HTML/JS.

This is a classic XSS vector for inline JSON. It applies even if the data is "trusted" because campaign organizationName comes from organizers via the public form.

**Where.**
- `frontend/app/pages/campanii.vue:369` — `innerHTML: JSON.stringify(e)` for events.
- `frontend/app/pages/campanii.vue:374` — `innerHTML: JSON.stringify(breadcrumbLd.value)`.
- `frontend/app/pages/index.vue:67` — `innerHTML: JSON.stringify({ ... })` for homepage org schema.

**Recommended solution.**

Add a tiny helper in `frontend/app/utils/format.ts`:
```ts
/**
 * Serialize a value as JSON safe for embedding inside an inline <script> tag.
 * Escapes `<` to `<` so a `</script>` substring in the data cannot break
 * out of the surrounding <script> element.
 */
export function safeJsonLd(value: unknown): string {
  return JSON.stringify(value).replace(/</g, '\\u003c')
}
```

Then in all three sites above, replace `JSON.stringify(...)` with `safeJsonLd(...)`. The function is auto-imported via Nuxt's `utils/` convention.

Also worth adding: in `nuxt.config.ts` route headers (see #8), set `Content-Security-Policy` with `script-src 'self' 'unsafe-inline' https://hcaptcha.com https://*.hcaptcha.com` to enforce defense in depth.

**Acceptance.**
- Submit a campaign with `organizationName: "ACME </script><img src=x onerror=alert(1)>"` (only possible to test once you can produce a campaign with that name in the API).
- View `/campanii` source — the JSON-LD block contains `</script>` instead of literal `</script>`. No alert fires.

---

### 6. Invalid TypeScript version pin (`^6.0.2`)

**Problem.** `frontend/package.json:26` pins `typescript: "^6.0.2"`. There is no published TypeScript 6.x — the latest stable is 5.x. The current `package-lock.json` may have resolved this to a beta/pre-release or a typo-squat package. Anyone running a clean `npm install` against this manifest will either fail or pull an unexpected version.

**Where.**
- `frontend/package.json:26`.

**Recommended solution.**

1. Check what's actually installed: `cd frontend && cat node_modules/typescript/package.json | grep version`.
2. Pin to a real version. Recommended: `"typescript": "^5.6.0"` (compatible with current Nuxt 4).
3. Run `npm install` to regenerate the lockfile.
4. Run `npm run typecheck` to confirm no regressions.

**Acceptance.**
- `npm install` on a clean checkout completes without warnings about unknown versions.
- `npm run typecheck` passes.

---

### 7. Suspicious `lucide-vue-next: ^1.0.0` version

**Problem.** The canonical `lucide-vue-next` package on npm is on the 0.x line (latest 0.5xx series). A `^1.0.0` pin either resolves to an unrelated 1.0 release (unlikely for an icon library that's still pre-1) or to a typo-squat / fork. This is a supply-chain risk.

**Where.**
- `frontend/package.json:16`.

**Recommended solution.**

1. Check what got installed: `cat frontend/node_modules/lucide-vue-next/package.json` — verify `repository.url` points to `lucide-icons/lucide`.
2. If it's a forked package, immediately replace with the canonical version: `npm install lucide-vue-next@latest` and verify the resolved version is in the 0.4xx-0.5xx range.
3. Update `package.json` to pin the actual installed version, e.g., `"lucide-vue-next": "^0.460.0"`.
4. Run `npm run typecheck` and visually verify all icons still render (start dev server, eyeball pages).

**Acceptance.**
- The installed package's `repository.url` is `https://github.com/lucide-icons/lucide`.
- All icons render unchanged in dev.

---

## Security & abuse hardening

### 8. No security response headers

**Problem.** The site emits no `Content-Security-Policy`, `X-Content-Type-Options`, `Strict-Transport-Security`, `X-Frame-Options`, or `Referrer-Policy`. For a public form-collecting site, these are baseline expectations. Missing them means the site is rated "F" by Mozilla Observatory and is more vulnerable to clickjacking, MIME sniffing, and protocol downgrade attacks.

**Where.**
- `frontend/nuxt.config.ts:76-86` — `routeRules` has no `headers` entries.

**Recommended solution.**

Add to `frontend/nuxt.config.ts` `routeRules`:
```ts
routeRules: {
  '/**': {
    headers: {
      'X-Content-Type-Options': 'nosniff',
      'X-Frame-Options': 'DENY',
      'Referrer-Policy': 'strict-origin-when-cross-origin',
      'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
      'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
      // Loose CSP — tighten after observing what actually loads.
      'Content-Security-Policy': [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' https://*.hcaptcha.com https://hcaptcha.com",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com data:",
        "img-src 'self' data: https:",
        "connect-src 'self' https://*.hcaptcha.com https://hcaptcha.com https://api.sterilizari-gratuite.ro",
        "frame-src https://*.hcaptcha.com https://hcaptcha.com",
        "frame-ancestors 'none'",
        "base-uri 'self'",
      ].join('; '),
    },
  },
  // ...existing rules
}
```

Test in staging first — CSP often breaks edge cases. Add `Content-Security-Policy-Report-Only` first if you want a soft rollout.

**Acceptance.**
- Run https://observatory.mozilla.org/analyze/sterilizari-gratuite.ro after deploy — should score B+ or higher.
- Site loads correctly, captcha widget works, fonts render. No console CSP errors.

---

### 9. No rate limiting on Nuxt server proxy

**Problem.** `/api/register` and `/api/campaigns/submit` blindly forward to AWS API Gateway. If the upstream Lambda doesn't throttle by IP (unlikely to be perfect), an attacker can spam submissions, costing money for SMS/email and polluting the database. The error code `rate_limited` is even mapped in `utils/api-error.ts` — but no enforcement layer exists at the Nuxt edge.

**Where.**
- `frontend/server/api/register.post.ts` — no limiter.
- `frontend/server/api/campaigns/submit.post.ts` — no limiter.
- `frontend/app/utils/api-error.ts:15` — `rate_limited` mapped but never produced.

**Recommended solution.**

Add an IP-based rate limiter as Nitro middleware. For MVP, an in-memory token bucket is sufficient (single-instance deploy). For multi-instance, use Redis/Upstash.

Create `frontend/server/middleware/rate-limit.ts`:
```ts
const buckets = new Map<string, { count: number; resetAt: number }>()
const LIMITS: Record<string, { max: number; windowMs: number }> = {
  '/api/register': { max: 5, windowMs: 60_000 },
  '/api/campaigns/submit': { max: 3, windowMs: 60_000 },
}

export default defineEventHandler((event) => {
  const url = event.node.req.url ?? ''
  const limit = Object.entries(LIMITS).find(([prefix]) => url.startsWith(prefix))?.[1]
  if (!limit) return

  const ip = getRequestIP(event, { xForwardedFor: true }) ?? 'unknown'
  const key = `${url}:${ip}`
  const now = Date.now()
  const bucket = buckets.get(key)

  if (!bucket || bucket.resetAt < now) {
    buckets.set(key, { count: 1, resetAt: now + limit.windowMs })
    return
  }
  bucket.count++
  if (bucket.count > limit.max) {
    throw createError({
      statusCode: 429,
      statusMessage: 'Prea multe cereri.',
      data: { error: 'rate_limited' },
    })
  }
})
```

For multi-instance deploys, swap the `Map` for `@upstash/ratelimit` or similar.

**Acceptance.**
- Submit `/api/register` 6 times within 60 seconds from the same IP — 6th request returns 429 with `data: { error: 'rate_limited' }`.
- Frontend's `extractApiError` correctly displays "Ai trimis prea multe cereri…" toast.

---

### 10. `v-html` on user-derivable strings

**Problem.** Three places use `v-html` to interpolate strings that include data originating from sessionStorage or form fields. While today the values come from controlled comboboxes (static `judete.json` dataset), the pattern is fragile:
1. SessionStorage is user-mutable — a user can edit it via DevTools and self-XSS.
2. If the locality dataset ever included free-form input, instant XSS.
3. Code review can't easily tell which `v-html` is safe vs. dangerous — better to ban the pattern.

**Where.**
- `frontend/app/pages/confirmare.vue:15` — `<p v-html="rankMessage" />`.
- `frontend/app/pages/confirmare-campanie.vue:27` — `<p v-html="reachMessage" />`.
- `frontend/app/components/forms/CampaignForm.vue:81` — `<span v-html="waitingCountMessage" />`.

(The `v-html` on `frontend/app/pages/organizatori.vue:70` for FAQ is fine — values are hardcoded constants.)

**Recommended solution.**

Refactor each `v-html` into structured template fragments. Example for `rankMessage` in `confirmare.vue`:

Replace the `rankMessage` computed with a small object:
```ts
interface RankParts {
  prefix: string  // "Ești "
  rank: string    // "prima persoană" or "a doua persoană"
  middle: string  // " din "
  locality: string
  suffix: string  // " care s-a înscris."
  countyTail?: { prefix: string; county: string }
}

const rankParts = computed<RankParts>(() => {
  // ... same logic as today, but return parts instead of HTML string
})
```

Then in template:
```html
<p>
  {{ rankParts.prefix }}<strong>{{ rankParts.rank }}</strong>{{ rankParts.middle }}<strong>{{ rankParts.locality }}</strong>{{ rankParts.suffix }}
  <template v-if="rankParts.countyTail">
    {{ rankParts.countyTail.prefix }}<strong>{{ rankParts.countyTail.county }}</strong>.
  </template>
</p>
```

Apply the same pattern to `reachMessage` (`confirmare-campanie.vue`) and `waitingCountMessage` (`CampaignForm.vue`).

**Acceptance.**
- Grep `v-html` in `frontend/app/` returns only the FAQ in `organizatori.vue`.
- Manually edit sessionStorage in DevTools to set `locality: "<img src=x onerror=alert(1)>"` and refresh — the literal string renders, no alert fires.
- All three pages still display correctly with bold locality/county names.

---

### 11. Unsigned-fetch fallback in stats endpoints

**Problem.** Two stats endpoints have a "fallback" branch that calls `$fetch` without SigV4 signing when AWS credentials aren't set. If the upstream API requires SigV4 (which it does — it's behind API Gateway), the unsigned call fails — but the error is opaque, and the fallback path is dead code that gives a false sense of "this endpoint can run without AWS creds".

**Where.**
- `frontend/server/api/stats/locality.get.ts:50` — `data = await $fetch<RegistrationsResponse>(upstreamUrl)`.
- `frontend/server/api/stats/registrations.get.ts:32` — same pattern.

**Recommended solution.**

Make AWS credentials mandatory and remove the unsigned branch. In both files, after the `if (!awsAccessKeyId || !awsSecretAccessKey || !awsApiBase)` guard pattern that already exists in `register.post.ts:19`:

```ts
if (!awsAccessKeyId || !awsSecretAccessKey || !awsApiBase) {
  throw createError({
    statusCode: 500,
    statusMessage: 'Server is missing AWS credentials or API base URL',
  })
}
```

Then unconditionally use signed `aws.fetch()`. Delete the `else` branch.

**Acceptance.**
- Both stats endpoints return data when env is fully configured.
- With creds removed, both return a clean 500 with the expected message instead of a confusing 403/CORS error.

---

### 12. No upstream timeouts on AWS / hCaptcha calls

**Problem.** `aws.fetch()` and the hCaptcha verify `$fetch` have no timeout. A slow Lambda cold start or a hung captcha API will keep the Nuxt SSR worker tied up indefinitely. Under load, this exhausts the worker pool and the entire site becomes unresponsive.

**Where.**
- `frontend/server/api/register.post.ts:39` (hCaptcha) and `:65` (AWS).
- `frontend/server/api/campaigns/submit.post.ts:45` and `:71`.
- `frontend/server/api/campaigns/index.get.ts:46`.
- `frontend/server/api/stats/locality.get.ts:40`.
- `frontend/server/api/stats/registrations.get.ts:22`.

**Recommended solution.**

Add `signal: AbortSignal.timeout(ms)` to every upstream call. Add a small helper:

In each server route, before the `aws.fetch(...)` call:
```ts
const res = await aws.fetch(`${baseUrl}/register`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(registration),
  signal: AbortSignal.timeout(10_000),
})
```

For `$fetch` (hCaptcha verify):
```ts
const verify = await $fetch<HcaptchaVerifyResponse>('https://api.hcaptcha.com/siteverify', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({ secret, response: hcaptchaToken }).toString(),
  timeout: 5_000,
})
```

Wrap in try/catch and return a clean `503` on timeout:
```ts
try {
  const res = await aws.fetch(..., { signal: AbortSignal.timeout(10_000) })
  // ...
} catch (err) {
  if (err instanceof Error && err.name === 'TimeoutError') {
    throw createError({ statusCode: 503, statusMessage: 'Upstream timeout', data: { error: 'server_error' } })
  }
  throw err
}
```

**Acceptance.**
- Simulate a slow upstream (e.g., `nc -l 8080` and point `AWS_API_BASE=http://localhost:8080`) — request resolves with a 503 within ~10s instead of hanging.
- Normal flow still works.

---

### 13. Deprecated `process.dev` usage

**Problem.** Nuxt 4 has deprecated `process.dev` in favor of `import.meta.dev`. The single existing usage will produce a deprecation warning and may stop working in a future minor release.

**Where.**
- `frontend/server/api/stats/registrations.get.ts:38` — `if (process.dev) console.warn(...)`.

**Recommended solution.**

Replace with `import.meta.dev`:
```ts
if (import.meta.dev) console.warn('[registrations] Backend returned "Ilfov" key — normalizing to "IF"')
```

**Acceptance.**
- `npm run typecheck` passes.
- Grep for `process.dev` returns no matches.

---

## SEO

### 14. Decide whether to enable OG images

**Problem.** `nuxt.config.ts:94-96` has `ogImage.enabled: false`, but `nuxt-og-image` is still pulling in `@takumi-rs/core` (~50MB native binaries) and `playwright-core` (~80MB) as runtime dependencies. Either:
- OG images are off — and the deps are pure bloat that should be removed.
- OG images should be on — Facebook/WhatsApp/Twitter shares to a Romanian NGO platform are the #1 organic distribution channel, and currently shares look like blank cards.

**Where.**
- `frontend/nuxt.config.ts:94-96`.
- `frontend/package.json:14, 18` — `@takumi-rs/core`, `playwright-core` listed as dependencies.

**Recommended solution.**

**Strongly recommend Option A: enable OG images.** For the use case (sharing campaigns + getting citizens onto registration pages), OG images significantly increase click-through rates.

1. Set `ogImage.enabled: true` in `nuxt.config.ts`.
2. Add per-page `defineOgImage(...)` calls (the SEO module has helpers).
3. Create a default OG template at `frontend/app/components/OgImage/Default.vue` matching the brand book (navy bg, orange accent, logo, title).
4. For `/campanii?judet=alba`, generate dynamic OG with the county name + active campaign count.
5. Run `npm run build` and verify `/__og-image__/...` URLs resolve.

**Option B (drop OG images entirely):**
1. Remove `'@nuxtjs/seo'` from modules — or override the OG submodule. Per `@nuxtjs/seo` docs, you can disable just og-image with `seo: { ogImage: false }`.
2. Remove `@takumi-rs/core` and `playwright-core` from `package.json`.
3. Run `npm install` and verify the deps are gone.
4. Add static fallback OG image at `frontend/public/og-default.png` and reference via `useSeoMeta({ ogImage: '/og-default.png' })` in `default.vue` layout.

**Acceptance.**
- For Option A: paste a deployed page URL into Facebook Debugger or https://www.opengraph.xyz/ and confirm a branded image renders.
- For Option B: `npm install` produces `<200MB` `node_modules` (currently bloated by takumi+playwright).

---

### 15. Add canonical links on every indexable page

**Problem.** Only `/campanii` sets `<link rel="canonical">`. `/harta` is indexable and has many query-param permutations (`?view=cerere&judet=alba`, `?view=oferta&judet=alba`, etc.) that produce near-duplicate content. Without canonical, Google will index multiple versions and dilute ranking signal. The homepage and `/organizatori` also lack explicit canonical (they rely on Nuxt site config, which works but is brittle).

**Where.**
- `frontend/app/pages/harta.vue:223-234` — `useSeoMeta` set, no `useHead` canonical.
- `frontend/app/pages/index.vue` — no canonical.
- `frontend/app/pages/organizatori.vue` — no canonical.
- `frontend/app/pages/politica-de-confidentialitate.vue` — no canonical.

**Recommended solution.**

For each page, add an explicit canonical that strips query params (or canonicalizes a known set). Pattern from `campanii.vue:263-268`:

```ts
const siteConfig = useSiteConfig()
const siteUrl = (siteConfig.url as string | undefined) || 'https://sterilizari-gratuite.ro'

useHead(() => ({
  link: [{ rel: 'canonical', href: `${siteUrl}${route.path}` }],
}))
```

For `/harta` specifically, canonicalize `?judet=...` (real facet) but strip `?view=...` (UI state):
```ts
const canonicalHref = computed(() => {
  const u = new URL('/harta', siteUrl)
  if (route.query.judet) u.searchParams.set('judet', String(route.query.judet))
  return u.toString()
})
```

Apply to all top-level pages.

**Acceptance.**
- View source of every indexable page — `<link rel="canonical" href="..."/>` is present and correct.
- Run a crawler (Screaming Frog or `curl ... | grep canonical`) to confirm.

---

### 16. Tidy redundant robots disallow entries

**Problem.** `nuxt.config.ts:57` has `disallow: ['/m/', '/r/', '/confirmare', '/confirmare-campanie']`. Robots.txt path matching is prefix-based, so `/confirmare` already matches both `/confirmare` and `/confirmare-campanie`. The fourth entry is redundant. Also `/m/` and `/r/` — the trailing slash means they only match URLs with a trailing slash; `/m/abc123` matches but `/m` (without slash) doesn't. For magic links the actual URLs are `/m/[token]` so `/m/` works. Worth verifying.

**Where.**
- `frontend/nuxt.config.ts:56-58`.

**Recommended solution.**

```ts
robots: {
  disallow: ['/m/', '/r/', '/confirmare'],
},
```

Verify by running `curl http://localhost:3000/robots.txt` after the change.

**Acceptance.**
- `robots.txt` excludes `/confirmare`, `/confirmare-campanie`, `/m/[token]`, `/r/[token]`.
- Includes `/`, `/campanii`, `/organizatori`, `/harta`, `/politica-de-confidentialitate`.

---

### 17. Use ISO 3166-2 codes for `addressRegion` in Schema.org

**Problem.** The `Event` schema on `/campanii` uses the human-readable Romanian county name (e.g., "Alba") for `addressRegion`. Google's Schema.org parser officially expects ISO 3166-2 subdivision codes (`RO-AB`, `RO-CJ`, etc.) for `addressRegion`. Using human names works but loses some structured-data weight in Google's local pack.

**Where.**
- `frontend/app/pages/campanii.vue:323-326`.

**Recommended solution.**

The county code (`AB`, `CJ`, etc.) is already the `auto` field in `judete.json`. Just prefix with `RO-`:
```ts
addressRegion: `RO-${c.county.toUpperCase()}`,
```

Optionally add the human name as `addressRegionName` (non-standard but harmless).

**Acceptance.**
- Google Rich Results Test (https://search.google.com/test/rich-results) on a deployed campaign page returns no schema warnings.

---

### 18. Don't hardcode site URL in JSON-LD

**Problem.** `frontend/app/pages/index.vue:73,79` hardcodes `https://sterilizari-gratuite.ro` in the homepage JSON-LD. Staging deploys (e.g., `staging.sterilizari-gratuite.ro` or a Vercel preview URL) will emit JSON-LD pointing at production, which confuses Google during crawl tests.

**Where.**
- `frontend/app/pages/index.vue:73, 79` — `url: 'https://sterilizari-gratuite.ro'`.

**Recommended solution.**

Use `useSiteConfig()` (already used in `campanii.vue`):
```ts
const siteConfig = useSiteConfig()
const siteUrl = (siteConfig.url as string | undefined) || 'https://sterilizari-gratuite.ro'

useHead(() => ({
  script: [{
    type: 'application/ld+json',
    innerHTML: safeJsonLd({  // ← uses the helper from #5
      '@context': 'https://schema.org',
      '@graph': [
        { '@type': 'Organization', name: 'Build4Paws', url: 'https://build4paws.ro', /* ... */ },
        { '@type': 'WebSite', name: 'Sterilizări Gratuite', url: siteUrl, /* ... */ },
      ],
    }),
  }],
}))
```

**Acceptance.**
- Set `NUXT_PUBLIC_SITE_URL=https://staging.example.com`, run dev, view source — JSON-LD `WebSite.url` is `https://staging.example.com`.

---

### 19. Self-host Google Fonts via `@nuxt/fonts` for LCP

**Problem.** `nuxt.config.ts:30-33` loads "Funnel Display" (weights 300-800) and "Rethink Sans" (italic + weights 400-800) from Google Fonts via a single CSS link. Google's CSS triggers ~6-8 font file requests on first paint. For a Romanian NGO site where many users are on mobile, this can add 500-800ms to LCP.

`@nuxt/fonts` is already in your transitive dependency tree (pulled by `@nuxtjs/seo`'s SEO Utils submodule). Use it.

**Where.**
- `frontend/nuxt.config.ts:21-34` — Google Fonts `<link>` in `app.head`.

**Recommended solution.**

1. Add `@nuxt/fonts` to `modules` in `nuxt.config.ts`:
```ts
modules: [
  '@nuxtjs/seo',
  '@vueuse/nuxt',
  '@nuxt/fonts',
],
```

2. Configure:
```ts
fonts: {
  families: [
    { name: 'Funnel Display', weights: [300, 400, 500, 600, 700, 800] },
    { name: 'Rethink Sans', weights: [400, 500, 600, 700, 800], styles: ['normal', 'italic'] },
  ],
  defaults: {
    weights: [400, 600],
    styles: ['normal'],
    subsets: ['latin', 'latin-ext'],  // latin-ext for Romanian diacritics
  },
},
```

3. Remove the manual `<link>` entries from `app.head.link` (keep only `favicon`).

4. The CSS in `main.css` (`--font-heading: 'Funnel Display', ...`) keeps working — `@nuxt/fonts` auto-injects `@font-face` declarations.

**Acceptance.**
- Run `npm run dev`, open DevTools Network tab, reload the homepage.
- No requests to `fonts.googleapis.com` or `fonts.gstatic.com`.
- Font requests come from `/_fonts/...` (self-hosted).
- Romanian diacritics (ă, â, î, ș, ț) render correctly.
- Run Lighthouse — LCP should improve by 200-500ms.

---

### 20. Add `error.vue` for branded 404/500

**Problem.** Nuxt's default error page is generic, English-only, and looks broken for a Romanian-only audience. Most users hitting a 404 (e.g., from old shared links, typos, or the broken link in #1 if not fixed) will think the site is down.

**Where.**
- `frontend/app/error.vue` — does not exist.

**Recommended solution.**

Create `frontend/app/error.vue`:
```vue
<template>
  <div class="error-page">
    <div class="container error-page__inner">
      <h1 class="error-page__code">{{ error?.statusCode || 'Eroare' }}</h1>
      <h2 class="error-page__title">{{ title }}</h2>
      <p class="error-page__message">{{ message }}</p>
      <div class="error-page__actions">
        <NuxtLink to="/" class="error-page__btn">Înapoi acasă</NuxtLink>
        <NuxtLink to="/campanii" class="error-page__btn error-page__btn--ghost">Vezi campaniile</NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { NuxtError } from '#app'

const props = defineProps<{ error: NuxtError }>()

const title = computed(() => {
  if (props.error?.statusCode === 404) return 'Pagina nu a fost găsită'
  if (props.error?.statusCode === 500) return 'A apărut o eroare pe server'
  return 'Ceva nu a mers bine'
})

const message = computed(() => {
  if (props.error?.statusCode === 404) {
    return 'Linkul este greșit sau pagina a fost mutată. Încearcă să cauți campania din pagina principală.'
  }
  return 'Te rugăm să încerci din nou peste câteva momente. Dacă problema persistă, contactează-ne la contact@build4paws.ro.'
})

useSeoMeta({
  robots: 'noindex, nofollow',
  title: () => `${props.error?.statusCode || 'Eroare'} — Sterilizări Gratuite`,
})
</script>

<style scoped>
/* Use design tokens from main.css */
.error-page {
  min-height: 100vh;
  background: var(--color-primary);
  color: var(--color-text-light);
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: var(--space-2xl) var(--space-md);
}
.error-page__code {
  font-size: 6rem;
  color: var(--color-accent);
  margin-bottom: var(--space-md);
}
/* ... fill in remaining styles matching brand */
</style>
```

**Acceptance.**
- Visit `/this-does-not-exist` — branded Romanian 404 page.
- "Înapoi acasă" and "Vezi campaniile" links work.
- The page is `noindex, nofollow`.

---

## Vue/Nuxt patterns

### 21. Remove dead-code `useFormValidation` composable

**Problem.** `useFormValidation` and its rule helpers exist but are not used anywhere. The `phoneOrEmail` helper is even a stub that always returns `false`. Either it's broken-by-design or abandoned. Either way, dead code is a maintenance burden.

**Where.**
- `frontend/app/composables/useFormValidation.ts` — entire file unused (verified by grep).

**Recommended solution.**

Delete `frontend/app/composables/useFormValidation.ts`. The `CitizenForm.vue` and `CampaignForm.vue` already validate inline because they have cross-field rules — that's the right pattern; don't migrate to the composable.

**Acceptance.**
- `npm run typecheck` passes.
- Grep for `useFormValidation` returns no matches.

---

### 22. Move module-level state into `useState`

**Problem.** Several composables hold module-level state:
- `useToast.ts` — `let nextId = 0` and `const toasts = ref([])` at module scope.
- `useCitizenSession.ts` — `const session = ref(null)` and `let hydrated = false`.
- `useOrganizerSubmission.ts` — same pattern.
- `useLocationData.ts` — multiple `let` caches.

In Nuxt SSR, module-level state is **shared across all concurrent requests on the same Node process**. This means user A's toast/session can leak into user B's render. For static-data caches (`useLocationData`) this is fine. For user state (toasts, sessions), it's a real bug — though rarely observed because hydration usually overwrites it before render.

**Where.**
- `frontend/app/composables/useToast.ts:9-10`.
- `frontend/app/composables/useCitizenSession.ts:18-20`.
- `frontend/app/composables/useOrganizerSubmission.ts:12-14`.

**Recommended solution.**

Wrap user state in `useState` (request-scoped on SSR, singleton on client):

For `useToast.ts`:
```ts
export function useToast() {
  const toasts = useState<Toast[]>('toasts', () => [])
  const nextId = useState<number>('toasts:nextId', () => 0)

  function push(variant: ToastVariant, message: string, durationMs = 4500): number {
    nextId.value++
    const id = nextId.value
    toasts.value.push({ id, variant, message })
    if (durationMs > 0 && import.meta.client) {
      setTimeout(() => dismiss(id), durationMs)
    }
    return id
  }
  // ...rest unchanged
}
```

For `useCitizenSession.ts`:
```ts
export function useCitizenSession() {
  const session = useState<CitizenSession | null>('citizen-session', () => null)

  // Hydrate once on client
  if (import.meta.client && !session.value) {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    if (raw) {
      try { session.value = JSON.parse(raw) }
      catch { sessionStorage.removeItem(STORAGE_KEY) }
    }
  }

  function setSession(data: CitizenSession) {
    session.value = data
    if (import.meta.client) sessionStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  }

  function clearSession() {
    session.value = null
    if (import.meta.client) sessionStorage.removeItem(STORAGE_KEY)
  }

  return { session, setSession, clearSession }
}
```

Apply the same pattern to `useOrganizerSubmission.ts`. **Don't change** `useLocationData.ts` — its caches are static derived from a JSON file; module-level is correct there.

**Acceptance.**
- `npm run typecheck` passes.
- Manual smoke test: open two browser windows, register on one, reload the other — neither shows the other's session.
- Toasts trigger on the right window only.

---

### 23. Standardize on `withDefaults(defineProps())`

**Problem.** Some components use `withDefaults` for default values (`UiButton`, `CampaignCard`, `MapRomania`), others use bare `defineProps` (`UiInput`, `UiCombobox`, `UiCheckbox`, `UiSelect`, `UiTextarea`, `UiPhoneInput`). Inconsistency makes "is this prop required?" harder to answer at a glance.

**Where.**
- `frontend/app/components/ui/UiInput.vue:28-39` — bare `defineProps`.
- `frontend/app/components/ui/UiCombobox.vue:95-104` — bare.
- Several others.

**Recommended solution.**

For each UI component with optional props, wrap in `withDefaults` and provide explicit defaults:
```ts
withDefaults(defineProps<{
  modelValue: string
  label: string
  id: string
  type?: 'text' | 'email' | 'tel' | 'url' | 'number' | 'date' | 'time' | 'datetime-local'
  placeholder?: string
  required?: boolean
  error?: string
  min?: string | number
  max?: string | number
}>(), {
  type: 'text',
  required: false,
})
```

**Acceptance.**
- All UI components in `app/components/ui/` use `withDefaults` when they have optional props.
- `npm run typecheck` passes.

---

### 24. Fix heading hierarchy (skipping H2)

**Problem.** Several pages have `<h1>` (hero) → `<h3>` (form section title) with no `<h2>` in between. Screen readers expose this as a broken heading tree, hurting accessibility (axe-core flags it) and SEO (Google's heading-structure heuristic).

**Where.**
- `frontend/app/components/forms/CitizenForm.vue` — `.form-section__title` is `<h3>` (e.g., line 6 — `<h3 class="form-section__title">Salut!...`).
- `frontend/app/components/forms/CampaignForm.vue` — same pattern.

**Recommended solution.**

Change `<h3 class="form-section__title">` to `<h2 class="form-section__title">` in both forms. The CSS in those files keys off `.form-section__title`, not the tag name, so styling is unchanged.

For the form-step-2 preview in `CampaignForm.vue`, the `<CampaignCard>` already uses `<h3>` for locality (which is correct under an `<h2>` page heading). Verify the resulting tree:
- `/organizatori`: `<h1>Anunță o campanie...</h1>` → `<h2>Despre organizația ta</h2>` (form sections) → no h3s in step 1.
- `/`: `<h1>Sterilizare gratuită...</h1>` → `<h2>Salut!...</h2>` (form sections).

**Acceptance.**
- Run axe-core on `/`, `/organizatori`, `/campanii` — no heading-order violations.
- View source — heading levels are sequential.

---

### 25. Add explicit keys to `useFetch` calls

**Problem.** `useFetch` and `useAsyncData` use the URL as the cache key by default. With reactive query params, this works, but explicit keys make caching deterministic and easier to invalidate.

**Where.**
- `frontend/app/composables/useCampaigns.ts:31-37` — no key.
- `frontend/app/composables/useLocalityWaitingCount.ts:31` — uses raw `$fetch` (no caching at all).

**Recommended solution.**

For `useCampaigns.ts`, add a key based on the county:
```ts
const { data, error, status, refresh } = useFetch<CampaignsApiResponse | Campaign[]>(
  '/api/campaigns',
  {
    key: computed(() => `campaigns:${toValue(filters.countyCode) || 'all'}`),
    query: queryParams,
    default: () => ({ campaigns: [] }),
  },
)
```

For `useLocalityWaitingCount.ts`, consider migrating to `useFetch`/`useAsyncData` so the SSR payload hydrates cleanly without a client-side refetch:
```ts
const { data: stats, status } = useAsyncData<LocalityWaitingStats | null>(
  () => `locality-waiting:${toValue(county)}:${toValue(locality)}`,
  () => {
    const c = toValue(county)
    const l = toValue(locality)
    if (!c || !l) return Promise.resolve(null)
    return $fetch<LocalityWaitingStats>('/api/stats/locality', { query: { county: c, locality: l } })
  },
  { watch: [() => toValue(county), () => toValue(locality)] },
)
```

**Acceptance.**
- DevTools Network tab shows no duplicate `/api/stats/locality` request when navigating to `/confirmare` after a citizen registration (SSR-hydrated).
- `npm run typecheck` passes.

---

### 26. Add `rel="noopener"` to `target="_blank"` NuxtLinks

**Problem.** `NuxtLink target="_blank"` does not auto-add `rel="noopener noreferrer"` (unlike modern browsers' default for plain `<a>`). Two internal links in forms link to the privacy policy with `target="_blank"` but no `rel`. While the target is an internal route (low risk), the pattern is inconsistent with all the external links elsewhere.

**Where.**
- `frontend/app/components/forms/CitizenForm.vue:138` — `<NuxtLink to="/politica-de-confidentialitate" target="_blank">`.
- `frontend/app/components/forms/CampaignForm.vue:256` — same.

**Recommended solution.**

Add `rel="noopener"` to both:
```vue
<NuxtLink to="/politica-de-confidentialitate" target="_blank" rel="noopener">
  politica de confidențialitate
</NuxtLink>
```

**Acceptance.**
- Both links have `rel="noopener"` in the rendered HTML.

---

## Production readiness

### 27. Pin `nitro.preset` for the deploy target

**Problem.** Without an explicit `nitro.preset`, Nuxt picks a default that may not match your deploy target. This causes "works in dev, breaks in prod" surprises (e.g., the AWS SigV4 client behaving differently on Edge runtime vs. Node).

**Where.**
- `frontend/nuxt.config.ts` — no `nitro` block.

**Recommended solution.**

Decide the deploy target. For an MVP with AWS-backed APIs, the recommended options are:
- **Vercel** — `nitro: { preset: 'vercel' }` (Node serverless functions).
- **Node server** — `nitro: { preset: 'node-server' }` (Docker/PM2/EC2).
- **AWS Lambda** — `nitro: { preset: 'aws-lambda' }` (if hosting on AWS for credential simplicity — see #4).

Add to `nuxt.config.ts`:
```ts
nitro: {
  preset: process.env.NITRO_PRESET || 'node-server',  // adjust default
},
```

This lets local builds use Node and CI/Vercel override via env var.

**Acceptance.**
- `npm run build` produces output for the chosen preset (check `.output/`).
- Document the preset choice in `docs/DEPLOY.md`.

---

### 28. Add structured server logging

**Problem.** Every upstream failure surfaces to the client as a Romanian-language toast, but is **never logged** server-side. CloudWatch / Vercel logs / wherever-you-deploy will show only the request line and 500. Debugging "why did 8 organizers see captcha_failed yesterday" is impossible.

**Where.**
- All `frontend/server/api/*` files — no `console.error` or structured log calls.

**Recommended solution.**

Add minimal logging in each catch path. For consistency, create `frontend/server/utils/log.ts`:
```ts
type LogLevel = 'info' | 'warn' | 'error'

export function log(level: LogLevel, scope: string, message: string, data?: Record<string, unknown>) {
  const entry = {
    time: new Date().toISOString(),
    level,
    scope,
    message,
    ...data,
  }
  if (level === 'error') console.error(JSON.stringify(entry))
  else if (level === 'warn') console.warn(JSON.stringify(entry))
  else console.log(JSON.stringify(entry))
}
```

Then in `register.post.ts`:
```ts
import { log } from '../utils/log'
// ...
if (!res.ok) {
  log('error', 'register', 'upstream error', { status: res.status, body: text.slice(0, 500) })
  throw createError({ /* ... */ })
}
```

Apply to all 5 server routes. Keep entries one-line JSON for easy parsing.

**Don't log** PII (full body, phone numbers, emails). Truncate text bodies to ~500 chars.

**Acceptance.**
- Trigger an upstream error in dev — server console shows a JSON log line with status + truncated body.
- Logs don't contain phone numbers or emails.

---

### 29. Drop unused heavy dependencies

**Problem.** `@takumi-rs/core` (native binaries for OG image generation, ~50MB) and `playwright-core` (Chromium driver, ~80MB) are in `dependencies` (not `devDependencies`). They're transitively required by `nuxt-og-image` — but `ogImage.enabled: false`. This bloats production Docker images and slows cold starts on serverless.

**Where.**
- `frontend/package.json:14, 18` — top-level `dependencies`.

**Recommended solution.**

This is conditional on the decision in #14:

**If enabling OG images (recommended):** keep these deps, just verify they're in `dependencies` (correct) not `devDependencies`.

**If keeping OG images off:**
1. Remove `@takumi-rs/core` and `playwright-core` from `package.json` `dependencies`.
2. In `nuxt.config.ts`, override the SEO module to disable og-image entirely:
```ts
seo: {
  // disables nuxt-og-image as a peer
  ogImage: false,
},
```
3. Run `npm install` to regenerate the lockfile.
4. Verify `node_modules` size dropped by ~130MB.

**Acceptance.**
- After change: `du -sh frontend/node_modules` is significantly smaller (or the deps are gone from `package.json`).
- `npm run build` succeeds.
- Site still loads.

---

### 30. Decide on `useClinics` stub: ship data or remove section

**Problem.** `useClinics` returns `[]` always. The "Cabinete permanente în zona ta" section in `confirmare.vue:21-37` is gated on a non-empty result, so it never renders. This is dead UI code shipping in every build.

**Where.**
- `frontend/app/composables/useClinics.ts` — stub.
- `frontend/app/pages/confirmare.vue:21-37` — gated section.

**Recommended solution.**

Three options:

**A — Ship a static seed list.** If you have even a handful of permanent clinics for major cities, hardcode them as a JSON file at `frontend/app/assets/data/clinics.json` and have `useClinics` filter by `(countyCode, locality)`. Even 10 clinics across Bucharest/Cluj/Timișoara give the section meaning.

**B — Remove until v2.** Delete `useClinics.ts` and the entire section in `confirmare.vue:21-37`. Cleaner.

**C — Keep stub but render an empty state.** Show "Caut cabinete în zona ta..." with a link to a generic clinic finder. Slowest path; not recommended.

For MVP, **prefer Option B**. Re-introduce when you have data.

**Acceptance.**
- For B: grep `useClinics` returns no matches; `confirmare.vue` no longer references the composable.
- The confirmation page still renders correctly.

---

### 31. Add minimal CI (typecheck + smoke test)

**Problem.** No CI workflow. Type errors and broken builds slip into `main`. For a public-facing site, this is risky.

**Where.**
- `.github/workflows/` — does not exist.

**Recommended solution.**

Create `.github/workflows/ci.yml`:
```yaml
name: CI
on:
  pull_request:
  push:
    branches: [main]

jobs:
  typecheck:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '24'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      - run: npm ci
      - run: npm run typecheck
      - run: npm run build
        env:
          NUXT_PUBLIC_HCAPTCHA_SITE_KEY: ''
          AWS_API_BASE: 'https://api.example.com'
```

Optionally add a Playwright smoke test (`playwright-core` is already installed) for the citizen happy path: load `/`, fill name/phone/county/locality/species/gdpr, submit (with a mocked `/api/register` response), expect navigation to `/confirmare`.

**Acceptance.**
- A PR that introduces a TypeScript error fails CI.
- A PR that doesn't compile fails CI.

---

### 32. Wrap forms in `<NuxtErrorBoundary>`

**Problem.** If the captcha widget or any other client dependency throws during form render (CDN block, ad-blocker, etc.), the user sees a blank or broken form with no recovery path. Toasts only fire on submit; render-time errors are silent.

**Where.**
- `frontend/app/pages/index.vue:24-29` — `<FormsCitizenForm />` not boundary-wrapped.
- `frontend/app/pages/organizatori.vue:35-42` — `<FormsCampaignForm />` not wrapped.

**Recommended solution.**

Wrap each form in `<NuxtErrorBoundary>`:
```vue
<div class="form-card">
  <NuxtErrorBoundary>
    <FormsCitizenForm />
    <template #error="{ error, clearError }">
      <UiAlert variant="error">
        Formularul nu se poate încărca. Încearcă să reîncarci pagina.
      </UiAlert>
      <UiButton variant="ghost" @click="clearError">Reîncearcă</UiButton>
    </template>
  </NuxtErrorBoundary>
</div>
```

Apply the same pattern to `/organizatori`.

**Acceptance.**
- Manually throw in a form's `<script setup>` — fallback UI appears with a "Reîncearcă" button.
- Normal flow unaffected.

---

## What's already good (no action needed)

- **Server proxy pattern** — `aws4fetch` SigV4, correct `execute-api` service, error forwarding via `createError({ data })` — copy-paste ready for new endpoints.
- **Form a11y** — every input has `aria-invalid`, `aria-describedby`, `role="alert"` on errors. Combobox has full ARIA listbox semantics.
- **Submit-only validation with reactive re-validation** — solid UX pattern, correct implementation.
- **`<CampaignCard>` single source of truth** — used by organizer preview AND `/campanii` listing, ensures visual consistency.
- **Romanian copy** — consistent friendly second-person tone across all pages, no leftover English strings.
- **Privacy policy** — thorough, GDPR-aligned, with legal basis per data category. Links to ANSPDCP.
- **Robots config marks token pages noindex** — `/m/`, `/r/`, `/confirmare*` correctly excluded.
- **Design tokens centralized** in `main.css` — every component consumes CSS custom properties, enabling future theming.
- **Brand-consistent UI** — navy + orange + slate scale, Funnel Display + Rethink Sans, matches the documented brand book.

---

## Suggested fix order

### Day 1 — must-do before launch
1, 2, 3, 5, 6, 7 (correctness/security blockers)

### Day 2 — must-decide before launch
4 (AWS strategy), 14 (OG images), 30 (clinics)

### Day 3 — security hardening
8, 9, 10, 11, 12, 13

### Day 4 — SEO polish
15, 16, 17, 18, 19, 20

### Post-launch
21, 22, 23, 24, 25, 26, 27, 28, 29, 31, 32

---

## How to use this document with Sonnet

Each task above is self-contained. To execute one:

1. Copy the entire section (e.g., **#5. JSON-LD `</script>` injection vector**) including Problem, Where, Recommended solution, and Acceptance.
2. Paste into a Sonnet conversation prefixed with: *"Execute this task. Make the changes, then verify against the Acceptance criteria. Don't expand scope."*
3. Review the diff before merging.

For multi-task batches, group by section (e.g., "do all Security tasks 8-13"). The agent should treat the Acceptance criteria as the contract.

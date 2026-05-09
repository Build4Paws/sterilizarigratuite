# Campaigns Flow — Plan

Organizer-side flow: ONGs / primării submit a sterilization campaign for review,
then we display approved campaigns publicly.

This document covers the **submission flow** (organizer landing → form →
preview → confirmation). The public listing (`/campanii`) reuses the
`CampaignCard` produced here and is tracked separately.

---

## 1. Current state

**Already in place**
- `pages/organizatori.vue` + `pages/confirmare-campanie.vue` — placeholders.
- `types/organizer.ts` defines `CampaignSubmission` (org name, county, locality,
  address, date/time, species, slots, doctor, phonePublic, emailContact).
- UI primitives: `UiInput`, `UiSelect`, `UiCheckbox`, `UiCombobox`,
  `UiPhoneInput`, `UiFormRow`, `UiFormItem`, `UiFormDivider`, `UiButton`,
  `UiAlert`, `UiToaster`.
- Composables: `useLocationData`, `useCitizenSession` (pattern reference).
- Server proxy pattern: `server/api/register.post.ts` (AWS SigV4 via
  `aws4fetch`, hCaptcha verify, JSON parse, error forwarding).

**Backend status**
- `POST /campaigns` and locality-stats endpoints **do not exist yet**.
  We define the contracts in §5 below; backend will implement to match.

---

## 2. Reuse vs. add

**Reuse as-is**
`UiInput`, `UiSelect`, `UiCheckbox`, `UiPhoneInput`, `UiCombobox`,
`UiFormRow/Item/Divider`, `UiButton`, `UiAlert`, `UiToaster`,
`useLocationData`, hCaptcha integration, the `register.post.ts` server-route
shape, and the `useCitizenSession` storage pattern.

**New (kept minimal)**
- `UiTextarea` — multiline address (or extend `UiInput` with a `multiline`
  prop — pick one).
- Date/time inputs — extend `UiInput` to accept `type="date" | "time"` rather
  than building separate components (native pickers are fine for MVP).
- `CampaignCard.vue` — single source of truth for how a campaign renders.
  Used by the preview step *and* later by `/campanii`.
- `CampaignForm.vue` — multi-step (fill → preview → submit).
- `useOrganizerSubmission.ts` — session-storage composable mirroring
  `useCitizenSession`; drives the confirmation page.
- `useLocalityWaitingCount.ts` — fetches "N persoane așteaptă" when a locality
  is picked.
- Server routes: `server/api/campaigns/submit.post.ts` and
  `server/api/stats/locality.get.ts`.

---

## 3. Page-level plan

### 3.1 `/organizatori`

1. **Hero** — short value prop: *"Anunță-ți campania, ajunge la cetățenii care
   așteaptă în zona ta."*
2. **"Cum funcționează"** — 3-step row (Trimiți → Aprobăm în 24h → Anunțăm
   cetățenii). Pure markup, no new component.
3. **Form card** — embedded `CampaignForm` inside the same `.form-card` style
   as the homepage so the visual language matches.
4. **Mini-FAQ** — accordion with 3-4 entries (cost, aprobare, anulare,
   modificări). Plain `<details>` is enough — no new component.

### 3.2 `CampaignForm` UX

Two-step inline wizard (no route change), mirroring `CitizenForm`'s
submit-only validation.

**Step 1 — Fill** (sectioned like CitizenForm):
- *Despre organizație*: organization name, contact email, contact phone.
- *Unde și când*: county + locality combobox → on locality change, fetch
  waiting count and show inline ("**12 persoane** din **Bosanci** așteaptă o
  campanie").
- *Adresă*: simple textarea (street + venue).
- *Date/ore*: date start, multi-day toggle, date end (conditional), time
  start, time end.
- *Specii și capacitate*: species checkboxes; slot count per species
  (conditional).
- *Medic veterinar*: optional.
- *GDPR + hCaptcha*.
- Submit button → "Continuă spre previzualizare".

**Step 2 — Preview**:
- Renders a real `<CampaignCard>` with the entered data — RO-formatted
  dates, species icons, full visual fidelity to how it will appear on
  `/campanii`.
- Two buttons: "Înapoi la editare" / "Trimite spre aprobare".
- On submit: POST to `/api/campaigns/submit`, on success store summary in
  `useOrganizerSubmission`, redirect to `/confirmare-campanie`.

### 3.3 `/confirmare-campanie` (upgrade)

- Mirror layout of `/confirmare`: header check + title + body block.
- *"Mulțumim, **{org}**! Campania ta din **{locality}, {date}** este în curs
  de aprobare."*
- *"Revenim în maxim 24h pe **{contactEmail}**."*
- Display the campaign summary as a `<CampaignCard variant="pending">`
  (greyscale) so the organizer sees exactly what's been submitted.
- Footer: *"Ai trimis greșit? Scrie-ne la …"* (no edit flow yet — v2).

### 3.4 Error / edge states

- **Network / 5xx**: red `UiAlert` at top of form + toast.
- **Validation 400 from backend**: surface field-level errors using same
  `errors` map pattern as `CitizenForm`.
- **Duplicate (409)**: friendly message ("O campanie identică există deja
  pentru această locație și dată"), keep form filled.
- **Captcha fail**: reset captcha + inline message.
- **Locality with 0 waiting people**: show neutral note ("Fii printre primii
  care anunță o campanie aici"), don't block submit.

### 3.5 SEO

- `useSeoMeta` updated with proper title/description/og.
- JSON-LD: `Organization` + breadcrumb back to home.
- `/confirmare-campanie` stays `noindex`.

---

## 4. Frontend types

To be added to `types/organizer.ts` (extends the current `CampaignSubmission`):

```ts
export interface CampaignSubmission {
  organizationName: string
  contactEmail: string        // private — we contact org here
  contactPhone: string        // private — internal contact
  phonePublic: string         // shown on the public campaign card
  county: string              // code, e.g. "SV"
  locality: string            // name
  address: string             // free text / multiline
  dateStart: string           // YYYY-MM-DD
  dateEnd?: string            // YYYY-MM-DD, only if multi-day
  timeStart: string           // HH:mm
  timeEnd: string             // HH:mm
  species: ('dog' | 'cat')[]
  slotsDogs?: number          // required iff 'dog' in species
  slotsCats?: number          // required iff 'cat' in species
  doctor?: string             // optional
  gdprConsent: boolean
}

export interface CampaignSubmissionResponse {
  message: string
  submissionId: string
  status: 'pending'
  stats?: {
    registeredInLocality: number
    registeredInCounty: number
  }
}

export interface LocalityWaitingStats {
  county: string
  locality: string
  registeredInLocality: number
  registeredInCounty: number
}
```

---

## 5. Proposed backend contracts

To hand to the backend team. All shapes designed to match the conventions
already established by `POST /register`.

### 5.1 `POST /campaigns/submit`

**Request body**

```json
{
  "organizationName": "ONG Patrupede",
  "contactEmail": "contact@patrupede.ro",
  "contactPhone": "+40712345678",
  "phonePublic": "+40712345678",
  "county": "SV",
  "locality": "Bosanci",
  "address": "Strada Principală nr. 12, lângă școala generală",
  "dateStart": "2026-05-15",
  "dateEnd": null,
  "timeStart": "09:00",
  "timeEnd": "17:00",
  "species": ["dog", "cat"],
  "slotsDogs": 20,
  "slotsCats": 30,
  "doctor": "Dr. Ionescu Maria",
  "gdprConsent": true,
  "hcaptchaToken": "..."
}
```

**Success — 200**

```json
{
  "message": "Campaign submitted for review",
  "submissionId": "b9f12e75-cdd3-4199-9426-27b74b4010ad",
  "status": "pending",
  "stats": {
    "registeredInLocality": 12,
    "registeredInCounty": 35
  }
}
```

The `stats` block lets the confirmation page tell the organizer how many
citizens are waiting for their campaign — same shape as the `/register`
response so we share rendering logic.

**Validation error — 400**

```json
{
  "error": "validation_failed",
  "errors": [
    { "field": "dateStart", "message": "Data trebuie să fie în viitor." },
    { "field": "slotsDogs", "message": "Câmpul este obligatoriu." }
  ]
}
```

**Duplicate / conflict — 409**

```json
{
  "error": "duplicate_submission",
  "message": "O campanie identică există deja pentru această locație și dată.",
  "existingSubmissionId": "uuid"
}
```

**Captcha failure — 400** (matches `/register` behaviour)

```json
{
  "error": "captcha_failed",
  "message": "Verificarea captcha a eșuat."
}
```

### 5.2 `GET /stats/locality?county=SV&locality=Bosanci`

Public, cacheable. Used by the form to show "N persoane așteaptă" on the fly
when an organizer picks a locality.

**Response — 200**

```json
{
  "county": "SV",
  "locality": "Bosanci",
  "registeredInLocality": 12,
  "registeredInCounty": 35
}
```

If locality is empty / unknown:

```json
{
  "county": "SV",
  "locality": "Bosanci",
  "registeredInLocality": 0,
  "registeredInCounty": 0
}
```

---

## 6. Story breakdown for the GitHub board

Sized small enough to be one PR each. Suggested order top-to-bottom; #1–#4
are unblockers and can run in parallel.

| # | Title | Notes |
|---|-------|-------|
| 1 | Extend `UiInput` to support `date` and `time` types | Preserve label/error/required API; verify mobile native pickers. |
| 2 | Add `UiTextarea` component | Same prop surface as `UiInput` (label, error, required, placeholder, v-model). |
| 3 | Build `CampaignCard` component | Props: `campaign` (CampaignSubmission + optional approved date/status), `variant: 'default' \| 'pending'`. RO-formatted dates, species icons. Reused on `/campanii` later. |
| 4 | Add `useOrganizerSubmission` composable | Mirrors `useCitizenSession`; stores submitted campaign + `submissionId` in `sessionStorage`. |
| 5 | Add `useLocalityWaitingCount` composable + `/api/stats/locality.get.ts` server route | Server route signs the AWS request; composable returns `{ count, loading, error }` reactive to county+locality. **Blocked on backend endpoint.** |
| 6 | Add `/api/campaigns/submit.post.ts` server route | Copy `register.post.ts` shape (SigV4, hCaptcha verify, JSON parse, error forwarding). **Blocked on backend endpoint.** |
| 7 | Build `CampaignForm.vue` — Step 1 (fill + validation) | All fields, submit-only validation, conditional fields (multi-day, species slots), inline waiting-count display. Clicking next just toggles step. |
| 8 | Build `CampaignForm.vue` — Step 2 (preview + submit) | Renders `<CampaignCard>`, "back" returns to fill, "submit" hits the server route, handles loading/error, persists session, navigates to `/confirmare-campanie`. |
| 9 | Redesign `/organizatori` page | Hero, "Cum funcționează" 3-step row, form card embed, FAQ `<details>`, SEO meta + JSON-LD. |
| 10 | Redesign `/confirmare-campanie` page | Hydrated from `useOrganizerSubmission`; redirects to `/organizatori` if no session; renders summary card + "next steps" copy. |
| 11 | Error & duplicate handling polish | Wire 4xx/5xx → field errors + alert; map known backend error codes (`duplicate_submission`, `validation_failed`) to Romanian copy; captcha reset on failure. |
| 12 | Refine `CampaignSubmission` type & shared validators | Extract phone RO + email validators into `utils/validators.ts` so `CitizenForm` uses them too. |
| 13 | QA pass & responsive checks | Manual run of all flows, mobile widths, keyboard nav, screen-reader labels on date/time inputs, Lighthouse on `/organizatori`. |
| 14 | Update `docs/FRONTEND-PLAN.md` | Replace § 2.3 / 2.5 placeholders with the actual built flow + open questions for v2 (edit/cancel, organizer dashboard). |

**Backend dependency:** stories #5 and #6 are blocked until the backend
team implements the contracts in §5. Stories #1–#4 and #7 (Step 1 only,
no submit) can ship first. #8 lands once #6 is unblocked.

---

## 7. Out of scope (v2)

- Organizer edit / cancel after submit (needs auth or magic link).
- Organizer dashboard / campaign history.
- Sold-out toggle on a published campaign.
- File uploads (poster, sponsor logos).
- Multiple contact people per organization.

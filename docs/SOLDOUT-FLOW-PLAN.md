# Sold-Out flow — plan

"Locuri ocupate": let an approved campaign's organizer stop registrations via a
per-campaign magic link they receive in the approval email. Once marked, the
campaign still shows on `/campanii` (and `/harta`, `/campanie/{id}`) but the
public phone is replaced by a closing notice **"⛔ Locuri ocupate. Mulțumim!"**.

Follows the existing citizen magic-link pattern (`/m/{token}` API + `/cont/{token}`
page) and the organizer email pattern (`send_campaign_email`).

## Data model (DB migration)

`lambda/migrations/2026-07-01-campaign-sold-out-and-manage-tokens.sql`

- `campaigns.sold_out boolean NOT NULL DEFAULT false` — the flag. A sold-out
  campaign stays `status='approved'`, so it remains inside `v_public_campaigns`
  (which filters approved + upcoming). No view change needed.
- `tokens.campaign_id bigint REFERENCES campaigns(id)` — lets a token point at a
  specific campaign. The `tokens` table already had `citizen_id` + `organizer_id`.

## Backend (Lambda)

**Token kind** `campaign_manage` — issued on approval, TTL 180 days, references the
campaign (`campaign_id`) and its organizer (`organizer_id`). Reusable (NOT consumed
on use), like `citizen_manage` — the organizer may revisit to reopen.

- `helpers.issue_token(..., campaign_id=None)` + `_load_token` selects `campaign_id`.
- `helpers.CAMPAIGN_MANAGE_PATH = "/gestionare-campanie"` + `_campaign_manage_url(token)`.
- `helpers.fetch_campaign_email_payload` also returns internal `organizer_id`.
- `helpers.send_campaign_email(..., manage_url=None)` → threads into templates.
- `email_templates.render(...)` 'approved' email gains a **"Gestionează campania"**
  button + one line explaining the sold-out control.

**Approval** (`admin.handle_admin_approve_campaign`): inside the existing
transaction, issue a `campaign_manage` token for the campaign; after commit pass
its URL as `manage_url` to the approved organizer email. (Nothing else changes.)

**Public routes** (`router.py` + `public_handlers.py`):
- `GET  /campaigns/manage/{token}` → `handle_get_campaign_manage` → `{ valid, campaign }`
  (org name, locality, county, dates, times, `soldOut`). `410 token_invalid` when bad.
- `POST /campaigns/manage/{token}/sold-out` → `handle_campaign_set_sold_out`.
  Body `{ soldOut?: boolean }` (default `true`). Sets `campaigns.sold_out`, audits
  `campaign.sold_out` / `campaign.reopen`. Idempotent. Returns `{ soldOut, message }`.

**Expose the flag on reads** (so the frontend can render it):
- `handle_list_campaigns`: `SELECT v.*, c.sold_out AS is_sold_out FROM v_public_campaigns v
  JOIN campaigns c ON c.public_id = v.submission_id ...` — adds the column without
  recreating the view.
- `handle_get_campaign`: add `c.sold_out AS "isSoldOut"`.

## Frontend (Nuxt)

**Proxy routes** (thin, `proxyAws`, mirror `/m/{token}`):
- `server/api/campaigns/manage/[token].get.ts`
- `server/api/campaigns/manage/[token]/sold-out.post.ts` (forwards the JSON body)

**Management page** `app/pages/gestionare-campanie/[token].vue` — mirrors
`cont/[token].vue`: fetches the campaign summary, shows the
**"Marchează Sold Out — oprește înscrierile"** button (and a "Redeschide
înscrierile" button once sold out, for mistake recovery). `noindex`.

**Config** `nuxt.config.ts`: add `/gestionare-campanie/` to `robots.disallow` and a
`'/gestionare-campanie/**': { robots: false }` route rule.

**Display side (already implemented + verified):** `PublicCampaign` carries
`isSoldOut`/`status`; `mapCampaign` + `normalizePublicCampaign` thread it through;
`CampaignCard`, the `/harta` SidePanel and `/campanie/{id}` hide the phone and show
the notice when sold out.

## Deploy notes

1. Run the migration against dev + prod RDS (from the EC2 box).
2. `./lambda/deploy.sh` (code only).
3. Ship the frontend.

Order matters: migration first (the Lambda reads `sold_out` / `tokens.campaign_id`).

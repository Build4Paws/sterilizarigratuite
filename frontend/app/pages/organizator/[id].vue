<template>
  <div class="page-organizator">

    <!-- 404 / not found -->
    <div v-if="notFound" class="container state-card state-card--pending">
      <Building2 class="state-card__icon" :size="48" />
      <h1 class="state-card__title">Organizatorul nu a fost găsit</h1>
      <p class="state-card__text">
        Nu există niciun organizator cu ID-ul <code class="id-chip">{{ id }}</code>,
        sau linkul este greșit.
      </p>
      <NuxtLink to="/campanii" class="state-card__link">Vezi toate campaniile →</NuxtLink>
    </div>

    <!-- Generic error -->
    <div v-else-if="fetchError" class="container state-card state-card--error">
      <AlertCircle class="state-card__icon" :size="48" />
      <h1 class="state-card__title">Nu s-au putut încărca datele</h1>
      <p class="state-card__text">{{ errorMessage }}</p>
    </div>

    <!-- Organizer profile -->
    <template v-else-if="profile">
      <!-- Hero / header -->
      <section class="hero">
        <div class="container hero__inner">
          <div class="hero__identity">
            <div class="hero__avatar" aria-hidden="true">
              <Building2 :size="32" />
            </div>
            <div class="hero__body">
              <p class="hero__eyebrow">Organizator</p>
              <h1 class="hero__title">{{ profile.organizationName }}</h1>
              <p v-if="statsLine" class="hero__stats">{{ statsLine }}</p>
            </div>
          </div>

          <!-- Action bar — single CTA for now; organizers will get more actions
               here later (edit profile, manage campaigns, etc.). -->
          <div class="hero__actions">
            <NuxtLink to="/organizatori" class="hero__cta">
              <Megaphone :size="18" aria-hidden="true" />
              Anunță o nouă campanie
            </NuxtLink>
          </div>
        </div>
      </section>

      <!-- Campaign lists -->
      <section class="container body">

        <!-- No campaigns at all -->
        <div v-if="!profile.campaigns.length" class="empty">
          <Inbox :size="40" class="empty__icon" aria-hidden="true" />
          <p class="empty__title">Nicio campanie încă</p>
          <p class="empty__text">
            Acest organizator nu a publicat încă nicio campanie de sterilizare.
          </p>
          <NuxtLink to="/organizatori" class="empty__cta">Anunță o nouă campanie →</NuxtLink>
        </div>

        <template v-else>
          <!-- Upcoming / ongoing -->
          <div v-if="upcomingCampaigns.length" class="group">
            <header class="group__head">
              <CalendarCheck :size="20" class="group__icon" aria-hidden="true" />
              <h2 class="group__title">Campanii viitoare și în desfășurare</h2>
              <span class="group__count">{{ upcomingCampaigns.length }}</span>
            </header>
            <ul class="grid">
              <li v-for="c in upcomingCampaigns" :key="c.key">
                <CampaignCard :campaign="c.card" />
              </li>
            </ul>
          </div>

          <!-- Past -->
          <div v-if="pastCampaigns.length" class="group">
            <header class="group__head">
              <History :size="20" class="group__icon" aria-hidden="true" />
              <h2 class="group__title">Campanii încheiate</h2>
              <span class="group__count">{{ pastCampaigns.length }}</span>
            </header>
            <ul class="grid">
              <li v-for="c in pastCampaigns" :key="c.key">
                <CampaignCard :campaign="c.card" />
              </li>
            </ul>
          </div>
        </template>

      </section>
    </template>

  </div>
</template>

<script setup lang="ts">
import { Building2, AlertCircle, Megaphone, CalendarCheck, History, Inbox } from 'lucide-vue-next'
import type { CampaignCardData, CampaignStatus, OrganizerCampaign, OrganizerProfile, Species } from '~/types'
import { ensureLocationIndexes, countyCodeToNameSync } from '~/composables/useLocationData'

definePageMeta({ layout: 'default' })

const route = useRoute()
const id = computed(() => String(route.params.id ?? ''))

interface EnrichedCampaign extends OrganizerCampaign { countyName: string }
interface EnrichedProfile { organizationName: string; campaigns: EnrichedCampaign[] }

// Resolve county names INSIDE useAsyncData so they land in the serialized
// payload. Resolving them in the template via `countyCodeToNameSync` caused a
// hydration mismatch: the server has the index built, but on the client the
// async-loaded index isn't ready at hydration, so it rendered the raw code.
// Doing it here means server and client hydrate from the same payload.
const { data: profile, error: fetchError } = await useAsyncData<EnrichedProfile>(
  `organizer-${id.value}`,
  async () => {
    const raw = await $fetch<OrganizerProfile>(`/api/organizer/${id.value}`)
    await ensureLocationIndexes()
    return {
      organizationName: raw.organizationName,
      campaigns: raw.campaigns.map(c => ({
        ...c,
        countyName: countyCodeToNameSync(c.county) || c.county,
      })),
    }
  },
)

const notFound = computed(() => {
  if (!fetchError.value) return false
  const status = (fetchError.value as { statusCode?: number }).statusCode
  return status === 404 || status === 400
})

const errorMessage = computed(() => extractApiError(fetchError.value))

// ── Header stats ──────────────────────────────────────────────────────────────
const statsLine = computed(() => {
  const campaigns = profile.value?.campaigns ?? []
  if (!campaigns.length) return ''
  const counties = new Set(campaigns.map(c => c.county)).size
  const nC = campaigns.length
  const nJ = counties
  return `${nC} ${nC === 1 ? 'campanie' : 'campanii'} · ${nJ} ${nJ === 1 ? 'județ' : 'județe'}`
})

// ── Map wire campaign → CampaignCardData ──────────────────────────────────────
function toCard(c: EnrichedCampaign): CampaignCardData {
  const species = (Object.keys(c.species) as Species[]).filter(k => k === 'dog' || k === 'cat')
  return {
    organizationName: profile.value?.organizationName ?? '',
    countyName: c.countyName,
    locality: c.locality,
    address: c.address,
    dateStart: c.dateStart,
    dateEnd: c.dateEnd ?? undefined,
    timeStart: c.timeStart,
    timeEnd: c.timeEnd,
    species,
    slotsDogs: c.species.dog,
    slotsCats: c.species.cat,
    phonePublic: '',
    status: c.status.toUpperCase() as CampaignStatus,
  }
}

/** Today as YYYY-MM-DD (local) — safe for string comparison with API dates. */
function localToday(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

interface CardEntry { key: string; card: CampaignCardData; start: string; end: string }

const entries = computed<CardEntry[]>(() =>
  (profile.value?.campaigns ?? []).map(c => ({
    key: c.submissionId,
    card: toCard(c),
    start: c.dateStart,
    end: c.dateEnd || c.dateStart,
  })),
)

// Upcoming/ongoing = end date today or later, soonest first.
const upcomingCampaigns = computed(() =>
  entries.value
    .filter(e => e.end >= localToday())
    .sort((a, b) => a.start.localeCompare(b.start)),
)

// Past = ended before today, most recent first.
const pastCampaigns = computed(() =>
  entries.value
    .filter(e => e.end < localToday())
    .sort((a, b) => b.start.localeCompare(a.start)),
)

// ── SEO — organizer pages are keyed by an unguessable UUID; keep them out of
// search indexes (consistent with /campanie/**). ──────────────────────────────
useSeoMeta({
  robots: 'noindex, nofollow',
  title: computed(() =>
    profile.value?.organizationName
      ? `${profile.value.organizationName} — campanii de sterilizare`
      : 'Organizator — Sterilizări Gratuite',
  ),
})
</script>

<style scoped>
.page-organizator {
  background: var(--color-bg-muted);
  min-height: 100vh;
}

/* ── Hero ── */
.hero {
  background: var(--color-primary);
  color: var(--color-text-light);
  padding: var(--space-2xl) 0;
}

.hero__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-lg);
}

.hero__identity {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  min-width: 0;
}

.hero__avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.14);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #fff;
}

.hero__body {
  min-width: 0;
}

.hero__eyebrow {
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-accent);
  margin: 0 0 2px;
}

.hero__title {
  font-family: var(--font-heading);
  font-size: clamp(1.4rem, 3.5vw, var(--font-size-2xl));
  font-weight: 800;
  line-height: var(--line-height-heading);
  margin: 0;
  color: #fff;
}

.hero__stats {
  font-size: var(--font-size-sm);
  color: rgba(255, 255, 255, 0.75);
  margin: var(--space-xs) 0 0;
}

/* ── Action bar (extensible — more organizer actions land here later) ── */
.hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.hero__cta {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  background: var(--color-accent);
  color: var(--color-text-light);
  font-family: var(--font-heading);
  font-weight: 600;
  font-size: var(--font-size-base);
  padding: var(--space-sm) var(--space-lg);
  border-radius: var(--radius-md);
  text-decoration: none;
  transition: background 0.2s, transform 0.1s;
}

.hero__cta:hover {
  background: var(--color-accent-hover);
  text-decoration: none;
}

.hero__cta:active {
  transform: translateY(1px);
}

/* ── Body ── */
.body {
  padding: var(--space-2xl) 0 var(--space-3xl);
  display: flex;
  flex-direction: column;
  gap: var(--space-2xl);
}

.group {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.group__head {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.group__icon {
  color: var(--color-primary);
  flex-shrink: 0;
}

.group__title {
  font-family: var(--font-heading);
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-primary);
  margin: 0;
}

.group__count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.5rem;
  height: 1.5rem;
  padding: 0 0.4rem;
  border-radius: 999px;
  background: rgba(4, 26, 73, 0.08);
  color: var(--color-primary);
  font-size: var(--font-size-sm);
  font-weight: 700;
}

/* ── 3-column card grid ── */
.grid {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-lg);
  align-items: start;
}

/* ── Empty state ── */
.empty {
  background: var(--color-bg);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-2xl) var(--space-lg);
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-sm);
}

.empty__icon {
  color: var(--color-text-muted);
  margin-bottom: var(--space-sm);
}

.empty__title {
  font-family: var(--font-heading);
  font-size: 1.1rem;
  color: var(--color-primary);
  margin: 0;
  font-weight: 700;
}

.empty__text {
  color: var(--color-text-muted);
  margin: 0;
  max-width: 420px;
  line-height: 1.5;
}

.empty__cta {
  margin-top: var(--space-sm);
  color: var(--color-accent);
  font-weight: 600;
  font-size: var(--font-size-sm);
  text-decoration: none;
}

.empty__cta:hover {
  text-decoration: underline;
}

/* ── State cards (not-found / error) ── */
.state-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: var(--space-md);
  margin: var(--space-2xl) auto;
  padding: var(--space-3xl) var(--space-xl);
  max-width: 600px;
  border-radius: var(--radius-lg);
  border: 1px dashed var(--color-border);
}

.state-card--pending { background: #fffbeb; border-color: #fbbf24; }
.state-card--error   { background: #fef2f2; border-color: var(--color-error); }

.state-card__icon { opacity: 0.7; color: var(--color-primary); }
.state-card--error .state-card__icon { color: var(--color-error); }

.state-card__title {
  font-family: var(--font-heading);
  font-size: var(--font-size-lg);
  color: var(--color-primary);
  margin: 0;
}

.state-card__text {
  color: var(--color-text-muted);
  margin: 0;
  line-height: 1.6;
  max-width: 480px;
}

.state-card__link {
  color: var(--color-accent);
  font-weight: 600;
  text-decoration: none;
}

.state-card__link:hover { text-decoration: underline; }

.id-chip {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.85em;
  background: var(--color-bg-muted, #f1f5f9);
  padding: 2px 7px;
  border-radius: 4px;
  word-break: break-all;
}

/* ── Responsive ── */
@media (max-width: 1024px) {
  .grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 680px) {
  .grid {
    grid-template-columns: 1fr;
  }

  .hero__actions {
    width: 100%;
  }

  .hero__cta {
    width: 100%;
    justify-content: center;
  }
}
</style>

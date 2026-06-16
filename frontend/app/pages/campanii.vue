<template>
  <div class="page-campanii">
    <!-- Hero -->
    <section class="hero">
      <div class="container hero__inner">
        <h1 class="hero__title">Campanii de sterilizare gratuită</h1>
        <p class="hero__subtitle">
          Găsește o campanie în zona ta. Sună direct la organizator pentru a te înscrie.
        </p>
      </div>
    </section>

    <!-- Filter bar -->
    <section class="filters">
      <div class="container filters__inner">
        <div class="filters__group">
          <UiCombobox
            id="filter-county"
            :model-value="countyCode"
            label="Județ"
            placeholder="Toate județele"
            :options="counties"
            @update:model-value="onCountyChange"
          />
        </div>
        <div class="filters__group">
          <UiSelect
            id="filter-species"
            :model-value="speciesUrl"
            label="Specie"
            :options="speciesOptions"
            @update:model-value="onSpeciesChange"
          />
        </div>
        <div v-if="hasActiveFilters" class="filters__reset">
          <UiButton variant="ghost" @click="resetFilters">
            <RotateCcw :size="16" aria-hidden="true" />
            Resetează filtrele
          </UiButton>
        </div>
      </div>
    </section>

    <!-- Guide CTA banner -->
    <section class="guide-banner" aria-label="Ghid sterilizare">
      <div class="container">
        <NuxtLink to="/ghid-sterilizare" class="guide-banner__card">
          <div class="guide-banner__icon" aria-hidden="true">
            <Stethoscope :size="22" />
          </div>
          <div class="guide-banner__body">
            <p class="guide-banner__eyebrow">Înainte de programare</p>
            <p class="guide-banner__title">
              Citește ghidul nostru de sterilizare: ce ai de făcut înainte, după și ce să știi despre procedură.
            </p>
          </div>
          <span class="guide-banner__cta">
            Vezi ghidul
            <ArrowRight :size="16" aria-hidden="true" />
          </span>
        </NuxtLink>
      </div>
    </section>

    <!-- Results -->
    <section class="list">
      <div class="container">
        <header class="list__header">
          <Calendar :size="22" class="list__icon" aria-hidden="true" />
          <h2 class="list__title">{{ headingText }}</h2>
        </header>

        <!-- Loading -->
        <ul v-if="loading" class="list__items" aria-busy="true">
          <li v-for="i in 3" :key="i">
            <div class="skeleton-card" aria-hidden="true">
              <div class="skeleton-card__head" />
              <div class="skeleton-card__line" />
              <div class="skeleton-card__line" />
              <div class="skeleton-card__line skeleton-card__line--short" />
              <div class="skeleton-card__cta" />
            </div>
          </li>
        </ul>

        <!-- Error -->
        <div v-else-if="error" class="list__error">
          <UiAlert variant="error">{{ errorMessage }}</UiAlert>
          <UiButton variant="secondary" @click="refresh()">
            Reîncearcă
          </UiButton>
        </div>

        <!-- Empty -->
        <div v-else-if="campaigns.length === 0" class="empty">
          <Inbox :size="40" class="empty__icon" aria-hidden="true" />
          <p class="empty__title">{{ emptyTitle }}</p>
          <p class="empty__text">{{ emptyText }}</p>
          <div class="empty__actions">
            <NuxtLink v-if="hasActiveFilters" to="/campanii" class="empty__link">
              Vezi toate campaniile
            </NuxtLink>
            <NuxtLink to="/" class="empty__cta">
              Anunță-mă
            </NuxtLink>
          </div>
        </div>

        <!-- Cards -->
        <ul v-else class="list__items">
          <li v-for="c in displayedCampaigns" :key="c.id">
            <CampaignCard :campaign="toCardData(c)" :show-call-cta="true" />
          </li>
        </ul>

        <!-- Infinite-scroll sentinel -->
        <div
          v-if="hasMore"
          ref="sentinelRef"
          class="list__sentinel"
          aria-hidden="true"
        />
        <p v-if="hasMore" class="list__loading-more" role="status">
          Se încarcă mai multe campanii…
        </p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { Calendar, Inbox, RotateCcw, Stethoscope, ArrowRight } from 'lucide-vue-next'
import type { Campaign, CampaignCardData, Species } from '~/types'

definePageMeta({ layout: 'default' })

const route = useRoute()
const router = useRouter()
const siteConfig = useSiteConfig()

// Load county indexes + names once for sync template lookups.
await ensureLocationIndexes()
const { counties, init: initCounties } = useLocationData()
await initCounties()

// URL ↔ internal species mapping.
const URL_TO_SPECIES: Record<string, Species> = { caine: 'dog', pisica: 'cat' }

const speciesOptions = [
  { value: '', label: 'Toate speciile' },
  { value: 'caine', label: 'Câini' },
  { value: 'pisica', label: 'Pisici' },
]

// URL-derived state.
const judetSlug = computed(() => String(route.query.judet ?? '').toLowerCase())
const speciesUrl = computed(() => String(route.query.specie ?? '').toLowerCase())

const countyCode = computed(() => slugToCountyCodeSync(judetSlug.value))
const countyName = computed(() => countyCodeToNameSync(countyCode.value))
const species = computed<Species | ''>(() => URL_TO_SPECIES[speciesUrl.value] ?? '')

// Fetch + filter.
const { campaigns, loading, error, refresh } = useCampaigns({
  countyCode,
  species,
})

// Infinite scroll — render-side window over the full result set. Backend
// pagination isn't supported yet; revisit when totals exceed ~80.
const PAGE_SIZE = 20
const displayedCount = ref(PAGE_SIZE)
const sentinelRef = ref<HTMLElement | null>(null)

const displayedCampaigns = computed(() =>
  campaigns.value.slice(0, displayedCount.value),
)
const hasMore = computed(() => displayedCount.value < campaigns.value.length)

useIntersectionObserver(
  sentinelRef,
  ([entry]) => {
    if (entry?.isIntersecting && hasMore.value) {
      displayedCount.value = Math.min(
        displayedCount.value + PAGE_SIZE,
        campaigns.value.length,
      )
    }
  },
  { rootMargin: '200px' },
)

// Reset window whenever the filtered result set changes (filter or refetch).
watch([countyCode, species], () => {
  displayedCount.value = PAGE_SIZE
})

const errorMessage = computed(() => extractApiError(error.value))

const hasActiveFilters = computed(() => !!countyCode.value || !!species.value)

// Heading text — adapts to active filters.
const headingText = computed(() => {
  const n = campaigns.value.length
  const noun = n === 1 ? 'campanie viitoare' : 'campanii viitoare'

  if (countyName.value && species.value) {
    const sp = species.value === 'dog' ? 'câini' : 'pisici'
    return `${n} ${noun} pentru ${sp} în ${countyName.value}`
  }
  if (countyName.value) {
    return `${n} ${noun} în ${countyName.value}`
  }
  if (species.value) {
    const sp = species.value === 'dog' ? 'câini' : 'pisici'
    return `${n} ${noun} pentru ${sp}`
  }
  return `${n} ${noun} în toată țara`
})

// Empty-state copy.
const emptyTitle = computed(() => {
  if (!hasActiveFilters.value) return 'Nu sunt campanii programate momentan.'
  if (countyName.value && species.value) {
    const sp = species.value === 'dog' ? 'câini' : 'pisici'
    return `Nu sunt campanii pentru ${sp} în ${countyName.value}.`
  }
  if (countyName.value) return `Nu sunt campanii viitoare în ${countyName.value}.`
  const sp = species.value === 'dog' ? 'câini' : 'pisici'
  return `Nu sunt campanii pentru ${sp} momentan.`
})

const emptyText = computed(() => {
  if (!hasActiveFilters.value) {
    return 'Lasă-ne telefonul sau emailul și te anunțăm când apare una în zona ta.'
  }
  if (species.value) return 'Încearcă alt județ sau altă specie.'
  return 'Încearcă alt județ.'
})

// Filter handlers — write to URL; refs follow reactively.
function onCountyChange(code: string) {
  const slug = code ? countyCodeToSlugSync(code) : ''
  syncUrl({ judet: slug, specie: speciesUrl.value })
}

function onSpeciesChange(value: string) {
  syncUrl({ judet: judetSlug.value, specie: value })
}

function resetFilters() {
  syncUrl({})
}

function syncUrl(query: { judet?: string; specie?: string }) {
  const cleaned: Record<string, string> = {}
  if (query.judet) cleaned.judet = query.judet
  if (query.specie) cleaned.specie = query.specie
  router.replace({ query: cleaned })
}

// Sync card data — `countyName` is already resolved in `useCampaigns` (baked
// into the SSR payload), so no template-time async lookup is needed here.
function toCardData(c: Campaign): CampaignCardData {
  return {
    organizationName: c.organizationName,
    countyName: c.countyName || c.county,
    locality: c.locality,
    address: c.address,
    dateStart: c.dateStart,
    dateEnd: c.dateEnd,
    timeStart: c.timeStart,
    timeEnd: c.timeEnd,
    species: c.species,
    slotsDogs: c.slotsDogs !== undefined ? Number(c.slotsDogs) : undefined,
    slotsCats: c.slotsCats !== undefined ? Number(c.slotsCats) : undefined,
    doctor: c.doctor,
    phonePublic: c.phonePublic,
    status: c.status,
    isSoldOut: c.isSoldOut,
  }
}

// ---- SEO ---------------------------------------------------------------
const siteUrl = siteConfig.url

const canonicalHref = computed(() => {
  // Specie variants canonicalize to the no-specie URL — avoids duplicate content.
  const u = new URL('/campanii', siteUrl)
  if (judetSlug.value) u.searchParams.set('judet', judetSlug.value)
  return u.toString()
})

const robotsValue = computed(() =>
  speciesUrl.value ? 'noindex, follow' : 'index, follow',
)

const seoTitle = computed(() => {
  if (countyName.value) {
    return `Campanii de sterilizare gratuită în ${countyName.value} · Sterilizări Gratuite`
  }
  return 'Campanii de sterilizare gratuită în toate județele active din România'
})

const seoDescription = computed(() => {
  if (countyName.value) {
    return `Vezi campaniile de sterilizare gratuită programate în ${countyName.value}. Câini și pisici. Sună direct la organizator pentru programare.`
  }
  return 'Toate campaniile de sterilizare gratuită active în România. Filtrează după județ și sună direct la organizator pentru programare.'
})

useSeoMeta({
  title: () => seoTitle.value,
  description: () => seoDescription.value,
  ogTitle: () => seoTitle.value,
  ogDescription: () => seoDescription.value,
  robots: () => robotsValue.value,
})

useHead(() => ({
  link: [{ rel: 'canonical', href: canonicalHref.value }],
}))

// ---- JSON-LD ------------------------------------------------------------
function pad(n: number) { return String(n).padStart(2, '0') }
function isoDateTime(date: string, time: string): string {
  // We don't know timezone reliably — leave naive (no Z). Crawlers tolerate this.
  const t = (time || '00:00').padEnd(5, '0')
  return `${date}T${t}:00`
}

const eventsLd = computed(() => {
  return campaigns.value.map((c) => ({
    '@context': 'https://schema.org',
    '@type': 'Event',
    name: `Campanie sterilizare gratuită în ${c.locality}`,
    startDate: isoDateTime(c.dateStart, c.timeStart),
    endDate: isoDateTime(c.dateEnd || c.dateStart, c.timeEnd),
    eventStatus: 'https://schema.org/EventScheduled',
    eventAttendanceMode: 'https://schema.org/OfflineEventAttendanceMode',
    location: {
      '@type': 'Place',
      name: c.locality,
      address: {
        '@type': 'PostalAddress',
        streetAddress: c.address,
        addressLocality: c.locality,
        addressRegion: c.countyName || c.county,
        addressCountry: 'RO',
      },
    },
    organizer: {
      '@type': 'Organization',
      name: c.organizationName,
      telephone: c.phonePublic,
    },
    isAccessibleForFree: true,
    offers: {
      '@type': 'Offer',
      price: '0',
      priceCurrency: 'RON',
      availability: 'https://schema.org/InStock',
      url: canonicalHref.value,
    },
  }))
})

const breadcrumbLd = computed(() => {
  const items: Record<string, unknown>[] = [
    { '@type': 'ListItem', position: 1, name: 'Acasă', item: `${siteUrl}/` },
    { '@type': 'ListItem', position: 2, name: 'Campanii', item: `${siteUrl}/campanii` },
  ]
  if (countyName.value) {
    items.push({
      '@type': 'ListItem',
      position: 3,
      name: countyName.value,
      item: canonicalHref.value,
    })
  }
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items,
  }
})

useHead(() => ({
  script: [
    ...eventsLd.value.map((e, i) => ({
      type: 'application/ld+json',
      key: `event-${i}`,
      innerHTML: safeJsonLd(e),
    })),
    {
      type: 'application/ld+json',
      key: 'breadcrumbs',
      innerHTML: safeJsonLd(breadcrumbLd.value),
    },
  ],
}))

</script>

<style scoped>
.page-campanii {
  background: var(--color-bg-muted);
  min-height: 100vh;
}

/* ---- Hero ---- */
.hero {
  background: var(--color-primary);
  color: var(--color-text-light);
  padding: var(--space-3xl) 0;
  text-align: center;
}

.hero__inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-md);
}

.hero__title {
  font-family: var(--font-heading);
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--color-text-light);
  margin: 0;
  max-width: 720px;
  line-height: 1.15;
}

.hero__subtitle {
  font-size: var(--font-size-lg);
  color: var(--color-slate-300);
  font-weight: 400;
  max-width: 620px;
  margin: 0;
  line-height: 1.5;
}

/* ---- Filter bar ---- */
.filters {
  background: var(--color-bg);
  border-bottom: 1px solid var(--color-border-light);
  position: sticky;
  top: 0;
  z-index: 10;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.filters__inner {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: var(--space-md);
  padding: var(--space-md);
  /* Align with the 720px-wide list column below. */
  max-width: 720px;
  margin: 0 auto;
}

.filters__group {
  flex: 0 1 240px;
  min-width: 180px;
  max-width: 280px;
}

.filters__reset {
  display: flex;
  align-items: flex-end;
  padding-bottom: 2px;
  margin-left: auto;
}

/* Compact the reset button so it fits on the same row as the two dropdowns
   instead of wrapping below them. */
.filters__reset :deep(.ui-btn) {
  padding: 0.5rem 0.85rem;
  font-size: var(--font-size-sm);
  border-width: 1px;
  white-space: nowrap;
}

/* ---- Guide CTA banner ---- */
.guide-banner {
  padding: var(--space-lg) 0 0;
}

.guide-banner__card {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  max-width: 720px;
  margin: 0 auto;
  padding: var(--space-md) var(--space-lg);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-left: 4px solid var(--color-accent);
  border-radius: var(--radius-md);
  color: var(--color-text);
  text-decoration: none;
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s;
}

.guide-banner__card:hover {
  border-color: var(--color-accent);
  box-shadow: 0 6px 18px rgba(249, 89, 5, 0.10);
  text-decoration: none;
  transform: translateY(-1px);
}

.guide-banner__icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(249, 89, 5, 0.10);
  color: var(--color-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.guide-banner__body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.guide-banner__eyebrow {
  font-family: var(--font-heading);
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-accent);
  margin: 0;
}

.guide-banner__title {
  font-size: var(--font-size-sm);
  color: var(--color-text);
  margin: 0;
  line-height: 1.45;
}

.guide-banner__cta {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  font-family: var(--font-heading);
  font-weight: 600;
  font-size: var(--font-size-sm);
  color: var(--color-primary);
  white-space: nowrap;
  flex-shrink: 0;
  transition: color 0.2s, gap 0.2s;
}

.guide-banner__card:hover .guide-banner__cta {
  color: var(--color-accent);
  gap: var(--space-sm);
}

@media (max-width: 600px) {
  .guide-banner {
    padding-top: var(--space-md);
  }

  .guide-banner__card {
    /* Icon + text on the first row, CTA on its own full-width row below. */
    flex-wrap: wrap;
    align-items: flex-start;
    gap: var(--space-sm) var(--space-md);
    padding: var(--space-md);
  }

  .guide-banner__icon {
    width: 38px;
    height: 38px;
  }

  .guide-banner__cta {
    flex-basis: 100%;
    justify-content: flex-start;
    margin-left: 0;
    padding-top: var(--space-sm);
    border-top: 1px solid var(--color-border-light);
  }
}

/* ---- List ---- */
.list {
  padding: var(--space-xl) 0 var(--space-3xl);
}

.list__header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin: 0 auto var(--space-lg);
  max-width: 720px;
}

.list__icon {
  color: var(--color-primary);
  flex-shrink: 0;
}

.list__title {
  font-family: var(--font-heading);
  font-size: 1.25rem;
  color: var(--color-primary);
  margin: 0;
  font-weight: 700;
  line-height: 1.3;
}

.list__items {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
  max-width: 720px;
  margin-inline: auto;
}

.list__sentinel {
  height: 1px;
  margin-top: var(--space-lg);
}

.list__loading-more {
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  margin: var(--space-md) 0 0;
}

/* ---- Skeleton ---- */
.skeleton-card {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  min-height: 280px;
}

.skeleton-card > * {
  background: linear-gradient(90deg, #eef2f7 0%, #f8fafc 50%, #eef2f7 100%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite linear;
  border-radius: var(--radius-sm);
}

.skeleton-card__head {
  height: 26px;
  width: 60%;
}

.skeleton-card__line {
  height: 14px;
  width: 90%;
}

.skeleton-card__line--short {
  width: 50%;
}

.skeleton-card__cta {
  height: 44px;
  width: 100%;
  margin-top: auto;
  border-radius: var(--radius-md);
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ---- Empty ---- */
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
  max-width: 720px;
  margin: 0 auto;
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
  max-width: 480px;
  line-height: 1.5;
}

.empty__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-md);
  margin-top: var(--space-md);
}

.empty__link {
  color: var(--color-primary);
  text-decoration: underline;
  font-weight: 500;
  align-self: center;
}

.empty__cta {
  display: inline-flex;
  align-items: center;
  background: var(--color-accent);
  color: var(--color-text-light);
  font-family: var(--font-heading);
  font-weight: 600;
  padding: var(--space-sm) var(--space-lg);
  border-radius: var(--radius-md);
  text-decoration: none;
  transition: background 0.2s;
}

.empty__cta:hover {
  background: var(--color-accent-hover);
}

/* ---- Error ---- */
.list__error {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  align-items: flex-start;
  max-width: 720px;
  margin: 0 auto;
}

/* ---- Responsive hero ---- */
@media (max-width: 768px) {
  .hero {
    padding: var(--space-xl) 0;
  }

  .hero__title {
    font-size: 1.5rem;
  }

  .hero__subtitle {
    font-size: 0.95rem;
  }

  .filters__inner {
    padding: var(--space-md);
  }

  .filters__group {
    flex: 1 1 100%;
    max-width: none;
  }

  .filters__reset {
    flex: 1 1 100%;
    margin-left: 0;
  }
}
</style>

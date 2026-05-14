<template>
  <div>
    <!-- Hero -->
    <section class="harta-hero">
      <div class="container harta-hero__inner">
        <h1 class="harta-hero__title">Harta sterilizărilor gratuite din România</h1>
        <p class="harta-hero__sub">
          {{ heroSub }}
        </p>

        <!-- View tabs -->
        <div class="harta-tabs" role="tablist" aria-label="Vizualizare hartă">
          <button
            v-for="tab in TABS"
            :key="tab.id"
            :id="`tab-${tab.id}`"
            role="tab"
            :aria-selected="activeView === tab.id"
            :aria-controls="`panel-${tab.id}`"
            :class="['harta-tab', { 'harta-tab--active': activeView === tab.id, 'harta-tab--disabled': tab.disabled }]"
            :disabled="tab.disabled"
            @click="setView(tab.id as ActiveView)"
          >
            {{ tab.label }}
            <span v-if="tab.disabled" class="harta-tab__soon">curând</span>
          </button>
        </div>
      </div>
    </section>

    <!-- Map + panel -->
    <section class="harta-body">
      <div class="container harta-body__inner">

        <!-- Map -->
        <div
          :id="`panel-${activeView}`"
          role="tabpanel"
          :aria-labelledby="`tab-${activeView}`"
          class="harta-map-col"
        >
          <div v-if="loading" class="harta-loading">Se încarcă datele…</div>
          <MapRomania
            :metric="activeMetric"
            :unit="activeUnit"
            :selected="selectedCode"
            :locality-registrations="selectedCountyData?.localities"
            :highlighted-locality="highlightedLocality"
            @hover="hoveredCode = $event"
            @select="onCountySelect"
            @clear="onClear"
          />
          <MapLegend
            v-if="activeView !== 'istoric'"
            :metric="activeMetric"
            :unit="activeUnit"
          />
        </div>

        <!-- Side panel -->
        <div ref="panelRef" class="harta-panel-col">
          <MapSidePanel
            :view="activeView"
            :selected="selectedCode"
            :county-data="selectedCountyData"
            :county-campaigns="selectedCampaigns"
            :top-ten="topTen"
            :cerere-by-county="regByCounty"
            :oferta-by-county="ofertaByCounty"
            @select="onCountySelect"
            @clear="onClear"
            @hover-locality="hoveredLocality = $event"
            @toggle-locality="onToggleLocality"
          />
        </div>

      </div>
    </section>

    <!-- Footer note -->
    <div class="container harta-attribution">
      <p>
        Hartă bazată pe
        <a href="https://commons.wikimedia.org/wiki/File:Romania_counties.svg" target="_blank" rel="noopener">
          Romania counties (Wikimedia, CC BY-SA 3.0)
        </a>.
        Date actualizate periodic. Sursa: Build4Paws.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Campaign, CountyStats } from '~/types'
import { slugToCountyCode, countyCodeToSlug, ensureLocationIndexes } from '~/composables/useLocationData'

type ActiveView = 'cerere' | 'oferta' | 'istoric'

const TABS = [
  { id: 'cerere', label: 'Cerere', disabled: false },
  { id: 'oferta', label: 'Ofertă', disabled: false },
  { id: 'istoric', label: 'Istoric', disabled: true },
] as const

// ── Route state ──────────────────────────────────────────────────────────────

const route = useRoute()
const router = useRouter()

const activeView = ref<ActiveView>(
  (['cerere', 'oferta', 'istoric'] as const).includes(route.query.view as ActiveView)
    ? (route.query.view as ActiveView)
    : 'cerere',
)

const selectedCode = ref('')

// Ensure county name indexes are available for SSR (top-10 list names)
onServerPrefetch(() => ensureLocationIndexes())

// Resolve ?judet= slug → 2-letter code after hydration
onMounted(async () => {
  await ensureLocationIndexes()
  if (route.query.judet) {
    const code = await slugToCountyCode(String(route.query.judet))
    if (code) selectedCode.value = code
  }
})

// ── Data fetching ────────────────────────────────────────────────────────────

const { byCounty: regByCounty, loading: regLoading } = useRegistrationStats()

// Always fetch campaigns so cross-view footer line stays accurate
const { campaigns, loading: campaignsLoading } = useCampaigns({ countyCode: ref(''), species: ref('') })

const loading = computed(() => regLoading.value || campaignsLoading.value)

// ── Derived metrics ──────────────────────────────────────────────────────────

const ofertaByCounty = computed<Record<string, number>>(() =>
  campaigns.value.reduce<Record<string, number>>((acc, c) => {
    const code = c.county.toUpperCase()
    acc[code] = (acc[code] ?? 0) + 1
    return acc
  }, {}),
)

const activeMetric = computed<Record<string, number>>(() => {
  if (activeView.value === 'oferta') return ofertaByCounty.value
  if (activeView.value === 'cerere') {
    return Object.fromEntries(
      Object.entries(regByCounty.value).map(([code, stats]) => [code, stats.total]),
    )
  }
  return {}
})

const activeUnit = computed(() => {
  if (activeView.value === 'oferta') return 'campanii'
  if (activeView.value === 'cerere') return 'înscrieri'
  return 'campanii încheiate'
})

const topTen = computed(() =>
  Object.entries(activeMetric.value)
    .map(([code, value]) => ({ code, value }))
    .sort((a, b) => b.value - a.value),
)

// ── Selected county helpers ──────────────────────────────────────────────────

const selectedCountyData = computed<CountyStats | undefined>(() => {
  if (!selectedCode.value) return undefined
  return regByCounty.value[selectedCode.value]
})

const selectedCampaigns = computed<Campaign[]>(() => {
  if (!selectedCode.value) return []
  return campaigns.value.filter(c => c.county.toUpperCase() === selectedCode.value)
})

// ── Interactions ─────────────────────────────────────────────────────────────

const hoveredCode = ref<string | null>(null)
const panelRef = ref<HTMLElement | null>(null)

// Highlighted locality (hover takes priority over the pinned/toggled one)
const hoveredLocality = ref<string | null>(null)
const pinnedLocality = ref<string | null>(null)
const highlightedLocality = computed(() => hoveredLocality.value || pinnedLocality.value)

function onToggleLocality(name: string) {
  pinnedLocality.value = pinnedLocality.value === name ? null : name
}

// Reset locality highlight when the county changes
watch(() => selectedCode.value, () => {
  hoveredLocality.value = null
  pinnedLocality.value = null
})

async function onCountySelect(code: string) {
  selectedCode.value = code
  const slug = await countyCodeToSlug(code)
  await router.replace({ query: { ...route.query, judet: slug } })

  // On stacked layout: scroll to panel
  if (import.meta.client && window.innerWidth < 1300) {
    await nextTick()
    panelRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

async function onClear() {
  selectedCode.value = ''
  const q = { ...route.query }
  delete q.judet
  await router.replace({ query: q })
}

async function setView(view: ActiveView) {
  if (view === 'istoric') return
  activeView.value = view
  // Switching tabs resets the map to the full-country view
  selectedCode.value = ''
  const q = { ...route.query } as Record<string, string | undefined>
  delete q.judet
  if (view === 'cerere') {
    delete q.view
  } else {
    q.view = view
  }
  await router.replace({ query: q })
}

// ── Hero copy ────────────────────────────────────────────────────────────────

const heroSub = computed(() => {
  if (activeView.value === 'oferta') return 'Vezi unde se desfășoară campanii de sterilizare gratuită chiar acum.'
  return 'Vezi unde e cea mai mare cerere și unde se țin campanii.'
})

// ── SEO ──────────────────────────────────────────────────────────────────────

useSeoMeta({
  title: computed(() =>
    activeView.value === 'oferta'
      ? 'Harta campaniilor de sterilizare gratuită în România'
      : 'Harta sterilizărilor gratuite din România — cerere',
  ),
  description: computed(() =>
    activeView.value === 'oferta'
      ? 'Vezi pe hartă unde se desfășoară campanii de sterilizare gratuită chiar acum.'
      : 'Vezi în ce județe sunt cei mai mulți oameni care așteaptă o campanie de sterilizare gratuită.',
  ),
})
</script>

<style scoped>
/* ── Hero ── */
.harta-hero {
  background: var(--color-primary);
  color: var(--color-text-light);
  padding: var(--space-2xl) 0 0;
}

.harta-hero__inner {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
  padding-bottom: 0;
}

.harta-hero__title {
  font-family: var(--font-heading);
  font-size: clamp(1.5rem, 4vw, var(--font-size-2xl));
  font-weight: 800;
  line-height: var(--line-height-heading);
}

.harta-hero__sub {
  font-size: var(--font-size-base);
  color: rgba(255, 255, 255, 0.75);
  max-width: 560px;
}

/* ── Tabs ── */
.harta-tabs {
  display: flex;
  gap: 2px;
  align-self: flex-start;
}

.harta-tab {
  background: rgba(255, 255, 255, 0.12);
  border: none;
  color: rgba(255, 255, 255, 0.7);
  font-family: var(--font-body);
  font-size: var(--font-size-sm);
  font-weight: 600;
  padding: var(--space-sm) var(--space-lg);
  cursor: pointer;
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  transition: background 0.15s, color 0.15s;
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.harta-tab:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.2);
  color: var(--color-text-light);
}

.harta-tab--active {
  background: var(--color-bg);
  color: var(--color-primary);
}

.harta-tab--active:hover {
  background: var(--color-bg) !important;
}

.harta-tab--disabled {
  opacity: 0.5;
  cursor: default;
}

.harta-tab__soon {
  font-size: 0.7rem;
  background: rgba(255, 255, 255, 0.2);
  padding: 1px 6px;
  border-radius: var(--radius-full);
  font-weight: 500;
}

/* ── Map + panel layout ── */
.harta-body {
  background: var(--color-bg-muted);
  padding: var(--space-xl) 0 var(--space-2xl);
}

.harta-body__inner {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: var(--space-xl);
  align-items: start;
}

.harta-map-col {
  position: relative;
  min-height: 200px;
}

.harta-panel-col {
  position: sticky;
  top: var(--space-xl);
}

/* ── Loading ── */
.harta-loading {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.6);
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  border-radius: var(--radius-md);
  z-index: 1;
}

/* ── Attribution ── */
.harta-attribution {
  padding: var(--space-md) 0;
}

.harta-attribution p {
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.harta-attribution a {
  color: var(--color-text-muted);
  text-decoration: underline;
}

/* ── Stacked layout (anything below 1300px) ── */
@media (max-width: 1300px) {
  .harta-body__inner {
    grid-template-columns: 1fr;
  }

  .harta-panel-col {
    position: static;
  }

  .harta-tabs {
    overflow-x: auto;
  }
}

@media (max-width: 768px) {
  .harta-hero__title {
    font-size: 1.5rem;
  }
}
</style>

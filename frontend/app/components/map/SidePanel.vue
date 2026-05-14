<template>
  <aside class="side-panel" :aria-live="selected ? 'polite' : undefined">

    <!-- Selected county -->
    <template v-if="selected && countyName">
      <div class="side-panel__header">
        <h2 class="side-panel__title">{{ countyName }}</h2>
        <button class="side-panel__close" aria-label="Închide panoul" @click="emit('clear')">
          <X :size="18" />
        </button>
      </div>

      <!-- Cerere selected — no data -->
      <template v-if="view === 'cerere' && (!countyData || countyData.total === 0)">
        <p class="side-panel__empty-county">
          Nicio cerere înregistrată din acest județ momentan.
        </p>
        <NuxtLink to="/" class="side-panel__cta">
          Înscrie-te pentru a fi notificat →
        </NuxtLink>
      </template>

      <!-- Cerere selected — has data -->
      <template v-else-if="view === 'cerere' && countyData">
        <p class="side-panel__big-number">{{ countyData.total.toLocaleString('ro-RO') }}</p>
        <p class="side-panel__unit">persoane înscrise</p>

        <div class="side-panel__species">
          <div class="side-panel__species-row">
            <span class="side-panel__species-label">
              <Dog :size="15" class="side-panel__species-icon" />
              Câini
            </span>
            <strong>{{ (countyData.species?.dog ?? 0).toLocaleString('ro-RO') }}</strong>
          </div>
          <div class="side-panel__species-row">
            <span class="side-panel__species-label">
              <Cat :size="15" class="side-panel__species-icon" />
              Pisici
            </span>
            <strong>{{ (countyData.species?.cat ?? 0).toLocaleString('ro-RO') }}</strong>
          </div>
        </div>

        <div v-if="topLocalities.length" class="side-panel__localities">
          <p class="side-panel__section-label">Top localități</p>
          <div
            v-for="[loc, n] in topLocalities"
            :key="loc"
            :class="['side-panel__loc-row', { 'is-pinned': pinnedLocality === loc }]"
            @mouseenter="emit('hover-locality', loc)"
            @mouseleave="emit('hover-locality', null)"
            @click="onLocalityClick(loc)"
          >
            <span class="side-panel__loc-name">{{ loc }}</span>
            <span class="side-panel__loc-count">{{ n }}</span>
          </div>
        </div>

        <NuxtLink to="/organizatori" class="side-panel__cta">
          Organizează o campanie aici →
        </NuxtLink>
      </template>

      <!-- Ofertă selected -->
      <template v-else-if="view === 'oferta'">
        <p class="side-panel__big-number">{{ countyCampaigns?.length ?? 0 }}</p>
        <p class="side-panel__unit">campanii active</p>

        <div v-if="countyCampaigns?.length" class="side-panel__campaigns">
          <div
            v-for="c in countyCampaigns"
            :key="c.id"
            class="side-panel__campaign-row"
          >
            <span class="side-panel__campaign-date">{{ formatDate(c.dateStart) }}</span>
            <span class="side-panel__campaign-loc">{{ c.locality }}</span>
            <span class="side-panel__campaign-org">{{ c.organizationName }}</span>
          </div>
        </div>
        <p v-else class="side-panel__empty">Nicio campanie activă în acest județ.</p>

        <NuxtLink :to="`/campanii?judet=${countySlug}`" class="side-panel__cta">
          Vezi toate campaniile →
        </NuxtLink>
      </template>

      <!-- Istoric selected -->
      <template v-else-if="view === 'istoric'">
        <p class="side-panel__placeholder">
          Statisticile campaniilor încheiate vor apărea aici curând.
        </p>
      </template>

      <!-- Cross-view footer line -->
      <div v-if="crossViewLine" class="side-panel__cross-view">
        {{ crossViewLine }}
      </div>
    </template>

    <!-- Default: top-10 list -->
    <template v-else>
      <h2 class="side-panel__title side-panel__title--default">{{ defaultTitle }}</h2>

      <template v-if="view === 'istoric'">
        <p class="side-panel__placeholder">
          Statisticile campaniilor încheiate vor apărea aici curând.
        </p>
      </template>

      <template v-else>
        <!-- Sort controls — only meaningful for Cerere (species data available) -->
        <div v-if="view === 'cerere' && topTen.length" class="side-panel__sort">
          <button
            v-for="opt in SORT_OPTIONS"
            :key="opt.key"
            :class="['side-panel__sort-btn', { 'is-active': sortBy === opt.key }]"
            @click="sortBy = opt.key"
          >
            <Dog v-if="opt.key === 'dog'" :size="12" aria-hidden="true" />
            <Cat v-if="opt.key === 'cat'" :size="12" aria-hidden="true" />
            {{ opt.label }}
          </button>
        </div>

        <div class="side-panel__list">
          <template v-if="topTen.length">
            <div
              v-for="(item, i) in visibleTopTen"
              :key="item.code"
              class="side-panel__top-row"
              role="button"
              tabindex="0"
              @click="emit('select', item.code)"
              @keydown.enter.prevent="emit('select', item.code)"
              @keydown.space.prevent="emit('select', item.code)"
            >
              <span class="side-panel__rank">{{ i + 1 }}</span>
              <span class="side-panel__county-name">{{ codeToName(item.code) }}</span>
              <template v-if="view === 'cerere'">
                <span class="side-panel__species-cell" :class="{ 'is-sort-key': sortBy === 'dog' }">
                  <Dog :size="13" aria-hidden="true" />{{ speciesDog(item.code) }}
                </span>
                <span class="side-panel__species-cell" :class="{ 'is-sort-key': sortBy === 'cat' }">
                  <Cat :size="13" aria-hidden="true" />{{ speciesCat(item.code) }}
                </span>
              </template>
              <span class="side-panel__value" :class="{ 'is-sort-key': sortBy === 'total' }">{{ item.value.toLocaleString('ro-RO') }}</span>
            </div>

            <button
              v-if="topTen.length > 10 && !showAll"
              class="side-panel__show-all"
              @click="showAll = true"
            >
              Vezi toate județele ({{ topTen.length }}) →
            </button>
          </template>
          <p v-else class="side-panel__empty">Niciun județ înregistrat încă.</p>
        </div>
      </template>
    </template>

  </aside>
</template>

<script setup lang="ts">
import { X, Dog, Cat } from 'lucide-vue-next'
import type { Campaign, CountyStats } from '~/types'
import { countyCodeToNameSync, countyCodeToSlugSync } from '~/composables/useLocationData'

const props = defineProps<{
  view: 'cerere' | 'oferta' | 'istoric'
  selected?: string
  countyData?: CountyStats
  countyCampaigns?: Campaign[]
  topTen: Array<{ code: string; value: number }>
  cerereByCounty?: Record<string, CountyStats>
  ofertaByCounty?: Record<string, number>
}>()

const emit = defineEmits<{
  select: [code: string]
  clear: []
  'hover-locality': [name: string | null]
  'toggle-locality': [name: string]
}>()

// Pinned locality (toggled by click; cleared when the county changes)
const pinnedLocality = ref<string | null>(null)
watch(() => props.selected, () => { pinnedLocality.value = null })

function onLocalityClick(name: string) {
  pinnedLocality.value = pinnedLocality.value === name ? null : name
  emit('toggle-locality', name)
}

const showAll = ref(false)

const countyName = computed(() => props.selected ? countyCodeToNameSync(props.selected) : '')
const countySlug = computed(() => props.selected ? countyCodeToSlugSync(props.selected) : '')

function codeToName(code: string) {
  return countyCodeToNameSync(code)
}

// ── Top-10 list — sort ───────────────────────────────────────────────────────

type SortKey = 'total' | 'dog' | 'cat'
const sortBy = ref<SortKey>('total')

// Reset sort + pagination when the view tab changes.
watch(() => props.view, () => {
  sortBy.value = 'total'
  showAll.value = false
})
watch(sortBy, () => { showAll.value = false })

const SORT_OPTIONS: { key: SortKey; label: string }[] = [
  { key: 'total', label: 'Total' },
  { key: 'dog',   label: 'Câini' },
  { key: 'cat',   label: 'Pisici' },
]

const sortedTopTen = computed(() => {
  if (sortBy.value === 'total' || props.view !== 'cerere') return props.topTen
  return [...props.topTen].sort((a, b) => {
    const get = (code: string) =>
      sortBy.value === 'dog'
        ? (props.cerereByCounty?.[code]?.species?.dog ?? 0)
        : (props.cerereByCounty?.[code]?.species?.cat ?? 0)
    return get(b.code) - get(a.code)
  })
})

const visibleTopTen = computed(() =>
  showAll.value ? sortedTopTen.value : sortedTopTen.value.slice(0, 10),
)

function speciesDog(code: string) {
  return props.cerereByCounty?.[code]?.species?.dog ?? 0
}
function speciesCat(code: string) {
  return props.cerereByCounty?.[code]?.species?.cat ?? 0
}

const defaultTitle = computed(() => {
  if (props.view === 'cerere') return 'Top județe după cerere'
  if (props.view === 'oferta') return 'Top județe după campanii'
  return 'Istoric campanii'
})

// ── Cerere selected helpers ──────────────────────────────────────────────────

const topLocalities = computed<[string, number][]>(() => {
  const locs = props.countyData?.localities
  if (!locs) return []
  return Object.entries(locs)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5)
})

// ── Cross-view footer ────────────────────────────────────────────────────────

const crossViewLine = computed(() => {
  if (!props.selected) return ''
  const code = props.selected
  const inscr = props.cerereByCounty?.[code]?.total ?? 0
  const camp = props.ofertaByCounty?.[code] ?? 0
  if (!inscr && !camp) return ''
  const parts: string[] = []
  if (inscr) parts.push(`${inscr.toLocaleString('ro-RO')} înscrieri`)
  if (camp) parts.push(`${camp} campanii active`)
  return `În acest județ: ${parts.join(' · ')}`
})

// ── Ofertă helpers ───────────────────────────────────────────────────────────

function formatDate(iso: string) {
  if (!iso) return ''
  const [y, m, d] = iso.split('-')
  return `${d}.${m}.${y}`
}
</script>

<style scoped>
.side-panel {
  background: var(--color-bg);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  min-height: 300px;
}

/* ── Header ── */
.side-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-sm);
}

.side-panel__title {
  font-family: var(--font-heading);
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--color-primary);
  line-height: var(--line-height-heading);
}

.side-panel__title--default {
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-family: var(--font-body);
  text-align: left;
}

.side-panel__close {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-text-muted);
  padding: var(--space-xs);
  display: flex;
  border-radius: var(--radius-sm);
  transition: color 0.15s, background 0.15s;
  flex-shrink: 0;
}

.side-panel__close:hover {
  color: var(--color-text);
  background: var(--color-bg-muted);
}

/* ── Big number ── */
.side-panel__big-number {
  font-family: var(--font-heading);
  font-size: 2.5rem;
  font-weight: 800;
  color: var(--color-primary);
  line-height: 1;
}

.side-panel__unit {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  margin-top: -var(--space-xs);
}

/* ── Species breakdown ── */
.side-panel__species {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  padding: var(--space-sm) 0;
  border-top: 1px solid var(--color-border-light);
  border-bottom: 1px solid var(--color-border-light);
}

.side-panel__species-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.side-panel__species-label {
  display: flex;
  align-items: center;
  gap: 5px;
}

.side-panel__species-icon {
  color: var(--color-primary);
  flex-shrink: 0;
}

.side-panel__species-row strong {
  color: var(--color-text);
  font-weight: 600;
}

.side-panel__empty-county {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  line-height: 1.6;
  font-style: italic;
}

/* ── Top localities ── */
.side-panel__section-label {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: var(--space-xs);
}

.side-panel__loc-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--font-size-sm);
  padding: 2px var(--space-xs);
  margin: 0 calc(-1 * var(--space-xs));
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background-color 0.12s;
}

.side-panel__loc-row:hover,
.side-panel__loc-row.is-pinned {
  background-color: var(--color-bg-muted);
}

.side-panel__loc-row.is-pinned .side-panel__loc-name {
  color: var(--color-accent);
}

.side-panel__loc-name {
  color: var(--color-text);
}

.side-panel__loc-count {
  color: var(--color-text-muted);
  font-weight: 600;
}

/* ── CTA ── */
.side-panel__cta {
  display: inline-block;
  margin-top: auto;
  color: var(--color-accent);
  font-weight: 600;
  font-size: var(--font-size-sm);
  text-decoration: none;
  transition: color 0.15s;
}

.side-panel__cta:hover {
  color: var(--color-accent-hover);
  text-decoration: underline;
}

/* ── Sort controls ── */
.side-panel__sort {
  display: flex;
  gap: 4px;
  padding-bottom: var(--space-xs);
  border-bottom: 1px solid var(--color-border-light);
  margin-bottom: 2px;
}

.side-panel__sort-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  padding: 3px 8px;
  font-size: 0.72rem;
  font-weight: 500;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: color 0.12s, background 0.12s, border-color 0.12s;
  line-height: 1.4;
}

.side-panel__sort-btn:hover {
  color: var(--color-text);
  background: var(--color-bg-muted);
}

.side-panel__sort-btn.is-active {
  color: var(--color-primary);
  background: rgba(4, 26, 73, 0.06);
  border-color: rgba(4, 26, 73, 0.15);
  font-weight: 600;
}

/* ── Top-10 list — full-width rows, per-row hover ── */
.side-panel__list {
  /* Break out of the panel's horizontal padding so the hover bg reaches the edges. */
  margin-inline: calc(-1 * var(--space-lg));
}

.side-panel__top-row {
  /* rank | name | dog-cell | cat-cell | total */
  display: grid;
  grid-template-columns: 1.4rem 1fr auto auto auto;
  align-items: center;
  column-gap: 8px;
  padding: 6px 10px;
  cursor: pointer;
  outline: none;
  transition: background 0.12s;
}

.side-panel__top-row:hover,
.side-panel__top-row:focus-visible {
  background: var(--color-bg-muted);
}

.side-panel__rank {
  font-size: 0.72rem;
  color: var(--color-text-muted);
  font-weight: 500;
  text-align: right;
  line-height: 1;
}

.side-panel__county-name {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: left;
}

.side-panel__species-cell {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 0.75rem;
  font-weight: 400;
  color: var(--color-text-muted);
  white-space: nowrap;
  line-height: 1;
  transition: color 0.12s, font-weight 0.12s;
}

.side-panel__species-cell svg {
  opacity: 0.45;
  flex-shrink: 0;
  transition: opacity 0.12s;
}

.side-panel__value {
  font-size: var(--font-size-sm);
  font-weight: 400;
  color: var(--color-text-muted);
  text-align: right;
  white-space: nowrap;
  min-width: 1.8rem;
  transition: color 0.12s, font-weight 0.12s;
}

/* Active sort column — bold + primary color */
.side-panel__species-cell.is-sort-key,
.side-panel__value.is-sort-key {
  font-weight: 700;
  color: var(--color-primary);
}

.side-panel__species-cell.is-sort-key svg {
  opacity: 0.8;
}

/* ── Campaigns list ── */
.side-panel__campaigns {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  max-height: 240px;
  overflow-y: auto;
}

.side-panel__campaign-row {
  display: flex;
  flex-direction: column;
  gap: 1px;
  padding: var(--space-xs) 0;
  border-bottom: 1px solid var(--color-border-light);
  font-size: var(--font-size-sm);
}

.side-panel__campaign-date {
  font-weight: 600;
  color: var(--color-primary);
}

.side-panel__campaign-loc {
  color: var(--color-text);
}

.side-panel__campaign-org {
  color: var(--color-text-muted);
  font-size: 0.8rem;
}

/* ── Misc ── */
.side-panel__show-all {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-accent);
  font-size: var(--font-size-sm);
  font-weight: 600;
  padding: 6px 10px;
  text-align: left;
  display: block;
  width: 100%;
  transition: color 0.15s, background 0.12s;
}

.side-panel__show-all:hover {
  background: var(--color-bg-muted);
  color: var(--color-accent-hover);
}

.side-panel__empty {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  font-style: italic;
}

.side-panel__placeholder {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  line-height: 1.6;
}

.side-panel__cross-view {
  margin-top: auto;
  padding-top: var(--space-sm);
  border-top: 1px solid var(--color-border-light);
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.side-panel__localities {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
</style>

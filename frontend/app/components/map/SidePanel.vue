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
          <div v-for="[loc, n] in topLocalities" :key="loc" class="side-panel__loc-row">
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
            <span class="side-panel__bar-wrap">
              <span class="side-panel__bar" :style="{ width: barWidth(item.value) + '%' }" />
            </span>
            <span class="side-panel__value">{{ item.value.toLocaleString('ro-RO') }}</span>
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
}>()

const showAll = ref(false)

const countyName = computed(() => props.selected ? countyCodeToNameSync(props.selected) : '')
const countySlug = computed(() => props.selected ? countyCodeToSlugSync(props.selected) : '')

function codeToName(code: string) {
  return countyCodeToNameSync(code)
}

// ── Top-10 list ──────────────────────────────────────────────────────────────

const visibleTopTen = computed(() =>
  showAll.value ? props.topTen : props.topTen.slice(0, 10),
)

const maxVal = computed(() => props.topTen[0]?.value ?? 1)

function barWidth(val: number) {
  return Math.round((val / maxVal.value) * 100)
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
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-family: var(--font-body);
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
  font-size: var(--font-size-sm);
  padding: 2px 0;
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

/* ── Top-10 list ── */
.side-panel__top-row {
  display: grid;
  grid-template-columns: 1.5rem 1fr auto auto;
  align-items: center;
  gap: var(--space-sm);
  padding: 5px var(--space-xs);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 0.12s;
  outline: none;
}

.side-panel__top-row:hover,
.side-panel__top-row:focus-visible {
  background: var(--color-bg-muted);
}

.side-panel__rank {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  font-weight: 600;
  text-align: right;
}

.side-panel__county-name {
  font-size: var(--font-size-sm);
  color: var(--color-text);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.side-panel__bar-wrap {
  width: 60px;
  height: 6px;
  background: var(--color-border-light);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.side-panel__bar {
  display: block;
  height: 100%;
  background: var(--color-primary);
  border-radius: var(--radius-full);
  transition: width 300ms ease;
}

.side-panel__value {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  font-weight: 600;
  min-width: 2.5rem;
  text-align: right;
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
  padding: var(--space-xs) 0;
  text-align: left;
  transition: color 0.15s;
}

.side-panel__show-all:hover {
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

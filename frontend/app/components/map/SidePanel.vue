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
        <p class="side-panel__total">
          <span class="side-panel__big-number">{{ countyData.total.toLocaleString('ro-RO') }}</span>
          <span class="side-panel__unit">persoane înscrise</span>
        </p>

        <!-- Species breakdown — hidden while viewing all localities. These are
             requests per species (a person can ask for both), so they don't sum
             to the "persoane înscrise" total. -->
        <div v-if="!showAllLocalities" class="side-panel__species">
          <div class="side-panel__species-row">
            <span class="side-panel__species-label">
              <UiSpeciesIcon species="dog" :size="15" class="side-panel__species-icon" />
              Cereri câini
            </span>
            <strong>{{ (countyData.species?.dog ?? 0).toLocaleString('ro-RO') }}</strong>
          </div>
          <div class="side-panel__species-row">
            <span class="side-panel__species-label">
              <UiSpeciesIcon species="cat" :size="15" class="side-panel__species-icon" />
              Cereri pisici
            </span>
            <strong>{{ (countyData.species?.cat ?? 0).toLocaleString('ro-RO') }}</strong>
          </div>
        </div>
        <p v-if="!showAllLocalities" class="side-panel__hint">
          O persoană poate cere sterilizare pentru mai multe specii.
        </p>

        <button
          v-if="showAllLocalities"
          class="side-panel__back"
          @click="showAllLocalities = false"
        >
          <ArrowLeft :size="16" aria-hidden="true" />
          Înapoi
        </button>

        <div v-if="localitiesList.length" class="side-panel__localities">
          <div class="side-panel__loc-head">
            <p class="side-panel__section-label">
              {{ showAllLocalities ? 'Toate cererile din județ' : 'Top localități' }}
            </p>
            <button
              v-if="!showAllLocalities && hasMoreLocalities"
              class="side-panel__see-all"
              @click="showAllLocalities = true"
            >
              Vezi toate →
            </button>
          </div>

          <div class="side-panel__loc-list" :class="{ 'is-scroll': showAllLocalities }">
            <div
              v-for="[loc, n] in localitiesList"
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
        </div>

        <NuxtLink v-if="!showAllLocalities" to="/organizatori" class="side-panel__cta">
          Organizează o campanie aici →
        </NuxtLink>
      </template>

      <!-- Ofertă selected -->
      <template v-else-if="view === 'oferta'">
        <p class="side-panel__big-number">{{ countyCampaigns?.length ?? 0 }}</p>
        <p class="side-panel__unit">campanii active</p>

        <div v-if="countyCampaigns?.length" class="side-panel__campaigns">
          <NuxtLink
            v-for="c in countyCampaigns"
            :key="c.id"
            :to="`/campanie/${c.id}`"
            class="side-panel__campaign-row"
          >
            <span class="side-panel__campaign-date">
              {{ formatDate(c.dateStart)
              }}<template v-if="c.timeStart && c.timeEnd">, {{ c.timeStart }}–{{ c.timeEnd }}</template>
            </span>
            <span class="side-panel__campaign-loc">{{ c.locality }}</span>
            <span class="side-panel__campaign-org">{{ c.organizationName }}</span>
            <a
              v-if="c.phonePublic"
              :href="`tel:${c.phonePublic}`"
              class="side-panel__campaign-phone"
              @click.stop
            >
              <Phone :size="12" aria-hidden="true" />
              {{ c.phonePublic }}
            </a>
          </NuxtLink>
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
        <!-- Species filter — only for Cerere; also recolors the map -->
        <div v-if="view === 'cerere' && topTen.length" class="side-panel__sort" role="group" aria-label="Filtrează după specie">
          <button
            v-for="opt in SPECIES_OPTIONS"
            :key="opt.key"
            :class="['side-panel__sort-btn', { 'is-active': species === opt.key }]"
            @click="species = opt.key"
          >
            <UiSpeciesIcon v-if="opt.key === 'dog'" species="dog" :size="12" />
            <UiSpeciesIcon v-if="opt.key === 'cat'" species="cat" :size="12" />
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
              <span class="side-panel__value">
                <UiSpeciesIcon v-if="view === 'cerere' && species === 'dog'" species="dog" :size="13" />
                <UiSpeciesIcon v-else-if="view === 'cerere' && species === 'cat'" species="cat" :size="13" />
                {{ item.value.toLocaleString('ro-RO') }}
              </span>
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
import { X, ArrowLeft, Phone } from 'lucide-vue-next'
import type { Campaign, CountyStats } from '~/types'
import { countyCodeToNameSync, countyCodeToSlugSync } from '~/composables/useLocationData'

const props = defineProps<{
  view: 'cerere' | 'oferta' | 'istoric'
  selected?: string
  countyData?: CountyStats
  countyCampaigns?: Campaign[]
  topTen: Array<{ code: string; value: number }>
}>()

// Cerere species filter, owned by the parent (it also drives the map coloring).
// 'total' = all species, 'dog', 'cat'.
const species = defineModel<'total' | 'dog' | 'cat'>('species', { default: 'total' })

const emit = defineEmits<{
  select: [code: string]
  clear: []
  'hover-locality': [name: string | null]
  'toggle-locality': [name: string]
}>()

// Pinned locality (toggled by click; cleared when the county changes). Clicking
// a locality row also raises its pin/label to the front of the map.
const pinnedLocality = ref<string | null>(null)

// "Vezi toate" → expand the Cerere panel to list every locality in the county.
const showAllLocalities = ref(false)

watch(() => props.selected, () => {
  pinnedLocality.value = null
  showAllLocalities.value = false
})

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

// ── Top-10 list — species filter ─────────────────────────────────────────────

// Collapse the expanded list when the view tab or species changes. The parent
// resets `species` itself when the view changes, so we don't touch it here.
watch(() => props.view, () => {
  showAll.value = false
  showAllLocalities.value = false
})
watch(species, () => { showAll.value = false })

const SPECIES_OPTIONS: { key: 'total' | 'dog' | 'cat'; label: string }[] = [
  { key: 'total', label: 'Total' },
  { key: 'dog',   label: 'Câini' },
  { key: 'cat',   label: 'Pisici' },
]

// `topTen` already arrives sorted and valued for the active species — the parent
// derives it from the same metric that colors the map — so we only paginate it.
const visibleTopTen = computed(() =>
  showAll.value ? props.topTen : props.topTen.slice(0, 10),
)

const defaultTitle = computed(() => {
  if (props.view === 'oferta') return 'Top județe după campanii'
  if (props.view === 'cerere') {
    if (species.value === 'dog') return 'Top județe după cerere câini'
    if (species.value === 'cat') return 'Top județe după cerere pisici'
    return 'Top județe după persoane înscrise'
  }
  return 'Istoric campanii'
})

// ── Cerere selected helpers ──────────────────────────────────────────────────

// All localities with registrations, sorted by count desc. The default panel
// shows the top 5; "Vezi toate" reveals the full list.
const allLocalities = computed<[string, number][]>(() => {
  const locs = props.countyData?.localities
  if (!locs) return []
  return Object.entries(locs).sort(([, a], [, b]) => b - a)
})

const TOP_LOCALITIES = 5
const topLocalities = computed(() => allLocalities.value.slice(0, TOP_LOCALITIES))
const localitiesList = computed(() =>
  showAllLocalities.value ? allLocalities.value : topLocalities.value,
)
const hasMoreLocalities = computed(() => allLocalities.value.length > TOP_LOCALITIES)

// Campaign dates render via the auto-imported `formatDate` (utils/format) —
// Romanian dd/mm/yyyy, consistent with the rest of the app.
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
  /* Never let an item's text widen the panel — long words wrap instead of
     forcing a horizontal scrollbar. `min-width: 0` lets the panel shrink inside
     its grid column rather than being sized by its widest unbreakable child. */
  min-width: 0;
  overflow-wrap: anywhere;
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

/* ── Big number — total + label inline ── */
.side-panel__total {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: var(--space-xs) var(--space-sm);
}

.side-panel__big-number {
  font-family: var(--font-heading);
  font-size: 2.25rem;
  font-weight: 800;
  color: var(--color-primary);
  line-height: 1;
}

.side-panel__unit {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
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

/* Clarifies that per-species requests don't sum to the people total. */
.side-panel__hint {
  font-size: 0.72rem;
  color: var(--color-text-muted);
  font-style: italic;
  margin-top: var(--space-xs);
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
  margin: 0;
}

.side-panel__loc-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
  padding-bottom: var(--space-xs);
  border-bottom: 1px solid var(--color-border-light);
}

.side-panel__see-all {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-accent);
  font-family: var(--font-body);
  font-size: 0.78rem;
  font-weight: 600;
  white-space: nowrap;
  padding: 0;
  transition: color 0.15s;
}

.side-panel__see-all:hover {
  color: var(--color-accent-hover);
  text-decoration: underline;
}

/* Scrollable full list in "Toate cererile din județ" mode */
.side-panel__loc-list.is-scroll {
  max-height: 360px;
  overflow-y: auto;
  margin: 0 calc(-1 * var(--space-xs));
  padding: 0 var(--space-xs);
}

/* Back button — return from the all-localities view */
.side-panel__back {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  align-self: flex-start;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-text-muted);
  font-family: var(--font-body);
  font-size: var(--font-size-sm);
  font-weight: 600;
  padding: 0;
  transition: color 0.15s;
}

.side-panel__back:hover {
  color: var(--color-primary);
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
  /* rank | name | value */
  display: grid;
  grid-template-columns: 1.4rem 1fr auto;
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

.side-panel__value {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-primary);
  text-align: right;
  white-space: nowrap;
  min-width: 1.8rem;
}

.side-panel__value svg {
  opacity: 0.55;
  flex-shrink: 0;
}

/* ── Campaigns list ── */
.side-panel__campaigns {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  max-height: 240px;
  overflow-y: auto;
  /* Contain the rows' negative-margin hover breakout so it doesn't spill past
     the container and trigger a horizontal scrollbar (overflow-y: auto makes
     overflow-x compute to auto). Also hard-clip any residual x overflow. */
  padding-inline: var(--space-xs);
  overflow-x: hidden;
}

.side-panel__campaign-row {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: var(--space-xs);
  margin: 0 calc(-1 * var(--space-xs));
  border-bottom: 1px solid var(--color-border-light);
  font-size: var(--font-size-sm);
  text-decoration: none;
  color: inherit;
  transition: background 0.12s;
  /* Let the row shrink to the panel and wrap long org names/addresses. */
  min-width: 0;
  overflow-wrap: anywhere;
}

.side-panel__campaign-row:hover {
  background: var(--color-bg-muted);
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

.side-panel__campaign-phone {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  align-self: flex-start;
  margin-top: 2px;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-accent);
  text-decoration: none;
}

.side-panel__campaign-phone:hover {
  color: var(--color-accent-hover);
  text-decoration: underline;
}

/* ── Misc ── */
.side-panel__show-all {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-accent);
  font-size: var(--font-size-sm);
  font-weight: 600;
  /* Align the label with the county names above (past the rank column),
     and add a little breathing room from the last row. */
  padding: 6px 10px;
  padding-left: calc(10px + 1.4rem + 8px);
  margin-top: var(--space-sm);
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

.side-panel__localities {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
</style>

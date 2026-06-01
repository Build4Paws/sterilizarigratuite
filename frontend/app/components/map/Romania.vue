<template>
  <div class="map-wrapper" @mouseleave="onWrapperMouseLeave">
    <svg
      xmlns="http://www.w3.org/2000/svg"
      :viewBox="currentViewBox"
      class="map-svg"
      :class="{ 'map-svg--zoomed': isZoomed }"
      aria-label="Harta județelor din România"
    >
      <path
        v-for="county in COUNTY_PATHS"
        :key="county.code"
        :id="`RO-${county.code}`"
        :data-code="county.code"
        :class="['county', {
          'is-selected': county.code === selected,
          'is-faded': isZoomed && county.code !== selected,
        }]"
        :style="{ '--fill': fillFor(county.code) }"
        :aria-label="`${county.name} — ${props.metric[county.code] ?? 0} ${props.unit}`"
        :tabindex="isZoomed && county.code !== selected ? -1 : 0"
        role="button"
        :d="county.d"
        @mouseenter="onEnter($event, county.code, county.name)"
        @mousemove="onMove"
        @click="onCountyClick(county.code)"
        @keydown.enter.prevent="onCountyClick(county.code)"
        @keydown.space.prevent="onCountyClick(county.code)"
      />

      <g v-if="selected && localitiesForCounty.length" class="localities">
        <circle
          v-for="(loc, i) in orderedLocalities"
          :key="`dot-${loc.n}`"
          :cx="loc.x"
          :cy="loc.y"
          :r="dotRadius(loc.t)"
          :class="['locality-dot', `locality-dot--t${loc.t}`, { 'is-active': isLocalityActive(loc.n), 'is-dimmed': isLocalityDimmed(loc.n) }]"
          :style="{ '--i': Math.min(i, 30) }"
          vector-effect="non-scaling-stroke"
          @mouseenter="hoveredLocality = loc.n"
          @mouseleave="hoveredLocality = null"
        />
        <text
          v-for="loc in orderedLocalities"
          :key="`label-${loc.n}`"
          :x="loc.x"
          :y="loc.y - dotRadius(loc.t) - labelOffset"
          :font-size="labelFontSize"
          :class="['locality-label', `locality-label--t${loc.t}`, { 'is-active': isLocalityActive(loc.n), 'is-dimmed': isLocalityDimmed(loc.n) }]"
          text-anchor="middle"
          aria-hidden="true"
        >{{ loc.n }}</text>
      </g>
    </svg>

    <button
      v-if="isZoomed"
      class="map-back-btn"
      type="button"
      aria-label="Înapoi la harta României"
      @click="emit('clear')"
    >
      <ArrowLeft :size="16" />
      <span>Toată harta</span>
    </button>

    <div
      v-if="tooltip.visible"
      class="map-tooltip"
      :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }"
      aria-hidden="true"
    >
      {{ tooltip.text }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ArrowLeft } from 'lucide-vue-next'
import { COUNTY_PATHS } from '~/assets/maps/counties'
import countyBBoxes from '~/assets/maps/county-bboxes.json'

interface Locality { n: string; x: number; y: number; t: 1 | 2; p: number }

const props = withDefaults(defineProps<{
  metric: Record<string, number>
  unit: string
  // active map view — drives the coloring model (graduated for cerere, binary
  // grey/blue for oferta) and whether locality labels show without a hover.
  view?: 'cerere' | 'oferta' | 'istoric'
  selected?: string
  // locality names to prioritise as dots for the selected county
  // (campaign localities in `oferta`, registration localities in `cerere`)
  priorityLocalities?: string[]
  // externally highlighted locality (hover or click) — drives z-order + emphasis
  highlightedLocality?: string | null
  // pinned (clicked) locality — when set, every other locality is dimmed so the
  // pinned one is easy to spot. Cleared on a second click (toggle).
  pinnedLocality?: string | null
}>(), {
  view: 'cerere',
  selected: undefined,
  priorityLocalities: () => [],
  highlightedLocality: null,
  pinnedLocality: null,
})

const emit = defineEmits<{
  hover: [code: string | null]
  select: [code: string]
  clear: []
}>()

// ── Color models ────────────────────────────────────────────────────────────
// Cerere: graduated blue scale (grey → dark blue), 4 buckets, 20/30/30/20 split.
// Oferta: binary — grey where there are no campaigns, dark blue where there are;
//         the selected county switches to a soft light blue.

const FILLS = [
  'var(--map-low)',
  'var(--map-mid-low)',
  'var(--map-mid-high)',
  'var(--map-high)',
] as const

const cutPoints = computed<[number, number, number]>(() => {
  const vals = Object.values(props.metric).filter(v => v > 0).sort((a, b) => a - b)
  if (!vals.length) return [1, 2, 3]
  const p = (pct: number) => vals[Math.max(0, Math.ceil(vals.length * pct) - 1)] ?? 0
  return [p(0.2), p(0.5), p(0.8)]
})

function fillFor(code: string): string {
  const val = props.metric[code] ?? 0

  if (props.view === 'oferta') {
    // Selected county reads as soft light blue so its dots/labels stand out.
    if (code === props.selected) return 'var(--map-offer-selected)'
    return val > 0 ? 'var(--map-offer-has)' : 'var(--map-none)'
  }

  if (!val) return 'var(--map-none)'
  const [p20, p50, p80] = cutPoints.value
  if (val <= p20) return FILLS[0]
  if (val <= p50) return FILLS[1]
  if (val <= p80) return FILLS[2]
  return FILLS[3]
}

// ── Zoom animation ───────────────────────────────────────────────────────────

const FULL_VIEWBOX = { x: 0, y: 0, w: 613, h: 433 }
const ASPECT = FULL_VIEWBOX.w / FULL_VIEWBOX.h
const PAD = 1.25 // 25% padding around the county bbox

const viewBox = reactive({ ...FULL_VIEWBOX })
const currentViewBox = computed(() => `${viewBox.x} ${viewBox.y} ${viewBox.w} ${viewBox.h}`)
const isZoomed = computed(() => !!props.selected)

function targetForCounty(code: string) {
  const b = (countyBBoxes as Record<string, { x: number; y: number; w: number; h: number }>)[code]
  if (!b) return { ...FULL_VIEWBOX }
  const cx = b.x + b.w / 2
  const cy = b.y + b.h / 2
  let w = b.w * PAD
  let h = b.h * PAD
  if (w / h > ASPECT) h = w / ASPECT
  else w = h * ASPECT
  return { x: cx - w / 2, y: cy - h / 2, w, h }
}

let rafId: number | null = null
function easeInOutCubic(t: number) {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2
}

function prefersReducedMotion() {
  return import.meta.client && window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

function animateTo(target: { x: number; y: number; w: number; h: number }, duration = 500) {
  if (rafId !== null) cancelAnimationFrame(rafId)
  if (prefersReducedMotion()) {
    Object.assign(viewBox, target)
    return
  }
  const from = { ...viewBox }
  const start = performance.now()
  const step = (now: number) => {
    const t = Math.min(1, (now - start) / duration)
    const e = easeInOutCubic(t)
    viewBox.x = from.x + (target.x - from.x) * e
    viewBox.y = from.y + (target.y - from.y) * e
    viewBox.w = from.w + (target.w - from.w) * e
    viewBox.h = from.h + (target.h - from.h) * e
    if (t < 1) rafId = requestAnimationFrame(step)
    else rafId = null
  }
  rafId = requestAnimationFrame(step)
}

watch(() => props.selected, (code) => {
  tooltip.visible = false
  if (code) {
    animateTo(targetForCounty(code))
    void ensureLocalityData()
  } else {
    animateTo(FULL_VIEWBOX)
  }
}, { immediate: false })

onBeforeUnmount(() => {
  if (rafId !== null) cancelAnimationFrame(rafId)
  if (import.meta.client) window.removeEventListener('keydown', onKeyDown)
})

function onKeyDown(e: KeyboardEvent) {
  if (e.key === 'Escape' && props.selected) emit('clear')
}

onMounted(() => {
  window.addEventListener('keydown', onKeyDown)
})

// ── Locality dots (lazy-loaded) ──────────────────────────────────────────────

const localityData = shallowRef<Record<string, Locality[]> | null>(null)

async function ensureLocalityData() {
  if (localityData.value) return
  const mod = await import('~/assets/data/locality-coords.json')
  localityData.value = mod.default as Record<string, Locality[]>
}

// Display rule: show ONLY the localities returned by the stats endpoint for
// the selected county (campaigns in `oferta`, registrations in `cerere`). No
// county seat, no population backfill — just the data-bearing localities we
// have coordinates for. Names are always shown above the pin (see template).
// A stats locality missing from the coordinate dataset is dropped from the map
// (it still appears in the side list); with the full API-backed dataset this
// should be vanishingly rare.
function normalizeLocalityName(s: string): string {
  return s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim()
}

const localitiesForCounty = computed<Locality[]>(() => {
  if (!props.selected || !localityData.value || !props.priorityLocalities.length) return []
  const all = localityData.value[props.selected] ?? []
  if (!all.length) return []

  const byNorm = new Map(all.map(l => [normalizeLocalityName(l.n), l]))
  const seen = new Set<string>()
  const out: Locality[] = []
  for (const name of props.priorityLocalities) {
    const l = byNorm.get(normalizeLocalityName(name))
    if (l && !seen.has(l.n)) {
      seen.add(l.n)
      out.push(l)
    }
  }
  return out
})

// Scale dot/label size with viewBox so on-screen size stays roughly constant
const zoomScale = computed(() => viewBox.w / FULL_VIEWBOX.w)

function dotRadius(tier: 1 | 2) {
  const base = tier === 1 ? 8 : 6
  return base * zoomScale.value
}

const labelFontSize = computed(() => 14 * zoomScale.value)
const labelOffset = computed(() => 5 * zoomScale.value)

// Active label state — visible on dot hover or via external highlight prop
const hoveredLocality = ref<string | null>(null)
const activeLocalityName = computed(() => hoveredLocality.value || props.highlightedLocality || null)

function isLocalityActive(name: string): boolean {
  const target = activeLocalityName.value
  if (!target) return false
  return normalizeLocalityName(name) === normalizeLocalityName(target)
}

// When a locality is pinned (clicked in the side list), fade every other one so
// the pinned locality stands out. Cleared when the pin is toggled off.
const pinnedNorm = computed(() =>
  props.pinnedLocality ? normalizeLocalityName(props.pinnedLocality) : null,
)
function isLocalityDimmed(name: string): boolean {
  return !!pinnedNorm.value && normalizeLocalityName(name) !== pinnedNorm.value
}

// Paint order = SVG z-order. Render the active locality (hovered or clicked in
// the side panel) LAST so its dot + label sit on top of any overlapping ones.
const orderedLocalities = computed<Locality[]>(() => {
  const list = localitiesForCounty.value
  const target = activeLocalityName.value
  if (!target) return list
  const t = normalizeLocalityName(target)
  const rest: Locality[] = []
  const active: Locality[] = []
  for (const l of list) (normalizeLocalityName(l.n) === t ? active : rest).push(l)
  return [...rest, ...active]
})

// ── Interactions ─────────────────────────────────────────────────────────────

function onCountyClick(code: string) {
  // Click an already-selected county or a faded one while zoomed → clear
  if (isZoomed.value && code === props.selected) {
    emit('clear')
    return
  }
  emit('select', code)
}

// ── Tooltip ──────────────────────────────────────────────────────────────────

const tooltip = reactive({ visible: false, x: 0, y: 0, text: '' })

function onEnter(e: MouseEvent, code: string, name: string) {
  // In zoom view, suppress all county tooltips — the side panel already shows
  // the data for the selected county, and the faded ones aren't interactive.
  if (isZoomed.value) return
  const val = props.metric[code] ?? 0
  tooltip.text = `${name} — ${val} ${props.unit}`
  tooltip.visible = true
  positionTooltip(e)
  emit('hover', code)
}

function onMove(e: MouseEvent) {
  if (tooltip.visible) positionTooltip(e)
}

function positionTooltip(e: MouseEvent) {
  const wrapper = (e.currentTarget as HTMLElement | null)?.closest('.map-wrapper') as HTMLElement | null
  if (!wrapper) return
  const rect = wrapper.getBoundingClientRect()
  tooltip.x = e.clientX - rect.left + 14
  tooltip.y = e.clientY - rect.top - 32
}

function onWrapperMouseLeave() {
  tooltip.visible = false
  emit('hover', null)
}
</script>

<style scoped>
.map-wrapper {
  position: relative;
  width: 100%;
}

.map-svg {
  width: 100%;
  height: auto;
  display: block;
}

.county {
  fill: var(--fill, var(--map-none));
  stroke: var(--color-bg);
  stroke-width: 0.6;
  cursor: pointer;
  transition: fill 120ms ease, filter 120ms ease, opacity 350ms ease;
  outline: none;
}

/* Subtle hover — darken the existing shade slightly. No dark-blue fill override. */
.county:not(.is-selected):hover {
  filter: brightness(0.9);
}

.county.is-selected {
  stroke: var(--color-accent);
  stroke-width: 1.4;
  cursor: default;
}

.county:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 1px;
}

/* When the map is zoomed into a county, fade everything else out */
.county.is-faded {
  opacity: 0.12;
  pointer-events: none;
}

.county.is-faded:hover {
  fill: var(--fill, var(--map-q0)) !important;
  opacity: 0.12;
}

.map-tooltip {
  position: absolute;
  pointer-events: none;
  background: var(--color-primary);
  color: var(--color-text-light);
  font-size: var(--font-size-sm);
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  white-space: nowrap;
  z-index: 10;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.map-back-btn {
  position: absolute;
  top: var(--space-sm);
  left: var(--space-sm);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--color-bg);
  color: var(--color-text);
  border: 1px solid var(--color-border, rgba(0, 0, 0, 0.1));
  font-family: var(--font-body);
  font-size: var(--font-size-sm);
  font-weight: 600;
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  z-index: 5;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  transition: background 0.15s, transform 0.15s;
}

.map-back-btn:hover {
  background: var(--color-bg-muted);
  transform: translateX(-1px);
}

.map-back-btn:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* ── Locality dots ── */
.locality-dot {
  fill: var(--color-accent, #f59e0b);
  stroke: var(--color-bg, #ffffff);
  stroke-width: 1.2;
  opacity: 0;
  cursor: pointer;
  animation: locality-fade-in 260ms ease-out forwards;
  animation-delay: calc(280ms + var(--i, 0) * 6ms);
  transition: stroke-width 0.15s ease, opacity 0.2s ease;
}

.locality-dot--t1 {
  fill: var(--color-primary);
}

.locality-dot.is-active {
  stroke-width: 2.4;
}

/* Pinned-locality mode: fade everything except the pinned one.
   `!important` is needed to override the fade-in animation's held opacity. */
.locality-dot.is-dimmed {
  opacity: 0.22 !important;
}

@keyframes locality-fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

.locality-label {
  fill: var(--color-text, #1f2937);
  font-family: var(--font-body);
  font-weight: 600;
  paint-order: stroke;
  stroke: var(--color-bg, #ffffff);
  stroke-width: 3px;
  stroke-linejoin: round;
  pointer-events: none;
  transition: opacity 0.2s ease;
}

.locality-label--t2 {
  font-weight: 500;
  fill: var(--color-text-muted, #4b5563);
}

/* Clicked/hovered locality — emphasised and (via paint order) on top. */
.locality-label.is-active {
  fill: var(--color-primary);
  font-weight: 700;
}

/* Pinned-locality mode: fade the non-pinned labels. */
.locality-label.is-dimmed {
  opacity: 0.22;
}

@media (prefers-reduced-motion: reduce) {
  .locality-dot,
  .locality-label {
    animation-duration: 0ms;
    animation-delay: 0ms;
  }
}
</style>

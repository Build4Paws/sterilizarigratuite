<template>
  <div class="map-wrapper" @mouseleave="onWrapperMouseLeave">
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 613 433"
      class="map-svg"
      aria-label="Harta județelor din România"
    >
      <path
        v-for="county in COUNTY_PATHS"
        :key="county.code"
        :id="`RO-${county.code}`"
        :data-code="county.code"
        :class="['county', { 'is-selected': county.code === selected }]"
        :style="{ '--fill': fillFor(county.code) }"
        :aria-label="`${county.name} — ${props.metric[county.code] ?? 0} ${props.unit}`"
        tabindex="0"
        role="button"
        :d="county.d"
        @mouseenter="onEnter($event, county.code, county.name)"
        @mousemove="onMove"
        @click="emit('select', county.code)"
        @keydown.enter.prevent="emit('select', county.code)"
        @keydown.space.prevent="emit('select', county.code)"
      />
    </svg>

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
import { COUNTY_PATHS } from '~/assets/maps/counties'

const props = withDefaults(defineProps<{
  metric: Record<string, number>
  unit: string
  selected?: string
  scale?: 'quintile' | 'linear'
}>(), {
  selected: undefined,
  scale: 'quintile',
})

const emit = defineEmits<{
  hover: [code: string | null]
  select: [code: string]
}>()

// ── Color scale ──────────────────────────────────────────────────────────────

const FILLS = ['var(--map-q1)', 'var(--map-q2)', 'var(--map-q3)', 'var(--map-q4)', 'var(--map-q5)']

const bins = computed<number[]>(() => {
  const vals = Object.values(props.metric).filter(v => v > 0)
  if (!vals.length) return [1, 2, 3, 4]
  if (props.scale === 'linear') {
    const max = Math.max(...vals)
    return [max * 0.2, max * 0.4, max * 0.6, max * 0.8]
  }
  const sorted = [...vals].sort((a, b) => a - b)
  const n = sorted.length
  return [
    sorted[Math.floor(n * 0.2)] ?? 0,
    sorted[Math.floor(n * 0.4)] ?? 0,
    sorted[Math.floor(n * 0.6)] ?? 0,
    sorted[Math.floor(n * 0.8)] ?? 0,
  ]
})

function fillFor(code: string): string {
  const val = props.metric[code] ?? 0
  if (!val) return 'var(--map-q0)'
  const b = bins.value
  if (val <= (b[0] ?? 0)) return FILLS[0]!
  if (val <= (b[1] ?? 0)) return FILLS[1]!
  if (val <= (b[2] ?? 0)) return FILLS[2]!
  if (val <= (b[3] ?? 0)) return FILLS[3]!
  return FILLS[4]!
}

// ── Tooltip ──────────────────────────────────────────────────────────────────

const tooltip = reactive({ visible: false, x: 0, y: 0, text: '' })

function getWrapper(el: EventTarget | null): HTMLElement | null {
  return (el as HTMLElement | null)?.closest('.map-wrapper') as HTMLElement | null
}

function onEnter(e: MouseEvent, code: string, name: string) {
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
  const wrapper = getWrapper(e.currentTarget)
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
  fill: var(--fill, var(--map-q0));
  stroke: var(--color-bg);
  stroke-width: 0.6;
  cursor: pointer;
  transition: fill 120ms ease;
  outline: none;
}

.county:hover {
  opacity: 0.85;
  fill: var(--color-accent) !important;
}

.county.is-selected {
  fill: var(--color-accent) !important;
  stroke: var(--color-primary);
  stroke-width: 1.2;
}

.county:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 1px;
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
</style>

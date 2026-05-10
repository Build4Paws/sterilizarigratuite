<template>
  <div class="map-legend" aria-label="Legendă hartă">
    <span class="map-legend__label">puțină cerere</span>

    <div class="map-legend__swatches">
      <div
        v-for="step in steps"
        :key="step.token"
        class="map-legend__swatch-wrap"
      >
        <div
          class="map-legend__swatch"
          :style="{ background: `var(${step.token})` }"
        />
        <span class="map-legend__threshold">{{ step.label }}</span>
      </div>
    </div>

    <span class="map-legend__label">multă cerere</span>

    <div class="map-legend__none">
      <div class="map-legend__swatch map-legend__swatch--small" style="background:var(--map-none)" />
      <span>Fără date</span>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  /** raw metric values to compute cut-points from */
  metric: Record<string, number>
  /** unit string appended to threshold labels, e.g. "înscrieri" */
  unit?: string
}>()

/** Three percentile cut-points: [p20, p50, p80] */
const cutPoints = computed<[number, number, number]>(() => {
  const vals = Object.values(props.metric).filter(v => v > 0).sort((a, b) => a - b)
  if (!vals.length) return [0, 0, 0]
  const p = (pct: number) => vals[Math.max(0, Math.ceil(vals.length * pct) - 1)] ?? 0
  return [p(0.2), p(0.5), p(0.8)]
})

const steps = computed(() => {
  const [p20, p50, p80] = cutPoints.value
  const u = props.unit ? ` ${props.unit}` : ''
  const hasData = p20 > 0 || p50 > 0 || p80 > 0
  return [
    { token: '--map-low',      label: hasData ? `≤ ${p20}${u}` : '' },
    { token: '--map-mid-low',  label: hasData ? `≤ ${p50}${u}` : '' },
    { token: '--map-mid-high', label: hasData ? `≤ ${p80}${u}` : '' },
    { token: '--map-high',     label: hasData ? `> ${p80}${u}` : '' },
  ]
})
</script>

<style scoped>
.map-legend {
  display: flex;
  align-items: flex-start;
  gap: var(--space-sm);
  flex-wrap: wrap;
  margin-top: var(--space-sm);
  padding: var(--space-xs) var(--space-sm);
  background: rgba(255,255,255,0.7);
  border-radius: var(--radius-sm);
  width: fit-content;
}

.map-legend__label {
  font-size: 0.7rem;
  color: var(--color-text-muted);
  white-space: nowrap;
  align-self: center;
}

.map-legend__swatches {
  display: flex;
  gap: 3px;
  align-items: flex-start;
}

.map-legend__swatch-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.map-legend__swatch {
  width: 32px;
  height: 14px;
  border-radius: 3px;
  border: 1px solid rgba(0,0,0,0.08);
}

.map-legend__swatch--small {
  width: 14px;
  height: 14px;
}

.map-legend__threshold {
  font-size: 0.62rem;
  color: var(--color-text-muted);
  white-space: nowrap;
  text-align: center;
}

.map-legend__none {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: var(--space-xs);
  padding-left: var(--space-sm);
  border-left: 1px solid var(--color-border-light);
  font-size: 0.7rem;
  color: var(--color-text-muted);
}
</style>

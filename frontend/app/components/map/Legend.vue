<template>
  <div class="map-legend" aria-label="Legendă hartă">

    <div class="map-legend__scale">
      <span class="map-legend__edge-label">puțină</span>

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
          <span class="map-legend__pct">{{ step.pct }}</span>
        </div>
      </div>

      <span class="map-legend__edge-label">multă</span>
    </div>

    <div class="map-legend__divider" aria-hidden="true" />

    <div class="map-legend__none">
      <div class="map-legend__swatch map-legend__swatch--small" style="background:var(--map-none)" />
      <span>Fără date</span>
    </div>

  </div>
</template>

<script setup lang="ts">
defineProps<{
  metric: Record<string, number>
  unit?: string
}>()

const steps = [
  { token: '--map-low',      pct: 'jos 20%'   },
  { token: '--map-mid-low',  pct: '20–50%'    },
  { token: '--map-mid-high', pct: '50–80%'    },
  { token: '--map-high',     pct: 'top 20%'   },
]
</script>

<style scoped>
.map-legend {
  display: flex;
  align-items: center;
  gap: var(--space-lg);
  margin-top: var(--space-2xl);
  padding: var(--space-sm) var(--space-md);
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  width: fit-content;
}

/* ── Scale group ── */
.map-legend__scale {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.map-legend__edge-label {
  font-size: 0.72rem;
  color: var(--color-text-muted);
  white-space: nowrap;
}

.map-legend__swatches {
  display: flex;
  gap: var(--space-xs);
  align-items: flex-start;
}

.map-legend__swatch-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.map-legend__swatch {
  width: 36px;
  height: 16px;
  border-radius: 4px;
  border: 1px solid rgba(0, 0, 0, 0.07);
}

.map-legend__swatch--small {
  width: 16px;
  height: 16px;
}

.map-legend__pct {
  font-size: 0.6rem;
  color: var(--color-text-muted);
  white-space: nowrap;
  text-align: center;
  line-height: 1.2;
}

/* ── Divider ── */
.map-legend__divider {
  width: 1px;
  height: 36px;
  background: var(--color-border);
  flex-shrink: 0;
}

/* ── No-data pill ── */
.map-legend__none {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: 0.72rem;
  color: var(--color-text-muted);
  white-space: nowrap;
}
</style>

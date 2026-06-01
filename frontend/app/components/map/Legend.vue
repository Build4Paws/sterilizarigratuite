<template>
  <div class="map-legend" aria-label="Legendă hartă">

    <!-- Ofertă: binary — grey (no campaigns) vs dark blue (has campaigns) -->
    <template v-if="view === 'oferta'">
      <div class="map-legend__none">
        <div class="map-legend__swatch map-legend__swatch--small" style="background:var(--map-none)" />
        <span>Fără campanii</span>
      </div>
      <div class="map-legend__none">
        <div class="map-legend__swatch map-legend__swatch--small" style="background:var(--map-offer-has)" />
        <span>Campanii active</span>
      </div>
    </template>

    <!-- Cerere: graduated blue scale (puțină → multă) -->
    <template v-else>
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
    </template>

  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  view?: 'cerere' | 'oferta' | 'istoric'
}>(), {
  view: 'cerere',
})

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
  flex-wrap: wrap;
  gap: var(--space-sm) var(--space-lg);
  margin-top: var(--space-2xl);
  padding: var(--space-sm) var(--space-md);
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  width: fit-content;
  max-width: 100%;
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

/* ── Mobile: drop the "puțină/multă" edge labels and the divider ── */
@media (max-width: 768px) {
  .map-legend__edge-label,
  .map-legend__divider {
    display: none;
  }
}
</style>

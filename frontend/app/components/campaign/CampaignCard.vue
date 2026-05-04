<template>
  <article :class="['campaign-card', `campaign-card--${variant}`]">
    <header class="campaign-card__head">
      <div class="campaign-card__location">
        <h3 class="campaign-card__locality">{{ campaign.locality }}</h3>
        <span class="campaign-card__county">{{ campaign.countyName }}</span>
      </div>
      <span v-if="badge" :class="['campaign-card__badge', `campaign-card__badge--${badge.tone}`]">
        {{ badge.label }}
      </span>
    </header>

    <div class="campaign-card__org-row">
      <Building2 :size="15" class="campaign-card__icon" aria-hidden="true" />
      <span class="campaign-card__row-label">Organizator:</span>
      <span class="campaign-card__org">{{ campaign.organizationName }}</span>
    </div>

    <ul class="campaign-card__meta">
      <li class="campaign-card__meta-row">
        <Calendar :size="15" class="campaign-card__icon" aria-hidden="true" />
        <span class="campaign-card__row-label">Data:</span>
        <span>{{ dateLabel }}</span>
      </li>
      <li class="campaign-card__meta-row">
        <Clock :size="15" class="campaign-card__icon" aria-hidden="true" />
        <span class="campaign-card__row-label">Ora de start:</span>
        <span>{{ campaign.timeStart }}</span>
      </li>
      <li class="campaign-card__meta-row">
        <Clock :size="15" class="campaign-card__icon" aria-hidden="true" />
        <span class="campaign-card__row-label">Ora de încheiere:</span>
        <span>{{ campaign.timeEnd }}</span>
      </li>
      <li class="campaign-card__meta-row campaign-card__meta-row--top">
        <MapPin :size="15" class="campaign-card__icon" aria-hidden="true" />
        <span class="campaign-card__row-label">Adresă:</span>
        <span class="campaign-card__address">{{ campaign.address }}</span>
      </li>
    </ul>

    <ul class="campaign-card__slots">
      <li v-if="campaign.species.includes('dog') && campaign.slotsDogs" class="campaign-card__slot">
        <Dog :size="16" class="campaign-card__slot-icon" aria-hidden="true" />
        <span class="campaign-card__row-label">Locuri câini:</span>
        <span>{{ campaign.slotsDogs }}</span>
      </li>
      <li v-if="campaign.species.includes('cat') && campaign.slotsCats" class="campaign-card__slot">
        <Cat :size="16" class="campaign-card__slot-icon" aria-hidden="true" />
        <span class="campaign-card__row-label">Locuri pisici:</span>
        <span>{{ campaign.slotsCats }}</span>
      </li>
    </ul>

    <footer class="campaign-card__foot">
      <div v-if="campaign.doctor" class="campaign-card__foot-row">
        <Stethoscope :size="15" class="campaign-card__icon" aria-hidden="true" />
        <span class="campaign-card__row-label">Medic veterinar:</span>
        <span>{{ campaign.doctor }}</span>
      </div>
      <div class="campaign-card__foot-row">
        <Phone :size="15" class="campaign-card__icon" aria-hidden="true" />
        <span class="campaign-card__row-label">Telefon:</span>
        <a :href="`tel:${campaign.phonePublic}`" class="campaign-card__phone">
          {{ campaign.phonePublic }}
        </a>
      </div>
    </footer>
  </article>
</template>

<script setup lang="ts">
import { Calendar, Clock, MapPin, Phone, Stethoscope, Dog, Cat, Building2 } from 'lucide-vue-next'
import type { CampaignCardData, CampaignStatus } from '~/types'

const props = withDefaults(defineProps<{
  campaign: CampaignCardData
  variant?: 'default' | 'pending'
}>(), {
  variant: 'default',
})

const badge = computed<{ label: string; tone: 'neutral' | 'warning' | 'muted' } | null>(() => {
  // Pending variant always shows the pending badge regardless of status payload.
  if (props.variant === 'pending') {
    return { label: 'În așteptarea aprobării', tone: 'neutral' }
  }
  const status: CampaignStatus | undefined = props.campaign.status
  if (!status || status === 'approved') return null
  if (status === 'soldout') return { label: 'Locuri epuizate', tone: 'warning' }
  if (status === 'completed') return { label: 'Finalizat', tone: 'muted' }
  return { label: 'În așteptare', tone: 'neutral' }
})

const dateLabel = computed(() => {
  const start = formatDateRO(props.campaign.dateStart)
  if (!props.campaign.dateEnd || props.campaign.dateEnd === props.campaign.dateStart) {
    return start
  }
  return `${start} – ${formatDateRO(props.campaign.dateEnd)}`
})

// Parse YYYY-MM-DD as a local date; `new Date(iso)` would treat it as UTC and
// could shift the displayed day depending on the user's timezone.
function formatDateRO(iso: string): string {
  const parts = iso.split('-').map(Number)
  if (parts.length !== 3 || parts.some(Number.isNaN)) return iso
  const [y, m, d] = parts as [number, number, number]
  const date = new Date(y, m - 1, d)
  return new Intl.DateTimeFormat('ro-RO', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(date)
}

</script>

<style scoped>
.campaign-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  padding: var(--space-lg);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  text-align: left;
}

.campaign-card--pending {
  border-top: 3px solid var(--color-accent);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08), 0 1px 4px rgba(0, 0, 0, 0.04);
}

/* ---- Header ---- */
.campaign-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-sm);
}

.campaign-card__location {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.campaign-card__locality {
  font-family: var(--font-heading);
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--color-primary);
  margin: 0;
}

.campaign-card__county {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

/* ---- Badge ---- */
.campaign-card__badge {
  font-size: var(--font-size-sm);
  font-weight: 600;
  padding: 0.25rem 0.625rem;
  border-radius: 999px;
  white-space: nowrap;
}

.campaign-card__badge--neutral {
  background: rgba(4, 26, 73, 0.08);
  color: var(--color-primary);
}

.campaign-card__badge--warning {
  background: #fef3c7;
  color: #92400e;
}

.campaign-card__badge--muted {
  background: #f1f5f9;
  color: #64748b;
}

/* ---- Shared row layout ---- */
.campaign-card__org-row,
.campaign-card__meta-row,
.campaign-card__foot-row {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: var(--font-size-base);
  color: var(--color-text);
}

.campaign-card__meta-row--top {
  align-items: flex-start;
}

.campaign-card__icon {
  color: var(--color-text-muted);
  flex-shrink: 0;
}

/* Small muted label before each value */
.campaign-card__row-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  white-space: nowrap;
  flex-shrink: 0;
  margin-right: 2px;
}

/* ---- Organizer row ---- */
.campaign-card__org {
  font-weight: 500;
  color: var(--color-text);
}

/* ---- Meta list ---- */
.campaign-card__meta {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.campaign-card__address {
  line-height: 1.4;
}

/* ---- Slot chips ---- */
.campaign-card__slots {
  list-style: none;
  padding: var(--space-sm) 0 0;
  margin: 0;
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  border-top: 1px solid var(--color-border-light, #e2e8f0);
}

.campaign-card__slot {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-text);
  background: rgba(249, 89, 5, 0.07);
  border: 1px solid rgba(249, 89, 5, 0.18);
  border-radius: 999px;
  padding: 0.25rem 0.75rem;
}

.campaign-card__slot-icon {
  color: var(--color-accent, #f95905);
  flex-shrink: 0;
}

/* ---- Footer ---- */
.campaign-card__foot {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  padding-top: var(--space-sm);
  border-top: 1px solid var(--color-border-light, #e2e8f0);
}

.campaign-card__phone {
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 500;
}

.campaign-card__phone:hover {
  text-decoration: underline;
}
</style>

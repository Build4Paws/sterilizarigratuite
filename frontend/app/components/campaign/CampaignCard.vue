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

    <p class="campaign-card__org">{{ campaign.organizationName }}</p>

    <ul class="campaign-card__meta">
      <li class="campaign-card__meta-row">
        <Calendar :size="16" class="campaign-card__icon" />
        <span>{{ dateLabel }}</span>
      </li>
      <li class="campaign-card__meta-row">
        <Clock :size="16" class="campaign-card__icon" />
        <span>{{ campaign.timeStart }} – {{ campaign.timeEnd }}</span>
      </li>
      <li class="campaign-card__meta-row">
        <MapPin :size="16" class="campaign-card__icon" />
        <span class="campaign-card__address">{{ campaign.address }}</span>
      </li>
    </ul>

    <ul class="campaign-card__slots">
      <li v-if="campaign.species.includes('dog') && campaign.slotsDogs" class="campaign-card__slot">
        <Dog :size="18" class="campaign-card__slot-icon" />
        <span>{{ dogLabel(campaign.slotsDogs) }}</span>
      </li>
      <li v-if="campaign.species.includes('cat') && campaign.slotsCats" class="campaign-card__slot">
        <Cat :size="18" class="campaign-card__slot-icon" />
        <span>{{ catLabel(campaign.slotsCats) }}</span>
      </li>
    </ul>

    <footer class="campaign-card__foot">
      <div v-if="campaign.doctor" class="campaign-card__foot-row">
        <Stethoscope :size="16" class="campaign-card__icon" />
        <span>{{ campaign.doctor }}</span>
      </div>
      <div class="campaign-card__foot-row">
        <Phone :size="16" class="campaign-card__icon" />
        <a :href="`tel:${campaign.phonePublic}`" class="campaign-card__phone">
          {{ campaign.phonePublic }}
        </a>
      </div>
    </footer>
  </article>
</template>

<script setup lang="ts">
import { Calendar, Clock, MapPin, Phone, Stethoscope, Dog, Cat } from 'lucide-vue-next'
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

function dogLabel(n: number): string {
  return n === 1 ? '1 câine' : `${n} câini`
}
function catLabel(n: number): string {
  return n === 1 ? '1 pisică' : `${n} pisici`
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
  background: var(--color-bg-muted, #f8fafc);
  border-style: dashed;
}

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

.campaign-card__badge {
  font-size: var(--font-size-sm);
  font-weight: 600;
  padding: 0.25rem 0.625rem;
  border-radius: 999px;
  white-space: nowrap;
}

.campaign-card__badge--neutral {
  background: #e2e8f0;
  color: #334155;
}

.campaign-card__badge--warning {
  background: #fef3c7;
  color: #92400e;
}

.campaign-card__badge--muted {
  background: #f1f5f9;
  color: #64748b;
}

.campaign-card__org {
  font-size: var(--font-size-base);
  font-weight: 500;
  color: var(--color-text);
  margin: 0;
}

.campaign-card__meta,
.campaign-card__slots {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.campaign-card__slots {
  flex-direction: row;
  flex-wrap: wrap;
  gap: var(--space-md);
  padding-top: var(--space-sm);
  border-top: 1px solid var(--color-border-light, #e2e8f0);
}

.campaign-card__meta-row,
.campaign-card__slot {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: var(--font-size-base);
  color: var(--color-text);
}

.campaign-card__icon {
  color: var(--color-text-muted);
  flex-shrink: 0;
}

.campaign-card__slot-icon {
  color: var(--color-accent, #f95905);
  flex-shrink: 0;
}

.campaign-card__address {
  line-height: 1.4;
}

.campaign-card__foot {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  padding-top: var(--space-sm);
  border-top: 1px solid var(--color-border-light, #e2e8f0);
}

.campaign-card__foot-row {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: var(--font-size-base);
  color: var(--color-text);
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

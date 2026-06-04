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

    <div class="campaign-card__when">
      <Calendar :size="20" class="campaign-card__when-icon" aria-hidden="true" />
      <span class="campaign-card__when-text">
        {{ dateLabel }}, {{ campaign.timeStart }}–{{ campaign.timeEnd }}
      </span>
    </div>

    <div class="campaign-card__address-row">
      <MapPin :size="14" class="campaign-card__address-icon" aria-hidden="true" />
      <span class="campaign-card__address">{{ campaign.address }}</span>
    </div>

    <ul class="campaign-card__slots">
      <li
        v-if="campaign.species.includes('dog') && campaign.slotsDogs"
        class="campaign-card__slot campaign-card__slot--dog"
      >
        <Dog :size="32" class="campaign-card__slot-icon" aria-hidden="true" />
        <div class="campaign-card__slot-info">
          <span class="campaign-card__slot-count">{{ campaign.slotsDogs }}</span>
          <span class="campaign-card__slot-label">{{ Number(campaign.slotsDogs) === 1 ? 'loc câine' : 'locuri câini' }}</span>
        </div>
      </li>
      <li
        v-if="campaign.species.includes('cat') && campaign.slotsCats"
        class="campaign-card__slot campaign-card__slot--cat"
      >
        <Cat :size="32" class="campaign-card__slot-icon" aria-hidden="true" />
        <div class="campaign-card__slot-info">
          <span class="campaign-card__slot-count">{{ campaign.slotsCats }}</span>
          <span class="campaign-card__slot-label">{{ Number(campaign.slotsCats) === 1 ? 'loc pisică' : 'locuri pisici' }}</span>
        </div>
      </li>
    </ul>

    <footer v-if="campaign.doctor || campaign.phonePublic" class="campaign-card__foot">
      <div v-if="campaign.doctor" class="campaign-card__foot-row">
        <Stethoscope :size="15" class="campaign-card__icon" aria-hidden="true" />
        <span class="campaign-card__row-label">Medic veterinar:</span>
        <span>{{ campaign.doctor }}</span>
      </div>
      <div v-if="campaign.phonePublic" class="campaign-card__foot-row">
        <Phone :size="15" class="campaign-card__icon" aria-hidden="true" />
        <span class="campaign-card__row-label">Telefon:</span>
        <a :href="`tel:${campaign.phonePublic}`" class="campaign-card__phone">
          {{ campaign.phonePublic }}
        </a>
      </div>
    </footer>

    <a
      v-if="showCta"
      :href="`tel:${campaign.phonePublic}`"
      class="campaign-card__cta"
    >
      <Phone :size="18" aria-hidden="true" />
      <span>Sună organizatorul</span>
    </a>
  </article>
</template>

<script setup lang="ts">
import { Calendar, MapPin, Phone, Stethoscope, Dog, Cat, Building2 } from 'lucide-vue-next'
import type { CampaignCardData } from '~/types'

type BadgeTone = 'upcoming' | 'ongoing' | 'warning' | 'muted' | 'neutral'
interface Badge { label: string; tone: BadgeTone }

const props = withDefaults(defineProps<{
  campaign: CampaignCardData
  variant?: 'default' | 'pending'
  showCallCta?: boolean
}>(), {
  variant: 'default',
  showCallCta: false,
})

/** Today as YYYY-MM-DD in local time — safe for string comparison with API date fields. */
function localToday(): string {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

const badge = computed<Badge | null>(() => {
  // Organizer preview — fixed badge, no date logic.
  if (props.variant === 'pending') {
    return { label: 'În așteptarea aprobării', tone: 'neutral' }
  }

  const { status, dateStart, dateEnd, isSoldOut } = props.campaign

  // Sold-out overrides everything else.
  if (isSoldOut) return { label: 'Locuri epuizate', tone: 'warning' }

  const today = localToday()
  // For single-day campaigns dateEnd is omitted — treat end === start.
  const effectiveEnd = dateEnd || dateStart

  const isApproved = status?.toUpperCase() === 'APPROVED'

  if (!isApproved) return { label: 'În așteptare', tone: 'neutral' }

  // APPROVED + dateEnd already passed → closed.
  if (effectiveEnd < today) return { label: 'Finalizată', tone: 'muted' }

  // APPROVED + dateStart in the future → upcoming, confirmed.
  if (dateStart > today) return { label: 'Confirmată', tone: 'upcoming' }

  // APPROVED + dateStart <= today AND dateEnd >= today → happening now.
  return { label: 'În desfășurare', tone: 'ongoing' }
})

/** Only confirmed-upcoming campaigns make sense to call about. */
const showCta = computed(() =>
  props.showCallCta && ['ongoing', 'upcoming'].includes(badge.value?.tone || '') && !!props.campaign.phonePublic,
)

// `formatDateRange` (auto-imported from utils/format) renders Romanian
// dd/mm/yyyy and collapses single-day campaigns to one date.
const dateLabel = computed(() =>
  formatDateRange(props.campaign.dateStart, props.campaign.dateEnd ?? undefined),
)

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

/* Confirmată — upcoming, confirmed */
.campaign-card__badge--upcoming {
  background: #dbeafe;
  color: #1e40af;
}

/* În desfășurare — happening now */
.campaign-card__badge--ongoing {
  background: #d1fae5;
  color: #065f46;
}

/* Locuri epuizate — sold out */
.campaign-card__badge--warning {
  background: #fef3c7;
  color: #92400e;
}

/* Finalizată — past */
.campaign-card__badge--muted {
  background: #f1f5f9;
  color: #64748b;
}

/* În așteptare / În așteptarea aprobării — pending */
.campaign-card__badge--neutral {
  background: rgba(4, 26, 73, 0.07);
  color: var(--color-primary);
}

/* ---- Shared row layout ---- */
.campaign-card__org-row,
.campaign-card__foot-row {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: var(--font-size-base);
  color: var(--color-text);
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

/* ---- When (date + time) — primary "what's the deal" line ---- */
.campaign-card__when {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  background: rgba(4, 26, 73, 0.04);
  border-left: 3px solid var(--color-primary);
  border-radius: var(--radius-sm);
  padding: var(--space-sm) var(--space-md);
}

.campaign-card__when-icon {
  color: var(--color-primary);
  flex-shrink: 0;
}

.campaign-card__when-text {
  font-family: var(--font-heading);
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--color-primary);
  letter-spacing: -0.005em;
  line-height: 1.3;
}

/* ---- Address — secondary detail ---- */
.campaign-card__address-row {
  display: flex;
  align-items: flex-start;
  gap: var(--space-xs);
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  line-height: 1.4;
}

.campaign-card__address-icon {
  color: var(--color-text-muted);
  flex-shrink: 0;
  margin-top: 2px;
}

.campaign-card__address {
  line-height: 1.4;
}

/* ---- Slots — large color-coded blocks ---- */
.campaign-card__slots {
  list-style: none;
  padding: var(--space-sm) 0 0;
  margin: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: var(--space-sm);
  border-top: 1px solid var(--color-border-light, #e2e8f0);
}

.campaign-card__slot {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  border-radius: var(--radius-md);
  padding: var(--space-sm) var(--space-md);
  border: 1px solid transparent;
}

.campaign-card__slot--dog {
  background: rgba(249, 89, 5, 0.08);
  border-color: rgba(249, 89, 5, 0.18);
}

.campaign-card__slot--dog .campaign-card__slot-icon {
  color: var(--color-accent);
}

.campaign-card__slot--dog .campaign-card__slot-count {
  color: var(--color-accent);
}

.campaign-card__slot--cat {
  background: rgba(4, 26, 73, 0.06);
  border-color: rgba(4, 26, 73, 0.15);
}

.campaign-card__slot--cat .campaign-card__slot-icon {
  color: var(--color-primary);
}

.campaign-card__slot--cat .campaign-card__slot-count {
  color: var(--color-primary);
}

.campaign-card__slot-icon {
  flex-shrink: 0;
}

.campaign-card__slot-info {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
}

.campaign-card__slot-count {
  font-family: var(--font-heading);
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.campaign-card__slot-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  font-weight: 500;
  margin-top: 1px;
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

/* ---- Call CTA (listing page) ---- */
.campaign-card__cta {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  align-self: stretch;
  background: var(--color-accent);
  color: var(--color-text-light);
  font-family: var(--font-heading);
  font-weight: 600;
  font-size: var(--font-size-base);
  padding: var(--space-sm) var(--space-lg);
  border-radius: var(--radius-md);
  text-decoration: none;
  transition: background 0.2s, transform 0.1s;
  margin-top: var(--space-xs);
}

.campaign-card__cta:hover {
  background: var(--color-accent-hover);
  text-decoration: none;
}

.campaign-card__cta:active {
  transform: translateY(1px);
}
</style>

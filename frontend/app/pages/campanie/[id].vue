<template>
  <div class="container page-campanie">

    <!-- 404 / pending -->
    <div v-if="notFound" class="state-card state-card--pending">
      <Clock class="state-card__icon" :size="48" />
      <h1 class="state-card__title">Campanie în așteptare</h1>
      <p class="state-card__text">
        Campania cu ID-ul <code class="id-chip">{{ id }}</code> nu este încă aprobată sau nu există.
        Verifică din nou după ce primești emailul de confirmare a aprobării.
      </p>
    </div>

    <!-- Generic error -->
    <div v-else-if="fetchError" class="state-card state-card--error">
      <AlertCircle class="state-card__icon" :size="48" />
      <h1 class="state-card__title">Nu s-au putut încărca datele</h1>
      <p class="state-card__text">{{ errorMessage }}</p>
    </div>

    <!-- Campaign detail -->
    <div v-else-if="campaign" class="detail">

      <header class="detail__header">
        <div class="detail__header-icon">
          <CalendarCheck :size="32" />
        </div>
        <div class="detail__header-body">
          <h1 class="detail__org">{{ campaign.organizationName }}</h1>
          <p class="detail__locality">{{ campaign.locality }}, {{ campaign.countyName }}</p>
        </div>
      </header>

      <!-- Main fields table -->
      <section class="detail__card">
        <h2 class="detail__section-title">Detalii campanie</h2>
        <dl class="detail__table">

          <div class="detail__row">
            <dt>ID cerere</dt>
            <dd><code class="id-chip">{{ campaign.submissionId }}</code></dd>
          </div>

          <div class="detail__row">
            <dt>Organizație</dt>
            <dd>{{ campaign.organizationName }}</dd>
          </div>

          <div class="detail__row">
            <dt>Județ</dt>
            <dd>{{ campaign.countyName }} <span class="detail__code">({{ campaign.county }})</span></dd>
          </div>

          <div class="detail__row">
            <dt>Localitate</dt>
            <dd>{{ campaign.locality }}</dd>
          </div>

          <div class="detail__row">
            <dt>Adresă</dt>
            <dd>{{ campaign.address }}</dd>
          </div>

          <div class="detail__row">
            <dt>Data</dt>
            <dd>
              {{ formatDate(campaign.dateStart) }}
              <template v-if="campaign.dateEnd && campaign.dateEnd !== campaign.dateStart">
                – {{ formatDate(campaign.dateEnd) }}
              </template>
            </dd>
          </div>

          <div class="detail__row">
            <dt>Ore</dt>
            <dd>{{ campaign.timeStart }} – {{ campaign.timeEnd }}</dd>
          </div>

          <div v-if="campaign.doctor" class="detail__row">
            <dt>Medic</dt>
            <dd>{{ campaign.doctor }}</dd>
          </div>

          <div class="detail__row">
            <dt>Telefon public</dt>
            <dd><a :href="`tel:${campaign.phonePublic}`">{{ campaign.phonePublic }}</a></dd>
          </div>

        </dl>
      </section>

      <!-- Species & slots -->
      <section class="detail__card">
        <h2 class="detail__section-title">Specii și locuri disponibile</h2>
        <div class="species">
          <div v-if="campaign.species.dog !== undefined" class="species__item">
            <span class="species__emoji" aria-hidden="true">🐕</span>
            <div class="species__body">
              <span class="species__label">Câini</span>
              <span class="species__slots">{{ campaign.species.dog }} locuri</span>
            </div>
          </div>
          <div v-if="campaign.species.cat !== undefined" class="species__item">
            <span class="species__emoji" aria-hidden="true">🐱</span>
            <div class="species__body">
              <span class="species__label">Pisici</span>
              <span class="species__slots">{{ campaign.species.cat }} locuri</span>
            </div>
          </div>
        </div>
      </section>

    </div>
  </div>
</template>

<script setup lang="ts">
import { Clock, AlertCircle, CalendarCheck } from 'lucide-vue-next'
import type { PublicCampaign } from '~/types'

definePageMeta({ layout: 'default' })
useSeoMeta({ robots: 'noindex, nofollow', title: 'Detalii campanie — Sterilizări Gratuite' })

const route = useRoute()
const id = computed(() => String(route.params.id ?? ''))

const { data: campaign, error: fetchError } = await useAsyncData<PublicCampaign>(
  `campaign-${id.value}`,
  () => $fetch<PublicCampaign>(`/api/campaigns/${id.value}`),
)

const notFound = computed(() => {
  if (!fetchError.value) return false
  const status = (fetchError.value as { statusCode?: number }).statusCode
  return status === 404 || status === 400
})

const errorMessage = computed(() => extractApiError(fetchError.value))

// ---- Formatting -------------------------------------------------------

const DATE_FMT = new Intl.DateTimeFormat('ro-RO', {
  day: 'numeric',
  month: 'long',
  year: 'numeric',
})

function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  const parts = iso.split('-').map(Number)
  const y = parts[0] ?? 0
  const m = parts[1] ?? 1
  const d = parts[2] ?? 1
  return DATE_FMT.format(new Date(y, m - 1, d))
}
</script>

<style scoped>
.page-campanie {
  padding: var(--space-2xl) 0;
  max-width: 680px;
  margin: 0 auto;
}

/* ---- State cards (pending / error) ---- */
.state-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: var(--space-md);
  padding: var(--space-3xl) var(--space-xl);
  border-radius: var(--radius-lg);
  border: 1px dashed var(--color-border);
}

.state-card--pending { background: #fffbeb; border-color: #fbbf24; }
.state-card--error   { background: #fef2f2; border-color: var(--color-error); }

.state-card__icon {
  opacity: 0.7;
}

.state-card--pending .state-card__icon { color: #d97706; }
.state-card--error   .state-card__icon { color: var(--color-error); }

.state-card__title {
  font-family: var(--font-heading);
  font-size: var(--font-size-lg);
  color: var(--color-primary);
  margin: 0;
}

.state-card__text {
  color: var(--color-text-muted);
  margin: 0;
  line-height: 1.6;
  max-width: 480px;
}

/* ---- Detail layout ---- */
.detail {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.detail__header {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-lg) var(--space-xl);
  background: var(--color-primary);
  color: var(--color-text-light);
  border-radius: var(--radius-lg);
}

.detail__header-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #fff;
}

.detail__org {
  font-family: var(--font-heading);
  font-size: var(--font-size-lg);
  font-weight: 700;
  margin: 0;
  color: #fff;
}

.detail__locality {
  font-size: var(--font-size-base);
  color: rgba(255, 255, 255, 0.75);
  margin: 0;
}

/* ---- Card wrapper ---- */
.detail__card {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.detail__section-title {
  font-family: var(--font-heading);
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-primary);
  margin: 0;
  padding-bottom: var(--space-sm);
  border-bottom: 1px solid var(--color-border-light, #e2e8f0);
}

/* ---- Detail table (dl grid) ---- */
.detail__table {
  display: flex;
  flex-direction: column;
  gap: 0;
  margin: 0;
}

.detail__row {
  display: grid;
  grid-template-columns: 160px 1fr;
  gap: var(--space-sm);
  padding: var(--space-sm) 0;
  border-bottom: 1px solid var(--color-border-light, #e2e8f0);
  align-items: baseline;
}

.detail__row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.detail__table dt {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.detail__table dd {
  margin: 0;
  font-size: var(--font-size-base);
  color: var(--color-text);
  word-break: break-word;
}

.detail__table dd a {
  color: var(--color-primary);
  text-decoration: underline;
}

.detail__code {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

/* ---- ID chip ---- */
.id-chip {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.85em;
  background: var(--color-bg-muted, #f1f5f9);
  padding: 2px 7px;
  border-radius: 4px;
  color: var(--color-text);
  word-break: break-all;
}

/* ---- Species ---- */
.species {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.species__item {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  background: var(--color-bg-muted, #f8fafc);
  border-radius: var(--radius-md);
}

.species__emoji {
  font-size: 1.75rem;
  line-height: 1;
}

.species__body {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.species__label {
  font-family: var(--font-heading);
  font-weight: 600;
  font-size: var(--font-size-base);
  color: var(--color-primary);
}

.species__slots {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

/* ---- Responsive ---- */
@media (max-width: 480px) {
  .detail__row {
    grid-template-columns: 1fr;
    gap: 2px;
  }

  .detail__table dt {
    font-size: 0.7rem;
  }

  .detail__header {
    padding: var(--space-md);
  }
}
</style>

<template>
  <div class="container page-confirmare-campanie">
    <div v-if="session" class="confirmare">
      <header class="confirmare__header">
        <CircleCheck class="confirmare__icon" :size="48" />
        <h1 class="confirmare__title">Mulțumim, {{ session.campaign.organizationName }}!</h1>
        <p class="confirmare__lead">
          Am primit cererea ta de campanie. O verificăm în maxim
          <strong>24 de ore</strong> și revenim cu un email la
          <a :href="`mailto:${session.campaign.contactEmail}`">{{ session.campaign.contactEmail }}</a>.
        </p>
      </header>

      <section class="confirmare__block">
        <div class="confirmare__block-header">
          <Eye :size="20" />
          <h2>Așa va apărea campania ta după aprobare</h2>
        </div>
        <CampaignCard :campaign="cardData" :show-call-cta="true" />
      </section>

      <section v-if="hasStats" class="confirmare__block confirmare__block--stats">
        <div class="confirmare__block-header">
          <Users :size="20" />
          <h2>În zona ta</h2>
        </div>
        <p>
          <template v-for="(seg, i) in reachParts" :key="i">
            <strong v-if="seg.b">{{ seg.t }}</strong><template v-else>{{ seg.t }}</template>
          </template>
        </p>
        <p class="confirmare__followup">
          Imediat ce campania este aprobată, îi anunțăm prin SMS și email.
        </p>
      </section>

      <section class="confirmare__block confirmare__block--meta">
        <div class="confirmare__block-header">
          <ClipboardList :size="20" />
          <h2>Detalii cerere</h2>
        </div>
        <dl class="confirmare__meta">
          <div class="confirmare__meta-row">
            <dt>ID campanie</dt>
            <dd><code>{{ session.submissionId }}</code></dd>
          </div>
          <div class="confirmare__meta-row">
            <dt>Trimisă</dt>
            <dd>{{ submittedLabel }}</dd>
          </div>
          <div class="confirmare__meta-row">
            <dt>Status</dt>
            <dd><span class="status-pill">În așteptarea aprobării</span></dd>
          </div>
        </dl>

      </section>

      <footer class="confirmare__footer">
        <NuxtLink to="/" class="confirmare__home">← Înapoi la pagina principală</NuxtLink>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { CircleCheck, Users, Eye, ClipboardList } from 'lucide-vue-next'
import type { CampaignCardData } from '~/types'

definePageMeta({ layout: 'default' })
useSeoMeta({
  robots: 'noindex, nofollow',
  title: 'Cerere primită — Sterilizări Gratuite',
})

const router = useRouter()
const { session } = useOrganizerSubmission()

onMounted(() => {
  if (!session.value) router.replace('/organizatori')
})

const cardData = computed<CampaignCardData>(() => {
  const s = session.value!
  const c = s.campaign
  return {
    organizationName: c.organizationName,
    countyName: s.countyName,
    locality: c.locality,
    address: c.address,
    dateStart: c.dateStart,
    dateEnd: c.dateEnd,
    timeStart: c.timeStart,
    timeEnd: c.timeEnd,
    species: c.species,
    slotsDogs: c.slotsDogs,
    slotsCats: c.slotsCats,
    doctor: c.doctor,
    phonePublic: c.phonePublic,
  }
})

const hasStats = computed(() => {
  const stats = session.value?.stats
  return !!stats && (stats.registeredInLocality > 0 || stats.registeredInCounty > 0)
})

interface Seg { t: string; b?: true }

const reachParts = computed<Seg[]>(() => {
  const s = session.value
  if (!s?.stats) return []
  const inLocality = s.stats.registeredInLocality
  const inCounty = s.stats.registeredInCounty
  const locality = s.campaign.locality
  const county = s.countyName

  if (inLocality === 0 && inCounty > 0) {
    return [
      { t: 'În ' },
      { t: locality, b: true },
      { t: ' nu așteaptă încă nimeni o campanie, dar sunt ' },
      { t: `${inCounty} ${peopleWord(inCounty)}`, b: true },
      { t: ' înregistrate în județul ' },
      { t: county, b: true },
      { t: '.' },
    ]
  }
  if (inLocality === 1) {
    return [
      { t: '1 persoană', b: true },
      { t: ' din ' },
      { t: locality, b: true },
      { t: ' așteaptă o campanie de sterilizare. O vom anunța imediat ce campania ta este aprobată.' },
    ]
  }
  const extra = Math.max(inCounty - inLocality, 0)
  return [
    { t: `${inLocality} ${peopleWord(inLocality)}`, b: true },
    { t: ' din ' },
    { t: locality, b: true },
    { t: ' și încă ' },
    { t: String(extra), b: true },
    { t: ' din restul județului ' },
    { t: county, b: true },
    { t: ' așteaptă o campanie. Le anunțăm imediat ce campania ta este aprobată.' },
  ]
})

function peopleWord(n: number): string {
  return n === 1 ? 'persoană' : 'persoane'
}

const submittedLabel = computed(() => {
  const iso = session.value?.submittedAt
  if (!iso) return ''
  return new Intl.DateTimeFormat('ro-RO', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(iso))
})
</script>

<style scoped>
.page-confirmare-campanie {
  padding: var(--space-2xl) 0;
}

.confirmare {
  max-width: 720px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-xl);
}

.confirmare__header {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-sm);
}

.confirmare__icon {
  color: #10b981;
}

.confirmare__title {
  font-family: var(--font-heading);
  font-size: var(--font-size-xl);
  color: var(--color-primary);
  margin: 0;
}

.confirmare__lead {
  color: var(--color-text);
  font-size: var(--font-size-base);
  margin: 0;
  max-width: 560px;
  line-height: 1.5;
}

.confirmare__lead a {
  color: var(--color-primary);
  font-weight: 500;
}

.confirmare__block {
  background: var(--color-slate-50, #f8fafc);
  border-radius: var(--radius-md);
  padding: var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.confirmare__block--stats {
  background: #ecfdf5;
  color: #065f46;
}

.confirmare__block--stats :deep(strong) {
  color: inherit;
}

.confirmare__block--meta {
  background: var(--color-bg);
  border: 1px solid var(--color-border-light, #e2e8f0);
}

.confirmare__block-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.confirmare__block-header h2 {
  font-family: var(--font-heading);
  font-size: 1.05rem;
  margin: 0;
  font-weight: 600;
  color: inherit;
}

.confirmare__block p {
  margin: 0;
  line-height: 1.5;
}

.confirmare__followup {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.confirmare__block--stats .confirmare__followup {
  color: #047857;
}

.confirmare__meta {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin: 0;
}

.confirmare__meta-row {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: var(--space-sm);
  border-bottom: 1px dashed var(--color-border-light, #e2e8f0);
  padding-bottom: var(--space-sm);
}

.confirmare__meta-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.confirmare__meta dt {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  min-width: 120px;
}

.confirmare__meta dd {
  margin: 0;
  font-size: var(--font-size-base);
  color: var(--color-text);
}

.confirmare__meta code {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.95em;
  background: var(--color-bg-muted, #f1f5f9);
  padding: 2px 6px;
  border-radius: 4px;
}

.status-pill {
  display: inline-block;
  background: #fef3c7;
  color: #92400e;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.confirmare__footer {
  text-align: center;
  padding-top: var(--space-md);
}

.confirmare__home {
  color: var(--color-primary);
  text-decoration: underline;
  font-weight: 500;
}
</style>

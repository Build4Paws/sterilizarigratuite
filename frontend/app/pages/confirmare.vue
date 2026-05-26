<template>
  <div class="container page-confirmare">
    <div v-if="session" class="confirmare">
      <header class="confirmare__header">
        <CircleCheck class="confirmare__icon" :size="48" />
        <h1 class="confirmare__title">Ești înscris/ă, {{ firstName }}!</h1>
        <p class="confirmare__channel">{{ channelMessage }}</p>
      </header>

      <section class="confirmare__block">
        <div class="confirmare__block-header">
          <Users :size="20" />
          <h2>În zona ta</h2>
        </div>
        <p>
          <template v-for="(seg, i) in rankParts" :key="i">
            <strong v-if="seg.b">{{ seg.t }}</strong><template v-else>{{ seg.t }}</template>
          </template>
        </p>
        <p class="confirmare__followup">
          Când strângem suficiente persoane din zona ta, organizăm o campanie și te anunțăm.
        </p>
      </section>

      <section v-if="clinics.length" class="confirmare__block confirmare__block--clinics">
        <div class="confirmare__block-header">
          <MapPin :size="20" />
          <h2>Cabinete permanente în zona ta</h2>
        </div>
        <p class="confirmare__lead">
          Vești bune — există deja cabinete unde poți steriliza gratuit, fără să aștepți o campanie:
        </p>
        <ul class="clinics">
          <li v-for="c in clinics" :key="`${c.name}-${c.locality}`" class="clinics__item">
            <div class="clinics__name">{{ c.name }}</div>
            <div class="clinics__meta">
              {{ c.locality }}<span v-if="c.phone"> — <a :href="`tel:${c.phone}`">{{ c.phone }}</a></span>
            </div>
          </li>
        </ul>
      </section>

      <footer class="confirmare__footer">
        <p class="confirmare__footer-label">Între timp, poți:</p>
        <div class="link-cards">
          <UiLinkCard
            to="/campanii"
            :icon="PawPrint"
            title="Campanii active"
            desc="Vezi campaniile de sterilizare gratuită din toată țara"
          />
          <UiLinkCard
            to="/despre-sterilizare"
            :icon="Stethoscope"
            title="Despre sterilizare"
            desc="Ghid medical — tot ce trebuie să știi înainte și după procedură"
          />
          <UiLinkCard
            to="/harta"
            :icon="Map"
            title="Harta înregistrărilor"
            desc="Descoperă câți oameni din județul tău așteaptă o campanie"
          />
        </div>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { CircleCheck, Users, MapPin, PawPrint, Stethoscope, Map } from 'lucide-vue-next'
// PawPrint, Stethoscope, Map are passed as :icon props to UiLinkCard

definePageMeta({ layout: 'default' })
useSeoMeta({ robots: 'noindex, nofollow', title: 'Înscriere confirmată — Sterilizări Gratuite' })

const router = useRouter()
const { session } = useCitizenSession()

onMounted(() => {
  if (!session.value) router.replace('/')
})

const firstName = computed(() => session.value?.name.trim().split(/\s+/)[0] ?? '')

const channelMessage = computed(() => {
  const s = session.value
  if (!s) return ''
  switch (s.channel) {
    case 'sms':   return `Te anunțăm prin SMS la ${s.phone}.`
    case 'email': return `Te anunțăm prin email la ${s.email}.`
    case 'both':  return `Te anunțăm prin SMS la ${s.phone} și email la ${s.email}.`
  }
})

// Live fallback for when POST /register didn't return stats in its response.
// The GET endpoint counts include the current user, so no +1 adjustment needed.
const { localityCount: liveLocalityCount, countyCount: liveCountyCount } = useLocalityWaitingCount(
  () => session.value?.countyCode ?? '',
  () => session.value?.locality ?? '',
)

const FEMININE_ORDINALS: Record<number, string> = {
  1: 'prima',
  2: 'a doua',
  3: 'a treia',
  4: 'a patra',
  5: 'a cincea',
  6: 'a șasea',
  7: 'a șaptea',
  8: 'a opta',
  9: 'a noua',
  10: 'a zecea',
}

function feminineOrdinal(n: number): string {
  return FEMININE_ORDINALS[n] ?? `a ${n}-a`
}

interface Seg { t: string; b?: true }

const rankParts = computed<Seg[]>(() => {
  const s = session.value
  if (!s) return []

  let localityRank: number
  let countyRank: number

  if (s.stats) {
    // POST /register returns counts of OTHERS registered before this user → rank = count + 1.
    localityRank = s.stats.registeredInLocality + 1
    countyRank = s.stats.registeredInCounty + 1
  } else {
    // Fallback: live GET stats already include the current user → rank = count as-is.
    localityRank = liveLocalityCount.value || 1
    countyRank = liveCountyCount.value || 1
  }

  if (countyRank === 1) {
    return [
      { t: 'Ești ' },
      { t: 'prima persoană', b: true },
      { t: ' din județul ' },
      { t: s.countyName, b: true },
      { t: ' care s-a înscris.' },
    ]
  }
  if (localityRank > 5) {
    return [
      { t: 'Ești ' },
      { t: `${feminineOrdinal(localityRank)} persoană`, b: true },
      { t: ' din ' },
      { t: s.locality, b: true },
      { t: ' care s-a înscris.' },
    ]
  }
  if (localityRank === 1) {
    return [
      { t: 'Ești ' },
      { t: 'prima persoană', b: true },
      { t: ' din ' },
      { t: s.locality, b: true },
      { t: ' și printre primele ' },
      { t: String(countyRank), b: true },
      { t: ' din județul ' },
      { t: s.countyName, b: true },
      { t: ' care s-au înscris.' },
    ]
  }
  if (countyRank > localityRank) {
    return [
      { t: 'Ești ' },
      { t: `${feminineOrdinal(localityRank)} persoană`, b: true },
      { t: ' din ' },
      { t: s.locality, b: true },
      { t: ', și printre primele ' },
      { t: String(countyRank), b: true },
      { t: ' din județul ' },
      { t: s.countyName, b: true },
      { t: ' care s-au înscris.' },
    ]
  }
  return [
    { t: 'Ești ' },
    { t: `${feminineOrdinal(localityRank)} persoană`, b: true },
    { t: ' din ' },
    { t: s.locality, b: true },
    { t: ' și din județul ' },
    { t: s.countyName, b: true },
    { t: ' care s-au înscris.' },
  ]
})

const { clinics } = useClinics(
  session.value?.countyCode ?? '',
  session.value?.locality ?? '',
)
</script>

<style scoped>
.page-confirmare {
  padding: var(--space-2xl) 0;
}

.confirmare {
  max-width: 640px;
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

.confirmare__channel {
  color: var(--color-text-muted);
  font-size: var(--font-size-base);
  margin: 0;
}

.confirmare__block {
  background: var(--color-slate-50, #f8fafc);
  border-radius: var(--radius-md);
  padding: var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.confirmare__block--clinics {
  background: #ecfdf5;
  color: #065f46;
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

.confirmare__lead {
  margin-bottom: var(--space-xs);
}

.confirmare__followup {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.clinics {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.clinics__item {
  padding: var(--space-sm) 0;
  border-top: 1px solid rgba(6, 95, 70, 0.15);
}

.clinics__item:first-child {
  border-top: 0;
}

.clinics__name {
  font-weight: 600;
}

.clinics__meta {
  font-size: var(--font-size-sm);
  opacity: 0.85;
}

.clinics__meta a {
  color: inherit;
  text-decoration: underline;
}

.confirmare__footer {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
  padding-top: var(--space-sm);
}

.confirmare__footer-label {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  margin: 0;
  text-align: center;
}

.link-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-md);
}

@media (max-width: 768px) {
  .link-cards {
    grid-template-columns: 1fr;
  }
}

@media (min-width: 769px) and (max-width: 900px) {
  .link-cards {
    grid-template-columns: 1fr 1fr;
  }
}
</style>

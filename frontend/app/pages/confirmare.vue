<template>
  <div v-if="session" class="cf">
    <!-- Celebratory hero -->
    <header class="cf__hero">
      <div class="cf__glow" aria-hidden="true" />
      <div class="cf__badge" aria-hidden="true">
        <CircleCheck :size="44" :stroke-width="2.25" />
      </div>
      <p class="cf__eyebrow">Înscriere confirmată</p>
      <h1 class="cf__title">Gata, {{ firstName }}!</h1>
      <p class="cf__lead">De acum primești notificări despre campaniile gratuite din localitatea ta.</p>
      <p class="cf__channel">{{ channelMessage }}</p>
    </header>

    <div class="cf__divider" aria-hidden="true">
      <svg viewBox="0 0 1440 120" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M0,0 L0,60 Q360,120 720,80 Q1080,40 1440,90 L1440,0 Z" fill="var(--color-primary)" />
      </svg>
    </div>

    <div class="cf__body">
      <!-- Area stats -->
      <section class="card statcard">
        <span class="statcard__icon" aria-hidden="true"><Users :size="22" /></span>
        <div>
          <p class="card__eyebrow">În zona ta</p>
          <p class="statcard__text">
            <template v-for="(seg, i) in rankParts" :key="i">
              <strong v-if="seg.b">{{ seg.t }}</strong><template v-else>{{ seg.t }}</template>
            </template>
          </p>
          <p class="statcard__note">
            Dacă se strâng suficiente cereri din {{ session.locality }}, notificăm oficial primăria,
            care poate aloca fonduri pentru sterilizare gratuită (Legea 258/2013).
          </p>
        </div>
      </section>

      <!-- Access code keepsake -->
      <section v-if="session.manageToken" class="keycard">
        <div class="keycard__head">
          <span class="keycard__icon" aria-hidden="true"><KeyRound :size="22" /></span>
          <h2 class="keycard__title">Link-ul tău de acces</h2>
        </div>
        <p class="keycard__lead">
          Cu acest link îți gestionezi înscrierea oricând — te dezabonezi sau îți
          ștergi datele, fără cont și fără parolă. Salvează-l într-un loc sigur.
        </p>
        <div class="keycard__field">
          <a class="keycard__token" :href="manageUrl" target="_blank" rel="noopener">{{ manageUrl }}</a>
          <button type="button" class="keycard__copy" :class="{ 'is-copied': copied }" @click="copyToken">
            <component :is="copied ? Check : Copy" :size="18" aria-hidden="true" />
            <span>{{ copied ? 'Copiat' : 'Copiază' }}</span>
          </button>
        </div>
      </section>

      <!-- Permanent clinics (shown only when available) -->
      <section v-if="clinics.length" class="card clinics">
        <div class="clinics__head">
          <span class="clinics__icon" aria-hidden="true"><MapPin :size="22" /></span>
          <h2 class="clinics__title">Cabinete permanente în zona ta</h2>
        </div>
        <p class="clinics__lead">
          Vești bune. Există deja cabinete unde poți steriliza gratuit, fără să aștepți o campanie.
        </p>
        <ul class="clinics__list">
          <li v-for="c in clinics" :key="`${c.name}-${c.locality}`" class="clinics__item">
            <span class="clinics__name">{{ c.name }}</span>
            <span class="clinics__meta">
              {{ c.locality }}<template v-if="c.phone"> · <a :href="`tel:${c.phone}`">{{ c.phone }}</a></template>
            </span>
          </li>
        </ul>
      </section>

      <!-- Share / referral nudge -->
      <section class="card share-card">
        <p class="share-card__title">Fiecare înscriere contează!</p>
        <p class="share-card__text">
          Dacă mai ai vecini care vor să își sterilizeze gratuit animalele, spune-le să se înscrie.
        </p>
        <button type="button" class="share-card__btn" :class="{ 'is-copied': linkCopied }" @click="copyLink">
          <component :is="linkCopied ? Check : Share2" :size="18" aria-hidden="true" />
          <span>{{ linkCopied ? 'Link copiat' : 'Copiază linkul' }}</span>
        </button>
      </section>

      <!-- Next steps -->
      <section class="next">
        <h2 class="next__label">Între timp, poți vedea:</h2>
        <div class="next__grid">
          <NuxtLink
            v-for="(a, i) in actions"
            :key="a.to"
            :to="a.to"
            class="action"
            :style="{ '--i': i }"
          >
            <span class="action__icon" aria-hidden="true"><component :is="a.icon" :size="24" /></span>
            <span class="action__title">{{ a.title }}</span>
            <span class="action__desc">{{ a.desc }}</span>
            <span class="action__go" aria-hidden="true"><ArrowUpRight :size="20" /></span>
          </NuxtLink>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  CircleCheck, Users, MapPin, KeyRound, Copy, Check, ShieldCheck,
  PawPrint, Stethoscope, Map, ArrowUpRight, Share2,
} from 'lucide-vue-next'

definePageMeta({ layout: 'default' })
useSeoMeta({ robots: 'noindex, nofollow', title: 'Înscriere confirmată · Sterilizări Gratuite' })

const router = useRouter()
const { session } = useCitizenSession()
const toast = useToast()

onMounted(() => {
  if (!session.value) router.replace('/')
})

const firstName = computed(() => session.value?.name.trim().split(/\s+/)[0] ?? '')

// Show the stored +40XXXXXXXXX phone in the friendly national form (0740 123 456).
function formatPhone(phone?: string): string {
  if (!phone) return ''
  const d = phone.replace(/\D/g, '').replace(/^40/, '')
  if (d.length !== 9) return phone
  return `0${d.slice(0, 3)} ${d.slice(3, 6)} ${d.slice(6, 9)}`
}

const channelMessage = computed(() => {
  const s = session.value
  if (!s) return ''
  const tel = formatPhone(s.phone)
  switch (s.channel) {
    case 'sms':   return `Te anunțăm prin SMS la ${tel}.`
    case 'email': return `Te anunțăm prin email la ${s.email}.`
    case 'both':  return `Te anunțăm prin SMS la ${tel} și prin email la ${s.email}.`
  }
})

const actions = [
  { to: '/campanii', icon: PawPrint, title: 'Campanii active', desc: 'Vezi campaniile de sterilizare gratuită din toată țara.' },
  { to: '/ghid-sterilizare', icon: Stethoscope, title: 'Ghid de sterilizare', desc: 'Tot ce e bine să știi înainte și după procedură.' },
  { to: '/harta', icon: Map, title: 'Harta înscrierilor', desc: 'Vezi câți oameni din județul tău așteaptă o campanie.' },
]

// The "access code" is the citizen-manage token; surface it as the ready-to-use
// management link (/cont/{token}), not the raw token.
const requestUrl = useRequestURL()
const manageUrl = computed(() =>
  session.value?.manageToken ? `${requestUrl.origin}/cont/${session.value.manageToken}` : '')

const copied = ref(false)
async function copyToken() {
  if (!manageUrl.value) return
  try {
    await navigator.clipboard.writeText(manageUrl.value)
    copied.value = true
    toast.success('Link copiat. Salvează-l într-un loc sigur.')
    setTimeout(() => { copied.value = false }, 2500)
  } catch {
    toast.error('Nu am putut copia linkul. Selectează-l și copiază-l manual.')
  }
}

const linkCopied = ref(false)
async function copyLink() {
  const url = 'https://sterilizarigratuite.ro/'
  try {
    await navigator.clipboard.writeText(url)
    linkCopied.value = true
    toast.success('Link copiat. Trimite-l vecinilor tăi.')
    setTimeout(() => { linkCopied.value = false }, 2500)
  } catch {
    toast.error('Nu am putut copia linkul. Copiază-l manual din bara de adrese.')
  }
}

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
      { t: ' care va fi alertată.' },
    ]
  }
  if (localityRank > 5) {
    return [
      { t: 'Ești ' },
      { t: `${feminineOrdinal(localityRank)} persoană`, b: true },
      { t: ' din ' },
      { t: s.locality, b: true },
      { t: ' care va fi alertată.' },
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
      { t: ' care vor fi alertate.' },
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
      { t: ' care vor fi alertate.' },
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
.cf {
  background: var(--color-bg-muted);
}

/* ---------- Hero ---------- */
.cf__hero {
  position: relative;
  overflow: hidden;
  text-align: center;
  padding: var(--space-2xl) var(--space-md) calc(var(--space-3xl) + var(--space-md));
  background: var(--color-primary);
  color: var(--color-text-light);
}

.cf__glow {
  position: absolute;
  top: -30%;
  left: 50%;
  width: 520px;
  height: 520px;
  transform: translateX(-50%);
  background: radial-gradient(circle, rgba(249, 89, 5, 0.28) 0%, rgba(249, 89, 5, 0) 62%);
  pointer-events: none;
}

.cf__badge {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 76px;
  height: 76px;
  border-radius: var(--radius-full);
  background: var(--color-bg);
  color: var(--color-success);
  box-shadow: 0 0 0 8px rgba(255, 255, 255, 0.08), 0 10px 30px rgba(0, 0, 0, 0.25);
}

.cf__eyebrow {
  margin: var(--space-lg) 0 0;
  font-size: var(--font-size-sm);
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-accent);
}

.cf__title {
  margin: var(--space-xs) auto 0;
  max-width: 16ch;
  font-family: var(--font-heading);
  font-weight: 700;
  font-size: clamp(1.85rem, 7vw, var(--font-size-2xl));
  line-height: var(--line-height-heading);
  color: var(--color-text-light);
}

.cf__lead {
  margin: var(--space-md) auto 0;
  max-width: 42ch;
  font-size: 1.1rem;
  line-height: 1.5;
  color: rgba(255, 255, 255, 0.92);
}

.cf__channel {
  margin: var(--space-sm) auto 0;
  max-width: 40ch;
  font-size: var(--font-size-sm);
  color: var(--color-slate-300);
}

/* ---------- Divider ---------- */
.cf__divider {
  margin-top: -1px;
  line-height: 0;
}

.cf__divider svg {
  display: block;
  width: 100%;
  height: 48px;
}

/* ---------- Body ---------- */
.cf__body {
  position: relative;
  z-index: 1;
  max-width: 680px;
  margin: -2rem auto 0;
  padding: 0 var(--space-md) var(--space-3xl);
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.card {
  background: var(--color-bg);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  box-shadow: 0 8px 28px rgba(4, 26, 73, 0.06);
}

.card__eyebrow {
  margin: 0 0 var(--space-xs);
  font-size: var(--font-size-sm);
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

/* ---------- Stat card ---------- */
.statcard {
  display: flex;
  align-items: flex-start;
  gap: var(--space-md);
}

.statcard__icon {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  background: var(--color-bg-muted);
  color: var(--color-primary);
}

.statcard__text {
  margin: 0;
  font-size: 1.15rem;
  line-height: 1.45;
  color: var(--color-text);
}

.statcard__text strong {
  font-weight: 700;
  color: var(--color-primary);
}

.statcard__note {
  margin: var(--space-sm) 0 0;
  font-size: var(--font-size-sm);
  line-height: 1.55;
  color: var(--color-text-muted);
}

/* ---------- Access code keepsake ---------- */
.keycard {
  position: relative;
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  color: var(--color-text-light);
  background:
    radial-gradient(120% 140% at 100% 0%, rgba(249, 89, 5, 0.22) 0%, rgba(249, 89, 5, 0) 55%),
    var(--color-primary);
  box-shadow: 0 12px 32px rgba(4, 26, 73, 0.22);
  overflow: hidden;
}

.keycard__head {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.keycard__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  background: var(--color-accent);
  color: var(--color-text-light);
  flex-shrink: 0;
}

.keycard__title {
  margin: 0;
  font-family: var(--font-heading);
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text-light);
}

.keycard__lead {
  margin: 0 0 var(--space-md);
  font-size: var(--font-size-base);
  line-height: 1.55;
  color: rgba(255, 255, 255, 0.82);
}

.keycard__field {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  padding: var(--space-sm);
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.16);
}

.keycard__token {
  font-family: 'Courier New', ui-monospace, monospace;
  font-size: 0.95rem;
  letter-spacing: 0.02em;
  word-break: break-all;
  color: var(--color-text-light);
  padding: var(--space-xs) var(--space-sm);
  user-select: all;
  text-decoration: none;
}
.keycard__token:hover { text-decoration: underline; }

.keycard__copy {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-xs);
  padding: var(--space-sm) var(--space-md);
  font-family: var(--font-body);
  font-size: var(--font-size-base);
  font-weight: 600;
  color: var(--color-text-light);
  background: var(--color-accent);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background 0.18s, transform 0.18s;
}

.keycard__copy:hover {
  background: var(--color-accent-hover);
}

.keycard__copy:active {
  transform: scale(0.97);
}

.keycard__copy.is-copied {
  background: var(--color-success);
}

.keycard__note {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  margin: var(--space-md) 0 0;
  font-size: var(--font-size-sm);
  color: rgba(255, 255, 255, 0.7);
}

.keycard__note svg {
  flex-shrink: 0;
}

/* ---------- Clinics ---------- */
.clinics__head {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.clinics__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  background: #ecfdf5;
  color: #059669;
  flex-shrink: 0;
}

.clinics__title {
  margin: 0;
  font-family: var(--font-heading);
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--color-primary);
}

.clinics__lead {
  margin: 0 0 var(--space-md);
  line-height: 1.5;
  color: var(--color-text-muted);
}

.clinics__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
}

.clinics__item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: var(--space-sm) 0;
  border-top: 1px solid var(--color-border-light);
}

.clinics__item:first-child {
  border-top: 0;
}

.clinics__name {
  font-weight: 600;
  color: var(--color-text);
}

.clinics__meta {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.clinics__meta a {
  color: var(--color-accent);
}

/* ---------- Share / referral nudge ---------- */
.share-card {
  border-left: 4px solid var(--color-accent);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  align-items: flex-start;
}

.share-card__title {
  margin: 0;
  font-family: var(--font-heading);
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--color-primary);
}

.share-card__text {
  margin: 0;
  line-height: 1.55;
  color: var(--color-text-muted);
}

.share-card__btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  margin-top: var(--space-xs);
  padding: var(--space-sm) var(--space-md);
  font-family: var(--font-body);
  font-size: var(--font-size-base);
  font-weight: 600;
  color: var(--color-text-light);
  background: var(--color-accent);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background 0.18s, transform 0.18s;
}

.share-card__btn:hover {
  background: var(--color-accent-hover);
}

.share-card__btn:active {
  transform: scale(0.97);
}

.share-card__btn.is-copied {
  background: var(--color-success);
}

/* ---------- Next steps ---------- */
.next {
  margin-top: var(--space-sm);
}

.next__label {
  margin: 0 0 var(--space-md);
  font-family: var(--font-heading);
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--color-primary);
}

.next__grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-md);
}

.action {
  position: relative;
  display: grid;
  grid-template-columns: auto 1fr;
  grid-template-areas:
    'icon go'
    'title title'
    'desc desc';
  align-items: center;
  gap: var(--space-xs) var(--space-md);
  padding: var(--space-lg);
  background: var(--color-bg);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  color: var(--color-text);
  text-decoration: none;
  box-shadow: 0 8px 28px rgba(4, 26, 73, 0.06);
  transition: transform 0.18s, box-shadow 0.18s, border-color 0.18s;
}

.action::before {
  content: '';
  position: absolute;
  inset: 0 0 auto 0;
  height: 3px;
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  background: var(--color-accent);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.22s ease;
}

.action:hover {
  text-decoration: none;
  transform: translateY(-3px);
  border-color: transparent;
  box-shadow: 0 14px 34px rgba(4, 26, 73, 0.12);
}

.action:hover::before {
  transform: scaleX(1);
}

.action__icon {
  grid-area: icon;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 46px;
  height: 46px;
  border-radius: var(--radius-md);
  background: var(--color-bg-muted);
  color: var(--color-primary);
  transition: background 0.18s, color 0.18s;
}

.action:hover .action__icon {
  background: var(--color-accent);
  color: var(--color-text-light);
}

.action__title {
  grid-area: title;
  margin-top: var(--space-sm);
  font-family: var(--font-heading);
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-primary);
}

.action__desc {
  grid-area: desc;
  font-size: var(--font-size-sm);
  line-height: 1.5;
  color: var(--color-text-muted);
}

.action__go {
  grid-area: go;
  justify-self: end;
  color: var(--color-slate-300);
  transition: color 0.18s, transform 0.18s;
}

.action:hover .action__go {
  color: var(--color-accent);
  transform: translate(2px, -2px);
}

/* ---------- Motion ---------- */
@media (prefers-reduced-motion: no-preference) {
  .cf__badge {
    animation: badge-pop 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) both;
  }

  .cf__title,
  .cf__lead,
  .cf__channel {
    animation: rise 0.5s ease both;
  }

  .cf__lead { animation-delay: 0.08s; }
  .cf__channel { animation-delay: 0.14s; }

  .action {
    animation: rise 0.4s ease both;
    animation-delay: calc(0.06s * var(--i));
  }
}

@keyframes badge-pop {
  from { transform: scale(0.4); opacity: 0; }
  to   { transform: scale(1); opacity: 1; }
}

@keyframes rise {
  from { transform: translateY(10px); opacity: 0; }
  to   { transform: translateY(0); opacity: 1; }
}

/* ---------- Responsive ---------- */
@media (min-width: 560px) {
  .cf__hero {
    padding-top: var(--space-3xl);
  }

  .cf__body {
    margin-top: -2.5rem;
  }

  .keycard__field {
    flex-direction: row;
    align-items: center;
  }

  .keycard__token {
    flex: 1;
    min-width: 0;
  }

  .keycard__copy {
    flex-shrink: 0;
  }

  .clinics__item {
    flex-direction: row;
    align-items: baseline;
    justify-content: space-between;
    gap: var(--space-md);
  }
}

@media (min-width: 768px) {
  .cf__divider svg {
    height: 64px;
  }

  .next__grid {
    grid-template-columns: repeat(3, 1fr);
  }

  .action {
    grid-template-columns: 1fr;
    grid-template-areas:
      'icon'
      'title'
      'desc'
      'go';
    align-items: stretch;
  }

  .action__go {
    margin-top: var(--space-sm);
    justify-self: start;
  }
}
</style>

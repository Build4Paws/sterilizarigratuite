<template>
  <div class="page-despre">
    <!-- Hero -->
    <section class="hero">
      <div class="container hero__inner">
        <Stethoscope class="hero__icon" :size="44" aria-hidden="true" />
        <p class="hero__eyebrow">Ghid medical</p>
        <h1 class="hero__title">Despre sterilizare</h1>
        <p class="hero__subtitle">
          Tot ce trebuie să știi — înainte, după și în timpul procedurii.
        </p>
        <p class="hero__credit">
          Conținut medical:
          <a
            href="https://urgenteveterinare.com"
            target="_blank"
            rel="noopener nofollow"
          >dr. Denisa Săraru — urgenteveterinare.com</a>
        </p>
      </div>
    </section>

    <!-- Curved divider -->
    <div class="divider" aria-hidden="true">
      <svg viewBox="0 0 1440 120" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M0,0 L0,60 Q360,120 720,80 Q1080,40 1440,90 L1440,0 Z" fill="var(--color-primary)" />
      </svg>
    </div>

    <!-- Lead / intro -->
    <section class="lead">
      <div class="container lead__inner">
        <span class="lead__rule" aria-hidden="true"></span>
        <p class="lead__text">
          Sterilizarea este una dintre cele mai responsabile decizii pe care le poți lua
          pentru animalul tău de companie. Reduce semnificativ riscul de tumori mamare și
          uterine, elimină sarcinile nedorite și contribuie la o viață mai lungă, mai
          liniștită și mai sănătoasă.
        </p>
        <p class="lead__sub">
          Mai jos găsești pașii — pe scurt, ce ai de făcut înainte, după și ce trebuie
          să știi despre procedură.
        </p>
        <nav class="lead__chips" aria-label="Sări la o secțiune">
          <a
            v-for="(step, i) in steps"
            :key="step.title"
            :href="`#pasul-${i + 1}`"
            class="chip"
            :class="`chip--${step.accent}`"
          >
            <span class="chip__num">{{ i + 1 }}</span>
            <span class="chip__label">{{ step.shortLabel }}</span>
          </a>
        </nav>
      </div>
    </section>

    <!-- Why sterilize — 3 benefits -->
    <section class="benefits">
      <div class="container">
        <h2 class="section-title">De ce contează</h2>
        <ul class="benefits__grid">
          <li v-for="b in benefits" :key="b.title" class="benefit">
            <div class="benefit__icon-wrap" aria-hidden="true">
              <component :is="b.icon" :size="26" class="benefit__icon" />
            </div>
            <h3 class="benefit__title">{{ b.title }}</h3>
            <p class="benefit__text">{{ b.text }}</p>
          </li>
        </ul>
      </div>
    </section>

    <!-- 3 steps -->
    <section class="steps">
      <div class="container steps__inner">
        <h2 class="section-title section-title--center">Pașii sterilizării</h2>

        <article
          v-for="(step, i) in steps"
          :id="`pasul-${i + 1}`"
          :key="step.title"
          class="step"
          :class="`step--${step.accent}`"
        >
          <div class="step__head">
            <div class="step__badge" aria-hidden="true">
              <component :is="step.icon" :size="22" />
            </div>
            <div>
              <p class="step__label">Pasul {{ i + 1 }}</p>
              <h3 class="step__title">{{ step.title }}</h3>
            </div>
          </div>

          <ol class="step__list">
            <li v-for="item in step.items" :key="item.title" class="step__item">
              <div class="step__item-num" aria-hidden="true">{{ item.n }}</div>
              <div class="step__item-body">
                <h4 class="step__item-title">{{ item.title }}</h4>
                <p class="step__item-text">{{ item.text }}</p>
              </div>
            </li>
          </ol>
        </article>
      </div>
    </section>

    <!-- Alarm signals callout -->
    <section class="alarm-section">
      <div class="container">
        <aside class="alarm" role="note" aria-labelledby="alarm-title">
          <div class="alarm__header">
            <AlertTriangle :size="22" class="alarm__icon" aria-hidden="true" />
            <p id="alarm-title" class="alarm__eyebrow">Atenție — semnale de alarmă</p>
          </div>
          <p class="alarm__lead">
            Mergi imediat la medicul veterinar dacă observi:
          </p>
          <ul class="alarm__list">
            <li v-for="sig in alarmSignals" :key="sig">{{ sig }}</li>
          </ul>
        </aside>
      </div>
    </section>

    <!-- 24/7 partner block -->
    <section class="emergency">
      <div class="container">
        <div class="emergency__card">
          <p class="emergency__eyebrow">Dispecerat non-stop</p>
          <h2 class="emergency__title">Ai nevoie de ajutor urgent?</h2>
          <p class="emergency__text">
            Zi sau noapte, în weekend sau de sărbători — un operator real îți răspunde
            imediat, îți spune unde să mergi și ce să faci până ajungi la medic.
            Nu aștepta până luni dimineața.
          </p>
          <a
            href="https://urgenteveterinare.com"
            target="_blank"
            rel="noopener nofollow"
            class="emergency__cta"
          >
            <PhoneCall :size="18" aria-hidden="true" />
            urgenteveterinare.com
          </a>
          <p class="emergency__note">
            Serviciu independent oferit de partenerii noștri medicali.
          </p>
        </div>
      </div>
    </section>

    <!-- Final CTA — back to Build4Paws funnel -->
    <section class="final-cta">
      <div class="container final-cta__inner">
        <PawPrint class="final-cta__icon" :size="36" aria-hidden="true" />
        <h2 class="final-cta__title">
          Sterilizarea gratuită este un cadou pentru animalul tău și pentru comunitate.
        </h2>
        <p class="final-cta__text">
          Profită de campaniile organizate în țară sau înscrie-te ca să te anunțăm
          când apare una în localitatea ta.
        </p>
        <div class="final-cta__actions">
          <NuxtLink to="/campanii" class="btn btn--accent">
            Vezi campaniile active
          </NuxtLink>
          <NuxtLink to="/" class="btn btn--ghost">
            Înscrie-te să fii anunțat
          </NuxtLink>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import {
  Stethoscope,
  HeartPulse,
  Smile,
  Users,
  ClipboardList,
  HeartHandshake,
  Activity,
  AlertTriangle,
  PhoneCall,
  PawPrint,
} from 'lucide-vue-next'

definePageMeta({ layout: 'default' })

const benefits = [
  {
    icon: HeartPulse,
    title: 'Mai sănătos, mai mult timp',
    text: 'Reduce semnificativ riscul de tumori mamare și uterine și contribuie la o viață mai lungă.',
  },
  {
    icon: Smile,
    title: 'Mai liniștit, la fel de jucăuș',
    text: 'Animalul devine mai calm în perioadele de călduri, dar rămâne afectuos și atașat de tine.',
  },
  {
    icon: Users,
    title: 'Un gest pentru comunitate',
    text: 'Mai puține sarcini nedorite înseamnă mai puține animale abandonate pe străzile orașului.',
  },
]

const steps = [
  {
    accent: 'before',
    icon: ClipboardList,
    title: 'Înainte de sterilizare',
    shortLabel: 'Înainte',
    items: [
      {
        n: 1,
        title: 'Post alimentar de 8–12 ore',
        text: 'Nu da mâncare în seara dinaintea operației. Apa poate rămâne disponibilă până cu aproximativ 2 ore înainte de procedură.',
      },
      {
        n: 2,
        title: 'Verifică starea de sănătate',
        text: 'Asigură-te că animalul nu prezintă tuse, diaree, vărsături sau febră în zilele dinainte. Orice simptom neobișnuit trebuie anunțat medicului veterinar.',
      },
      {
        n: 3,
        title: 'Pregătește transportul și locul de recuperare',
        text: 'Folosește o cușcă de transport sigură. Acasă, pregătește o cameră liniștită, ferită de alte animale și de copii, cu o pătură curată și călduroasă.',
      },
    ],
  },
  {
    accent: 'after',
    icon: HeartHandshake,
    title: 'După sterilizare',
    shortLabel: 'După',
    items: [
      {
        n: 1,
        title: 'Liniște și căldură primele 24 de ore',
        text: 'Anestezia dispare treptat — animalul va fi somnoros și instabil pe picioare. Nu-l lăsa să sară pe canapea, pe pat sau pe scări.',
      },
      {
        n: 2,
        title: 'Verifică zilnic plaga operatorie',
        text: 'Trebuie să fie curată, fără secreții, fără roșeață excesivă și fără umflături. Folosește guler Elizabetan pentru a împiedica lingerea sau scărpinarea.',
      },
      {
        n: 3,
        title: 'Respectă tratamentul prescris',
        text: 'Administrează antibioticele și antiinflamatoarele exact conform indicațiilor. Programează scoaterea firelor — de regulă la 10–14 zile de la operație.',
      },
    ],
  },
  {
    accent: 'procedure',
    icon: Activity,
    title: 'Ce trebuie să știi despre procedură',
    shortLabel: 'Procedură',
    items: [
      {
        n: 1,
        title: 'Este o intervenție de rutină, sigură',
        text: 'Se efectuează sub anestezie generală, durează între 20 și 60 de minute, iar animalul pleacă acasă în aceeași zi.',
      },
      {
        n: 2,
        title: 'Nu îți schimbă caracterul animalului',
        text: 'Devine mai calm și mai puțin agresiv în perioadele de călduri, dar rămâne la fel de jucăuș, afectuos și atașat de tine.',
      },
      {
        n: 3,
        title: 'Apetitul poate crește',
        text: 'Ajustează porțiile de mâncare și asigură-i mișcare zilnică, pentru a preveni obezitatea — cea mai frecventă problemă post-sterilizare.',
      },
    ],
  },
]

const alarmSignals = [
  'Sângerare la plagă sau plagă deschisă',
  'Vărsături repetate sau refuzul apei mai mult de 24 de ore',
  'Animal apatic, care nu se ridică sau nu reacționează',
]

useSeoMeta({
  title: 'Despre sterilizare — ghid pentru câini și pisici · Sterilizări Gratuite',
  description: 'Ghid medical: ce trebuie să știi înainte, după și în timpul sterilizării câinilor și pisicilor. Pași simpli, semnale de alarmă, recuperare.',
  ogTitle: 'Despre sterilizare — ghid complet',
  ogDescription: 'Tot ce trebuie să știi înainte, după și în timpul sterilizării — pe înțelesul tuturor.',
})

const siteConfig = useSiteConfig()
const siteUrl = (siteConfig.url as string | undefined) || 'https://sterilizarigratuite.ro'

useHead(() => ({
  link: [{ rel: 'canonical', href: `${siteUrl}/despre-sterilizare` }],
  script: [
    {
      type: 'application/ld+json',
      key: 'despre-article',
      innerHTML: safeJsonLd({
        '@context': 'https://schema.org',
        '@type': 'Article',
        headline: 'Despre sterilizare — ghid pentru câini și pisici',
        description: 'Ghid medical complet despre sterilizarea câinilor și pisicilor: pregătire, procedură și recuperare.',
        inLanguage: 'ro',
        url: `${siteUrl}/despre-sterilizare`,
        author: {
          '@type': 'Person',
          name: 'dr. Denisa Săraru',
          affiliation: {
            '@type': 'Organization',
            name: 'urgenteveterinare.com',
            url: 'https://urgenteveterinare.com',
          },
        },
        publisher: {
          '@type': 'Organization',
          name: 'Sterilizări Gratuite',
          url: siteUrl,
        },
      }),
    },
    {
      type: 'application/ld+json',
      key: 'despre-breadcrumbs',
      innerHTML: safeJsonLd({
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        itemListElement: [
          { '@type': 'ListItem', position: 1, name: 'Acasă', item: `${siteUrl}/` },
          { '@type': 'ListItem', position: 2, name: 'Despre sterilizare', item: `${siteUrl}/despre-sterilizare` },
        ],
      }),
    },
  ],
}))
</script>

<style scoped>
.page-despre {
  background: var(--color-bg-muted);
}

/* ---- Hero ---- */
.hero {
  background: var(--color-primary);
  color: var(--color-text-light);
  padding: var(--space-3xl) 0 6rem;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.hero__inner {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-sm);
}

.hero__icon {
  color: var(--color-accent);
  margin-bottom: var(--space-xs);
}

.hero__eyebrow {
  font-family: var(--font-heading);
  font-size: var(--font-size-sm);
  font-weight: 600;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--color-accent);
  margin: 0;
}

.hero__title {
  font-family: var(--font-heading);
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--color-text-light);
  margin: 0;
  max-width: 700px;
  line-height: 1.15;
}

.hero__subtitle {
  font-size: var(--font-size-lg);
  color: var(--color-slate-300);
  font-weight: 400;
  max-width: 560px;
  margin: var(--space-xs) auto 0;
  line-height: 1.5;
}

.hero__credit {
  font-size: var(--font-size-sm);
  color: var(--color-slate-300);
  margin-top: var(--space-md);
  opacity: 0.85;
}

.hero__credit a {
  color: var(--color-text-light);
  text-decoration: underline;
  text-decoration-color: rgba(255, 255, 255, 0.35);
  text-underline-offset: 3px;
}

.hero__credit a:hover {
  text-decoration-color: var(--color-accent);
}

/* ---- Curved divider ---- */
.divider {
  margin-top: -1px;
  line-height: 0;
  background: var(--color-bg);
}

.divider svg {
  width: 100%;
  height: 80px;
  display: block;
}

/* ---- Section titles (shared) ---- */
.section-title {
  font-family: var(--font-heading);
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--color-primary);
  margin: 0 0 var(--space-xl);
}

.section-title--center {
  text-align: center;
}

/* ---- Lead ---- */
.lead {
  background: var(--color-bg);
  padding: var(--space-3xl) 0 var(--space-2xl);
}

.lead__inner {
  max-width: 760px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: var(--space-md);
}

/* Thin orange accent rule above the paragraph — quiet but signals "article opener". */
.lead__rule {
  display: block;
  width: 48px;
  height: 3px;
  border-radius: 2px;
  background: var(--color-accent);
}

.lead__text {
  font-family: var(--font-heading);
  font-size: 1.5rem;
  font-weight: 500;
  color: var(--color-primary);
  line-height: 1.4;
  letter-spacing: -0.01em;
  margin: 0;
  max-width: 680px;
}

.lead__sub {
  font-size: var(--font-size-base);
  color: var(--color-text-muted);
  line-height: 1.6;
  margin: 0;
  max-width: 560px;
}

.lead__chips {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-sm);
  margin-top: var(--space-md);
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md) var(--space-sm) var(--space-xs);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  text-decoration: none;
  transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s, background-color 0.2s;
}

.chip:hover {
  text-decoration: none;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(4, 26, 73, 0.08);
}

.chip__num {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-heading);
  font-weight: 700;
  font-size: 0.85rem;
  color: var(--color-text-light);
  background: var(--color-primary);
  flex-shrink: 0;
}

.chip__label {
  font-family: var(--font-heading);
  font-weight: 600;
  font-size: var(--font-size-sm);
  color: var(--color-primary);
  letter-spacing: 0.01em;
}

.chip--before .chip__num { background: var(--color-primary); }
.chip--before:hover { border-color: var(--color-primary); }

.chip--after .chip__num { background: var(--color-success); }
.chip--after:hover { border-color: var(--color-success); }

.chip--procedure .chip__num { background: var(--color-accent); }
.chip--procedure:hover { border-color: var(--color-accent); }

/* Anchor offset so step headings clear the page top when chip-linked. */
.step {
  scroll-margin-top: var(--space-xl);
}

/* ---- Benefits ---- */
.benefits {
  background: var(--color-bg);
  padding: var(--space-2xl) 0;
}

.benefits__grid {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-lg);
}

.benefit {
  background: var(--color-bg);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--space-sm);
  transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s;
}

.benefit:hover {
  border-color: var(--color-accent);
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(4, 26, 73, 0.08);
}

.benefit__icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: rgba(249, 89, 5, 0.10);
  display: flex;
  align-items: center;
  justify-content: center;
}

.benefit__icon {
  color: var(--color-accent);
}

.benefit__title {
  font-family: var(--font-heading);
  font-size: 1.05rem;
  color: var(--color-primary);
  margin: 0;
  font-weight: 700;
}

.benefit__text {
  font-size: var(--font-size-base);
  color: var(--color-text-muted);
  line-height: 1.55;
  margin: 0;
}

/* ---- Steps ---- */
.steps {
  background: var(--color-bg-muted);
  padding: var(--space-3xl) 0;
}

.steps__inner {
  max-width: 820px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-xl);
}

.step {
  background: var(--color-bg);
  border-radius: var(--radius-lg);
  border-left: 4px solid var(--color-primary);
  padding: var(--space-xl) var(--space-xl) var(--space-lg);
  box-shadow: 0 4px 14px rgba(4, 26, 73, 0.06);
}

.step--before { border-left-color: var(--color-primary); }
.step--after { border-left-color: var(--color-success); }
.step--procedure { border-left-color: var(--color-accent); }

.step__head {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.step__badge {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: var(--color-text-light);
  background: var(--color-primary);
}

.step--after .step__badge { background: var(--color-success); }
.step--procedure .step__badge { background: var(--color-accent); }

.step__label {
  font-family: var(--font-heading);
  font-size: var(--font-size-sm);
  font-weight: 600;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--color-text-muted);
  margin: 0 0 var(--space-xs);
}

.step__title {
  font-family: var(--font-heading);
  font-size: 1.4rem;
  color: var(--color-primary);
  margin: 0;
  font-weight: 700;
  line-height: 1.2;
}

.step__list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.step__item {
  display: flex;
  gap: var(--space-md);
  align-items: flex-start;
}

.step__item-num {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--color-bg-muted);
  color: var(--color-primary);
  font-family: var(--font-heading);
  font-weight: 700;
  font-size: 0.95rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}

.step--after .step__item-num { color: var(--color-success); }
.step--procedure .step__item-num { color: var(--color-accent); }

.step__item-body {
  flex: 1;
  min-width: 0;
}

.step__item-title {
  font-family: var(--font-heading);
  font-size: 1.05rem;
  color: var(--color-primary);
  margin: 0 0 var(--space-xs);
  font-weight: 700;
}

.step__item-text {
  font-size: var(--font-size-base);
  color: var(--color-text-muted);
  line-height: 1.6;
  margin: 0;
}

/* ---- Alarm callout ---- */
.alarm-section {
  background: var(--color-bg);
  padding: var(--space-2xl) 0;
}

.alarm {
  max-width: 820px;
  margin: 0 auto;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-left: 5px solid var(--color-error);
  border-radius: var(--radius-lg);
  padding: var(--space-lg) var(--space-xl);
}

.alarm__header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.alarm__icon {
  color: var(--color-error);
  flex-shrink: 0;
}

.alarm__eyebrow {
  font-family: var(--font-heading);
  font-size: var(--font-size-sm);
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--color-error);
  margin: 0;
}

.alarm__lead {
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 var(--space-sm);
}

.alarm__list {
  margin: 0;
  padding-left: var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.alarm__list li {
  color: var(--color-text);
  line-height: 1.55;
}

/* ---- Emergency 24/7 block ---- */
.emergency {
  background: var(--color-bg-muted);
  padding: var(--space-2xl) 0 var(--space-3xl);
}

.emergency__card {
  max-width: 820px;
  margin: 0 auto;
  background: var(--color-primary);
  color: var(--color-text-light);
  border-radius: var(--radius-lg);
  padding: var(--space-2xl) var(--space-xl);
  text-align: center;
  position: relative;
  overflow: hidden;
  box-shadow: 0 10px 32px rgba(4, 26, 73, 0.18);
}

.emergency__card::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 0% 0%, rgba(249, 89, 5, 0.18), transparent 40%),
    radial-gradient(circle at 100% 100%, rgba(249, 89, 5, 0.12), transparent 40%);
  pointer-events: none;
}

.emergency__card > * {
  position: relative;
  z-index: 1;
}

.emergency__eyebrow {
  font-family: var(--font-heading);
  font-size: var(--font-size-sm);
  font-weight: 600;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--color-accent);
  margin: 0 0 var(--space-sm);
}

.emergency__title {
  font-family: var(--font-heading);
  font-size: var(--font-size-lg);
  color: var(--color-text-light);
  margin: 0 0 var(--space-md);
  font-weight: 700;
}

.emergency__text {
  font-size: var(--font-size-base);
  color: var(--color-slate-300);
  line-height: 1.6;
  max-width: 560px;
  margin: 0 auto var(--space-lg);
}

.emergency__cta {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  background: var(--color-accent);
  color: var(--color-text-light);
  font-family: var(--font-heading);
  font-weight: 600;
  font-size: 1.05rem;
  padding: var(--space-sm) var(--space-xl);
  border-radius: var(--radius-md);
  text-decoration: none;
  transition: background 0.2s, transform 0.2s;
}

.emergency__cta:hover {
  background: var(--color-accent-hover);
  text-decoration: none;
  transform: translateY(-1px);
}

.emergency__note {
  font-size: var(--font-size-sm);
  color: var(--color-slate-300);
  opacity: 0.75;
  margin: var(--space-md) 0 0;
}

/* ---- Final CTA ---- */
.final-cta {
  background: var(--color-bg);
  padding: var(--space-3xl) 0;
}

.final-cta__inner {
  max-width: 720px;
  margin: 0 auto;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-md);
}

.final-cta__icon {
  color: var(--color-accent);
}

.final-cta__title {
  font-family: var(--font-heading);
  font-size: 1.5rem;
  color: var(--color-primary);
  font-weight: 700;
  margin: 0;
  line-height: 1.3;
}

.final-cta__text {
  color: var(--color-text-muted);
  line-height: 1.6;
  margin: 0;
  max-width: 560px;
}

.final-cta__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-md);
  margin-top: var(--space-sm);
}

.btn {
  display: inline-flex;
  align-items: center;
  font-family: var(--font-heading);
  font-weight: 600;
  padding: var(--space-sm) var(--space-xl);
  border-radius: var(--radius-md);
  text-decoration: none;
  transition: background 0.2s, color 0.2s, border-color 0.2s;
  border: 2px solid transparent;
  line-height: 1.4;
}

.btn--accent {
  background: var(--color-accent);
  color: var(--color-text-light);
}

.btn--accent:hover {
  background: var(--color-accent-hover);
  text-decoration: none;
}

.btn--ghost {
  background: transparent;
  color: var(--color-primary);
  border-color: var(--color-primary);
}

.btn--ghost:hover {
  background: var(--color-primary);
  color: var(--color-text-light);
  text-decoration: none;
}

/* ---- Responsive ---- */
@media (min-width: 1300px) {
  .hero {
    padding: var(--space-3xl) 0 8rem;
  }

  .hero__title {
    font-size: var(--font-size-2xl);
  }
}

@media (max-width: 900px) {
  .benefits__grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .hero {
    padding: var(--space-2xl) 0 4rem;
  }

  .hero__title {
    font-size: 1.75rem;
  }

  .hero__subtitle {
    font-size: 1.05rem;
  }

  .divider svg {
    height: 50px;
  }

  .lead__text {
    font-size: 1.05rem;
  }

  .step {
    padding: var(--space-lg) var(--space-md);
  }

  .step__head {
    gap: var(--space-sm);
  }

  .step__badge {
    width: 44px;
    height: 44px;
    border-radius: 12px;
  }

  .step__title {
    font-size: 1.2rem;
  }

  .alarm {
    padding: var(--space-md) var(--space-lg);
  }

  .emergency__card {
    padding: var(--space-xl) var(--space-md);
  }

  .emergency__title {
    font-size: 1.25rem;
  }

  .final-cta__title {
    font-size: 1.25rem;
  }

  .final-cta__actions {
    flex-direction: column;
    align-items: stretch;
  }

  .btn {
    justify-content: center;
  }
}
</style>

# Plan de implementare — feedback pre-lansare

Acest document transformă lista de feedback într-un set de task-uri gata de implementat.
Fiecare task spune **unde** (fișier + reper de linie), **ce** se schimbă și **cum verifici**.

> Zonele marcate `OK ... END OK` din feedback-ul original sunt deja implementate (titlu/subtitlu
> homepage, contorul de înscrieri, butonul „Anunță-mă", label-ul „Salut! Cum te numești?",
> input-ul de telefon cu `0` în față). Nu apar ca task-uri aici.

## Convenții obligatorii (citește înainte de orice modificare)

- **Nuxt 4** — codul stă sub `frontend/app/` (nu `frontend/`). Comenzile rulează din `frontend/`.
- **Toate textele vizibile sunt în română**, ton prietenos, persoana a II-a („te anunțăm…").
- **Fără em dash (`—`, U+2014) în text vizibil.** Vezi T4. La nevoie pentru intervale folosește
  en dash `–` (U+2013) sau reformulează. Nu introduce em dash-uri noi în niciun task.
- **Design tokens** din `app/assets/css/main.css` (`--color-primary` navy `#041A49`,
  `--color-accent` orange `#F95905`, fonturi `--font-heading` Funnel Display / `--font-body`
  Rethink Sans). Nu hardcoda hex în `<style scoped>`.
- **Mobile-first.** Majoritatea utilizatorilor sunt pe telefon. Scrie stilurile de bază pentru
  ecran îngust și folosește `@media (min-width: …)` pentru a crește.
- Verificare: `npm run typecheck` (strict). Nu există test runner/linter — spune explicit când nu
  poți verifica automat.
- Telefon: `<UiPhoneInput>` afișează formatul național `07XX XXX XXX` dar **stochează `+40XXXXXXXXX`**.
  Validează cu `isValidPhone` / `stripPhone` din `app/utils/validators.ts`.

## Stare curentă (actualizat)

**Făcute:** T1, T2, T8 — implementate și verificate în browser (mobil + desktop), `npm run typecheck`
trece (exit 0). Modificările sunt pe branch-ul `main`, **fără commit**.

**Rămase de făcut:** T3, T4, T5, T6, T7, T9, T12.

## Sumar task-uri

| ID | Status | Task | Fișier principal | Risc |
|----|--------|------|------------------|------|
| T1 | ✅ Done | Copy nou pe pagina de confirmare cetățean | `app/pages/confirmare.vue` | mic |
| T2 | ✅ Done | „alt județ sau altă specie" doar când e specie selectată | `app/pages/campanii.vue` | mic |
| T3 | ⬜ Todo | Iconițe distincte și consistente câine/pisică | nou `app/components/ui/SpeciesIcon.vue` + 3 fișiere | mediu |
| T4 | ⬜ Todo | Elimină em dash-ul peste tot (inclusiv meta) | global | mediu |
| T5 | ⬜ Todo | Redenumește „Top județe după…" + clarifică matematica speciilor | `app/components/map/SidePanel.vue` | mediu |
| T6 | ⬜ Todo | Telefon + detalii + link campanie în panoul hărții | `app/components/map/SidePanel.vue` | mediu |
| T7 | ⬜ Todo | Harta pornește pe „Ofertă" implicit | `app/pages/harta.vue` | mic |
| T8 | ✅ Done | „locuri disponibile" → „numărul de locuri alocate campaniei" | `app/pages/organizatori.vue` | mic |
| T9 | ⬜ Todo | Telefon public diferit pentru medic în formular organizator | `app/components/forms/CampaignForm.vue` | mic |
| T10 | ✅ Done | Buton „înapoi sus" pe orice pagină | nou `app/components/layout/BackToTop.vue` + layout | mic |
| T11 | ✅ Done | Pagină dedicată de donații / sprijin | nou `app/pages/sustine.vue` + nav/footer | mediu |
| T12 | ⬜ Todo | Numerotarea paragrafelor din Termeni și Condiții | de localizat | INVESTIGHează |
| T13 | ✅ Done | Format dată lună/zi/an în formular campanii + „rest" stray | `app/components/forms/CampaignForm.vue` | INVESTIGHează |

---

## T1 — Copy nou pe pagina de confirmare cetățean ✅ DONE

**Status:** implementat în `app/pages/confirmare.vue` și verificat în browser. Realizat: titlu
„Gata, {nume}!" + frază lead, rang cu „…care vor fi alertate / va fi alertată", paragraf despre
primărie (Legea 258/2013) cu localitatea dinamică, și callout „Fiecare înscriere contează!" cu buton
„Copiază linkul" (copiază `https://sterilizarigratuite.ro/` + toast). Stiluri noi: `.cf__lead`,
`.statcard__note`, `.share-card*`. Detaliile de mai jos rămân ca referință a ce s-a făcut.

**Fișier:** `app/pages/confirmare.vue` (pagina a fost recent redesenată; modifici doar copy + adaugi 2 blocuri).

### 1a. Hero (liniile ~9–11)
Înlocuiește titlul și adaugă o frază de lead sub el. Structura dorită:

```html
<p class="cf__eyebrow">Înscriere confirmată</p>
<h1 class="cf__title">Gata, {{ firstName }}!</h1>
<p class="cf__lead">De acum primești notificări despre campaniile gratuite din localitatea ta.</p>
<p class="cf__channel">{{ channelMessage }}</p>
```

Adaugă stilul `.cf__lead` lângă `.cf__channel` (aceeași culoare `var(--color-slate-300)`, puțin mai
mare, `margin-top: var(--space-sm)`).

### 1b. Textul de rang (computed `rankParts`, ~liniile 130–210)
Schimbă finalul propozițiilor ca să fie despre „a fi alertat", nu „s-a înscris":
- toate aparițiile `' care s-au înscris.'` → `' care vor fi alertate.'`
- toate aparițiile `' care s-a înscris.'` → `' care va fi alertată.'`

Exemplu rezultat: „Ești **a doua persoană** din **Cugir** și printre primele **28** din județul
**Alba** care vor fi alertate."

### 1c. Paragraf nou despre primărie (în cardul „În zona ta", după `<p class="statcard__text">`, ~linia 36)
Adaugă, în interiorul `<div>`-ului din `.statcard`, sub textul de rang:

```html
<p class="statcard__note">
  Dacă se strâng suficiente cereri din {{ session.locality }}, notificăm oficial primăria,
  care poate aloca fonduri pentru sterilizare gratuită (Legea 258/2013).
</p>
```

Stil `.statcard__note`: `font-size: var(--font-size-sm)`, `color: var(--color-text-muted)`,
`margin-top: var(--space-sm)`, `line-height: 1.55`.

### 1d. Callout „Fiecare înscriere contează" (card nou înainte de secțiunea `.next`)
Adaugă un card distinct (folosește stilul `.card` existent + accent orange la stânga) între
`.keycard`/`.clinics` și `<section class="next">`:

```html
<section class="card share-card">
  <p class="share-card__title">Fiecare înscriere contează!</p>
  <p class="share-card__text">
    Dacă mai ai vecini care vor să își sterilizeze gratuit animalele, spune-le să se înscrie.
  </p>
</section>
```

Opțional (nice to have): un buton care copiază linkul `https://sterilizarigratuite.ro/` folosind
același pattern `navigator.clipboard.writeText` + `toast.success(...)` ca la `copyToken`. Dacă îl
adaugi, textul butonului: „Copiază linkul" / „Link copiat".

**Accept:** pe `/confirmare` (cu sesiune validă) apar: „Gata, {nume}!", fraza de lead, mesajul de
canal, rangul cu „…care vor fi alertate.", paragraful despre primărie cu localitatea reală, și
callout-ul de recomandare. Niciun em dash. `npm run typecheck` trece.

> Cum testezi pagina fără să completezi formularul: pe homepage rulează în consolă
> `sessionStorage.setItem('citizen-session', JSON.stringify({name:'Dragoș Pop',channel:'both',phone:'+40740123456',email:'a@b.ro',countyCode:'AB',countyName:'Alba',locality:'Cugir',species:['dog','cat'],dogCount:1,catCount:2,submittedAt:new Date().toISOString(),stats:{registeredInLocality:1,registeredInCounty:27},manageToken:'8f3b1c9e-7a42-4d6b-9e21-5c0af2b8d7e1'}))`
> apoi navighează la `/confirmare`.

---

## T2 — „alt județ sau altă specie" doar când e selectată o specie ✅ DONE

**Status:** implementat și verificat. `/campanii?judet=alba` → „Încearcă alt județ.";
`/campanii?judet=alba&specie=caine` → „Încearcă alt județ sau altă specie."

**Fișier:** `app/pages/campanii.vue`, computed `emptyText` (~liniile 233–237).

Acum returnează mereu „Încearcă alt județ sau altă specie." când există orice filtru activ. Trebuie
să menționeze specia **doar dacă `species` e setată**:

```ts
const emptyText = computed(() => {
  if (!hasActiveFilters.value) {
    return 'Lasă-ne telefonul sau emailul și te anunțăm când apare una în zona ta.'
  }
  if (species.value) return 'Încearcă alt județ sau altă specie.'
  return 'Încearcă alt județ.'
})
```

**Accept:** `/campanii?judet=alba` (fără `specie`) → „Încearcă alt județ.";
`/campanii?judet=alba&specie=caine` → „Încearcă alt județ sau altă specie."

---

## T3 — Iconițe distincte și consistente pentru câine/pisică

**Problemă:** iconițele `Dog`/`Cat` din lucide sunt folosite în mai multe locuri și se pot confunda
la dimensiuni mici. Vrem (a) o **singură sursă de adevăr** ca să fie identice peste tot și (b) să fie
ușor de distins.

**Pas 1 — componentă comună.** Creează `app/components/ui/SpeciesIcon.vue`:

```vue
<template>
  <component :is="icon" :size="size" :aria-hidden="true" class="species-icon" />
</template>

<script setup lang="ts">
import { Dog, Cat } from 'lucide-vue-next'
import type { Species } from '~/types'

const props = withDefaults(defineProps<{ species: Species; size?: number }>(), { size: 18 })
const icon = computed(() => (props.species === 'dog' ? Dog : Cat))
</script>
```

> Dacă la review-ul vizual `Dog` și `Cat` tot se confundă, schimbă mappingul **doar aici** (de ex.
> menține `Cat` pentru pisică și încearcă o variantă mai citeață pentru câine, sau diferențiază prin
> culoare: câine = `var(--color-primary)`, pisică = `var(--color-accent)`). Pune diferențierea de
> culoare ca prop opțional dacă e nevoie. Schimbarea într-un singur fișier se propagă global.

**Pas 2 — înlocuiește utilizările directe** (`<Dog .../>` / `<Cat .../>`) cu `<UiSpeciesIcon :species="…" />`:
- `app/components/campaign/CampaignCard.vue` — liniile 36 (`Dog`) și 46 (`Cat`); scoate importul
  `Dog, Cat` din linia 81 dacă nu mai e folosit.
- `app/components/map/SidePanel.vue` — liniile 34, 41, 141–142, 162–163; ajustează importul de pe linia 185.
- `app/pages/confirmare.vue` — în computed `speciesTags` (folosește deja `Dog`/`Cat`); poți păstra
  iconul în obiect dar importă-l din aceeași sursă, sau randează `<UiSpeciesIcon>` în template.

**Accept:** aceeași pereche de iconițe apare pe card campanie, panou hartă (breakdown + filtre + listă
top) și header confirmare. Schimbarea iconului într-un singur loc (`SpeciesIcon.vue`) se reflectă
peste tot. `npm run typecheck` trece.

---

## T4 — Elimină em dash-ul peste tot (inclusiv meta)

**Țintă:** caracterul **em dash `—` (U+2014)** din orice text vizibil utilizatorului: template-uri,
string-uri de copy, `useSeoMeta`/`useHead`, `meta` din `nuxt.config.ts`, toast-uri, `placeholder`,
`aria-label`, JSON-LD `name`/`description`.

**Găsește-le:**
```bash
# din frontend/
rg -n --glob '!node_modules' "—" app nuxt.config.ts
```
(45+ apariții; multe sunt și în comentarii de cod — acelea sunt opționale, prioritizează textul vizibil.)

**Reguli de înlocuire:**
- În **proză** (fraze): reformulează cu virgulă, două puncte sau punct. Ex. `nuxt.config.ts:40`
  „Sterilizări Gratuite — Campanii…" → „Sterilizări Gratuite. Campanii…". La fel pentru toate
  `seoTitle`/`seoDescription`/`og*` din `campanii.vue`, `harta.vue`, `index.vue`, paginile admin etc.
- În **intervale de dată/oră**: folosește en dash `–`. Ex. `app/utils/format.ts:23`
  `formatDateRange` returnează `` `${formatDate(start)} — ${formatDate(end)}` `` → schimbă `—` în `–`.
  (Nota: `CampaignCard.vue:22` folosește deja en dash `–` pentru ore, e ok.)

**Locuri confirmate cu em dash în text vizibil** (nu exhaustiv, verifică cu rg):
`nuxt.config.ts` (title, description), `app/utils/format.ts:23`, `app/pages/campanii.vue`
(seoTitle/Description, guide-banner title linia 54), `app/pages/index.vue`, `app/pages/harta.vue`
(SEO), `app/pages/politica-de-confidentialitate.vue` (mai multe „Temei legal: … —"),
`app/components/layout/Footer.vue` nu are, dar verifică. Tratează și paginile `admin/**`.

**Accept:** `rg "—" app nuxt.config.ts` nu mai returnează apariții în string-uri vizibile/meta
(comentariile de cod pot rămâne). `npm run typecheck` trece.

---

## T5 — Redenumește „Top județe după…" + clarifică matematica speciilor

**Fișier:** `app/components/map/SidePanel.vue`.

### 5a. Titlu dinamic în funcție de specie (computed `defaultTitle`, ~liniile 256–260)
Acum e static „Top județe după cerere". Trebuie să reflecte filtrul activ de specie din `species`:

```ts
const defaultTitle = computed(() => {
  if (props.view === 'oferta') return 'Top județe după campanii'
  if (props.view === 'cerere') {
    if (species.value === 'dog') return 'Top județe după cerere câini'
    if (species.value === 'cat') return 'Top județe după cerere pisici'
    return 'Top județe după persoane înscrise'
  }
  return 'Istoric campanii'
})
```

### 5b. Clarifică matematica „total ≠ câini + pisici"
**Cauză:** `total` = numărul de **persoane** înscrise; o persoană poate cere și câini și pisici, deci
`câini + pisici` poate depăși `total` (ex. Vaslui total 27, câini 19, pisici 22). Nu e bug de date, e
etichetare ambiguă. Fă breakdown-ul (liniile ~31–46) să spună clar că sunt **cereri pe specie**, nu o
împărțire a totalului:

- Eticheta mare a totalului (linia 27): păstrează „persoane înscrise".
- Rândurile de specie (liniile 33–44): redenumește „Câini" → „Cereri câini" și „Pisici" →
  „Cereri pisici".
- Adaugă sub breakdown un rând fin explicativ:
  ```html
  <p class="side-panel__hint">O persoană poate cere sterilizare pentru mai multe specii.</p>
  ```
  Stil `.side-panel__hint`: `font-size: 0.72rem; color: var(--color-text-muted); font-style: italic;`.

**Accept:** schimbarea filtrului de specie schimbă titlul listei; breakdown-ul spune „Cereri câini/pisici"
cu nota explicativă; nicio sumă nu mai pare greșită.

---

## T6 — Telefon + detalii + link campanie în panoul hărții (Ofertă)

**Fișier:** `app/components/map/SidePanel.vue`, blocul „Ofertă selected" (liniile ~92–112).

Acum fiecare rând de campanie arată doar dată, localitate, organizație și nu e clickabil. Adaugă
telefon (cu `tel:`) și fă tot rândul link către pagina campaniei. `Campaign` are `id`, `phonePublic`,
`address`, `timeStart`, `timeEnd` (vezi `app/types/campaign.ts`).

```html
<NuxtLink
  v-for="c in countyCampaigns"
  :key="c.id"
  :to="`/campanie/${c.id}`"
  class="side-panel__campaign-row"
>
  <span class="side-panel__campaign-date">{{ formatDate(c.dateStart) }}, {{ c.timeStart }}–{{ c.timeEnd }}</span>
  <span class="side-panel__campaign-loc">{{ c.locality }}</span>
  <span class="side-panel__campaign-org">{{ c.organizationName }}</span>
  <span v-if="c.phonePublic" class="side-panel__campaign-phone">{{ c.phonePublic }}</span>
</NuxtLink>
```

Note:
- `–` între ore e en dash (ok, nu em dash).
- Telefonul: dacă vrei să fie apelabil direct, pune un `<a :href="tel:…" @click.stop>` separat în
  interior; altfel lasă rândul ca link spre detalii (mai sigur pe mobil) și afișează numărul ca text.
- Stilizează `.side-panel__campaign-row` ca link (scoate underline pe hover, `color: inherit`),
  păstrând `border-bottom` existent. Adaugă `.side-panel__campaign-phone` (font mic,
  `color: var(--color-accent)`).
- Verifică ruta detaliu: `app/pages/campanie/[id].vue` există. Confirmă că acceptă `id`-ul folosit.

**Accept:** în tab-ul „Ofertă", selectând un județ cu campanii, fiecare rând duce la
`/campanie/{id}` și afișează ora + telefonul. Pe mobil rândul e ușor de atins.

---

## T7 — Harta pornește pe „Ofertă" implicit

**Fișier:** `app/pages/harta.vue`.

1. Default-ul `activeView` (liniile ~110–114): când nu există `?view=`, folosește `'oferta'` în loc
   de `'cerere'`:
   ```ts
   const activeView = ref<ActiveView>(
     (['cerere', 'oferta', 'istoric'] as const).includes(route.query.view as ActiveView)
       ? (route.query.view as ActiveView)
       : 'oferta',
   )
   ```
2. `setView` (liniile ~253–267): inversează logica de URL ca să fie „ofertă" canonic (fără query) și
   „cerere" explicit. Adică pentru `view === 'oferta'` fă `delete q.view`, iar pentru `'cerere'`
   setează `q.view = 'cerere'`. Astfel `/harta` arată Ofertă, iar `/harta?view=cerere` arată Cerere.
3. Verifică `onMounted` și `?judet=` să funcționeze în continuare pe ambele view-uri.

**Accept:** `/harta` (fără query) deschide tab-ul „Ofertă"; comutarea pe „Cerere" pune `?view=cerere`;
revenirea pe „Ofertă" curăță query-ul. SSR-ul nu aruncă erori.

---

## T8 — „locuri disponibile" → „numărul de locuri alocate campaniei" ✅ DONE

**Status:** implementat și verificat. Răspunsul FAQ folosește acum „numărul de locuri alocate
campaniei"; nu mai există „locuri disponibile" în `app/`.

**Fișier:** `app/pages/organizatori.vue`, linia ~127 (răspuns FAQ).

Înlocuiește în text „locurile disponibile" cu „numărul de locuri alocate campaniei":

> „Publicăm doar numele organizației, locația, datele campaniei, numărul de locuri alocate campaniei,
> medicul (dacă îl specifici) și un telefon de contact pentru cetățeni. …"

(Restul aplicației folosește deja formularea corectă: `campanie/[id].vue:94` și etichetele din
`CampaignCard.vue` „locuri alocate câini/pisici".)

**Accept:** căutarea „locuri disponibile" în `app/` nu mai întoarce rezultate.

---

## T9 — Telefon public diferit pentru medic în formularul de organizator

**Fișier:** `app/components/forms/CampaignForm.vue`, secțiunea „Ce apare public?" (liniile ~215–247).

**Stare actuală:** există deja `samePublicPhone` (checkbox „Folosește telefonul de contact și ca
telefon public", linia 232) iar la debifare apare câmpul `phonePublic` „Telefon public" (liniile
237–246). Deci capabilitatea există, dar e **greu de descoperit** și nu e legată vizual de medic.

**Ce faci:** îmbunătățește claritatea, nu rescrie logica.
1. Mută/încadrează câmpul „Telefon public" imediat sub câmpul medicului, în aceeași secțiune
   „Ce apare public?", ca să fie clar că publicul (inclusiv medicul) poate avea alt număr decât cel
   intern de contact.
2. Reformulează label-ul checkbox-ului ca să fie explicit: „Numărul public de contact este același cu
   telefonul de contact al organizației" și textul câmpului condițional: „Telefon public diferit
   (afișat pe pagina campaniei)".
3. Adaugă un mic helper text sub checkbox: „Debifează dacă vrei să afișezi un alt număr public (de ex.
   al medicului) decât telefonul intern al organizației."
4. Verifică validarea existentă (liniile ~472–475) și maparea la submit (liniile ~521–523, 580) — nu
   le strica; numărul public corect e deja calculat din `samePublicPhone`.

> Dacă produsul chiar vrea un câmp **separat de contact pentru medic** (distinct de „telefon public"),
> clarifică cu owner-ul înainte: ar însemna câmp nou + schimbare de payload backend
> (`PublicCampaign`). Default-ul acestui task este doar claritate UI peste câmpul existent.

**Accept:** la debifarea opțiunii apare un câmp de telefon public, plasat lângă medic, cu label și
helper clare. Submit-ul trimite numărul public corect (egal cu contactul dacă e bifat, altfel cel
introdus). `npm run typecheck` trece.

---

## T10 — Buton „înapoi sus" pe orice pagină ✅ DONE

**Status:** implementat și verificat în browser. Creat `app/components/layout/BackToTop.vue` (buton
`position: fixed` dreapta-jos, apare după `y > 600` via `useWindowScroll` din `@vueuse/core`, iconiță
`ArrowUp`, `aria-label="Înapoi sus"`, fundal `--color-primary`, hover `--color-primary-hover`,
`border-radius: var(--radius-full)`, `z-index: 90` (sub toast/nav), tranziție fade+slide care respectă
`prefers-reduced-motion`). Click → `window.scrollTo({ top: 0, behavior: 'smooth' })` (fără `smooth`
când reduce-motion). Montat global în `app/layouts/default.vue` lângă `<UiToaster />` (deci apare pe
toate paginile publice). Verificat: butonul apare la scroll, scrolează sus la click și se ascunde.
Layout-ul `admin.vue` a fost lăsat fără buton (intern) — se poate adăuga ușor dacă owner-ul vrea.

Detaliile de mai jos rămân ca referință a planului inițial.

**Pas 1 — componentă.** Creează `app/components/layout/BackToTop.vue`:
- Buton `position: fixed; right/bottom`, ascuns inițial, apare după `window.scrollY > 600`
  (listener `scroll` cu `{ passive: true }`, curățat în `onUnmounted`; ghidează-te după VueUse
  `useWindowScroll` din `@vueuse/nuxt` care e deja instalat).
- Click → `window.scrollTo({ top: 0, behavior: 'smooth' })` (respectă
  `prefers-reduced-motion`: dacă e `reduce`, fără `smooth`).
- Iconiță `ArrowUp` din lucide. `aria-label="Înapoi sus"`. Culori: fundal `var(--color-primary)`,
  iconiță albă; hover `var(--color-primary-hover)`. `border-radius: var(--radius-full)`,
  `z-index` peste conținut dar sub toast/nav. Pe mobil așază-l să nu acopere CTA-uri importante
  (ex. `bottom: var(--space-lg)`).

**Pas 2 — montare globală.** Adaugă `<LayoutBackToTop />` în `app/layouts/default.vue`
(lângă `<UiToaster />`). Verifică și `app/layouts/admin.vue` dacă vrei buton și în admin
(opțional; cere acceptul dacă nu ești sigur).

**Accept:** pe orice pagină publică, după ce derulezi, apare butonul; click-ul te duce sus lin;
nu apare cât timp ești în partea de sus; funcționează pe mobil și desktop.

---

## T11 — Pagină dedicată de donații / sprijin ✅ DONE

**Status:** implementat și verificat în browser. Creat `app/pages/sustine.vue` (hero navy cu iconiță
`Heart`, două carduri albe care se suprapun peste hero: „Donează prin transfer bancar" cu accent
portocaliu la stânga + „Date asociație"). Design inspirat de `build4paws.ro/contact`. IBAN-ul real
**RO55RNCB0068185806750001** e completat (afișat grupat „RO55 RNCB …", copiat fără spații), bancă
**Banca Comercială Română (BCR)** (dedus din codul RNCB), buton „Copiază IBAN" cu pattern
`navigator.clipboard` + toast. Datele legale (denumire, formă juridică, hotărâre, CIF, email) sunt
cele din task. Link „Susține-ne" adăugat în footer (coloana Navigare) și **banner pe homepage**
(strip navy între cardurile de jos și footer, CTA portocaliu → `/sustine`). `routeRules` în
`nuxt.config.ts`: `'/sustine': { prerender: true }`. (Nu am rulat typecheck — tooling blocat, vezi T13.)

Detaliile de mai jos rămân ca referință a planului inițial.

**Pas 1 — pagină.** Creează `app/pages/sustine.vue` (slug RO „susține"; alternativă `donatii.vue`
dacă preferi). Conținut și ton ca restul site-ului (hero navy + corp pe `--color-bg-muted`, carduri
albe `--radius-lg`). Mobile-first.

Secțiuni:
1. **Hero**: „Cum ne poți sprijini" + un paragraf scurt despre ce face asociația cu donațiile
   (campanii de sterilizare gratuită). Fără em dash.
2. **Card „Date asociație"** cu datele legale:
   - Denumire: **Asociația Build 4 Paws**
   - Formă juridică: **Asociație fără scop patrimonial (OG 26/2000)**
   - Hotărâre: **Nr. 217/2026, 21.01.2026, Judecătoria Alba Iulia**
   - CIF: **54236826**
   - Email oficial: **contact@build4paws.ro** (link `mailto:`)
3. **Card „Date pentru donații"**:
   - IBAN: `__TODO__` (de completat — owner-ul îl adaugă)
   - Bancă: `__TODO__`
   - Adaugă un buton „Copiază IBAN" (același pattern `navigator.clipboard` + toast ca la
     `confirmare.vue` `copyToken`). Marchează clar cu un comentariu `<!-- TODO: IBAN + bancă -->`
     până sunt furnizate.

SEO: `useSeoMeta({ title: 'Susține Build4Paws — sterilizări gratuite', description: '…' })`
(fără em dash în copy; folosește punct).

**Pas 2 — linkuri.**
- Footer `app/components/layout/Footer.vue`: adaugă în coloana „Navigare" (liniile 24–29) un
  `<NuxtLink to="/sustine">Susține-ne</NuxtLink>`.
- Opțional TopNav `app/components/layout/TopNav.vue` array `links` (liniile 35–41): adaugă
  `{ to: '/sustine', label: 'Susține-ne' }` dacă owner-ul vrea și în meniul principal.

**Pas 3 — SEO/prerender (opțional, recomandat).** În `nuxt.config.ts` `routeRules`, pagina e statică
(fără date backend), deci poți adăuga `'/sustine': { prerender: true }` lângă `/organizatori`.

**Accept:** `/sustine` afișează datele legale corecte, are placeholder vizibil pentru IBAN/bancă cu
buton de copiere, e linkată din footer, arată bine pe mobil, `npm run typecheck` trece.

---

## T12 — Numerotarea paragrafelor din Termeni și Condiții (INVESTIGHează)

**Status:** în repo **nu există** o pagină „Termeni și Condiții" (există doar
`app/pages/politica-de-confidentialitate.vue`, care are secțiuni numerotate `8.1…8.5`).

**Ce faci:**
1. Confirmă cu owner-ul / caută dacă pagina de Termeni e: (a) încă de creat, (b) în
   `politica-de-confidentialitate.vue`, sau (c) în alt loc.
2. Dacă **există**: auditează numerotarea titlurilor/paragrafelor (`<h2>`/`<h3>` și liste) pentru
   salturi sau duplicate și corectează secvența să fie continuă.
3. Dacă feedback-ul se referă de fapt la `politica-de-confidentialitate.vue`: verifică numerotarea
   secțiunilor (1, 2, 3 … și sub-secțiunile 8.1–8.5) să fie corectă și fără găuri.

**Accept:** numerotarea paragrafelor/secțiunilor pe pagina de Termeni (sau Politică, dacă aceea era
ținta) e continuă și corectă. Notează în PR ce pagină ai ajustat.

---

## T13 — Format dată lună/zi/an în formular campanii + „rest" stray ✅ DONE

**Status:** implementat opțiunea A. Adăugat prop opțional `hint?: string` în `app/components/ui/UiInput.vue`
(randat sub input doar când nu există eroare, legat prin `aria-describedby`) și pus
`hint="Format: zi/lună/an"` pe ambele câmpuri de dată din `CampaignForm.vue` (Data început / Data sfârșit).

**Investigația „rest" (stray US date):** nu există nicio dată afișată în format US în fluxul de organizator.
Toate datele randate trec prin `formatDate` / `formatDateRange` / `formatDateTime` din `app/utils/format.ts`
(toate RO): preview-ul (`CampaignCard` → `formatDateRange`), `confirmare-campanie.vue` (`formatDateTime`),
`organizator/[id].vue` (string-compare, fără afișare). Singurul loc unde apare `MM/DD/YYYY` este chiar
`<input type="date">`-ul nativ, al cărui format afișat urmează locale-ul browserului/OS, nu `lang="ro"`.
Hint-ul de format rezolvă confuzia fără picker custom. (Notă: nu am rulat `npm run typecheck` — tooling-ul
e momentan blocat și nu e prioritate în această etapă.)

**Context:** câmpurile de dată din `app/components/forms/CampaignForm.vue` (liniile ~116–138) sunt
`<UiInput type="date">` native. Formatul AFIȘAT al unui `<input type="date">` urmează **locale-ul
browserului/OS**, nu `lang`-ul paginii — de aceea poate apărea `MM/DD/YYYY` pe un browser setat pe
engleză. `<html lang="ro">` e deja setat în `nuxt.config.ts:12`, dar Chrome ignoră asta și folosește
locale-ul sistemului.

**Opțiuni (alege cu owner-ul):**
- **A (minim):** lasă input-ul nativ; nu e controlabil cross-browser. Adaugă un mic hint sub câmp:
  „Format: zi/lună/an" ca să reduci confuzia. (Datele AFIȘATE în restul aplicației sunt deja RO prin
  `formatDate` din `app/utils/format.ts`.)
- **B (robust):** înlocuiește input-ul nativ cu un date picker custom care afișează garantat
  `zi/lună/an`. Mai mult efort; cere acceptul înainte.

**Despre „cred ca e un rest de undeva (din formularul de organizator)":** feedback-ul sugerează un
element/text rămas (stray) care arată o dată în format US. Caută în fluxul organizator:
`CampaignForm.vue`, pasul de preview (step 2), `app/pages/confirmare-campanie.vue`,
`app/pages/organizator/[id].vue`. Verifică dacă vreo dată e randată cu `toLocaleDateString()` fără
locale RO sau cu un `new Date()` în loc de `formatDate`. Dacă găsești, schimbă pe `formatDate`
(component-wise, fără shift de timezone).

**Accept:** ori hint vizibil de format pe câmpurile de dată (opțiunea A), ori picker RO (opțiunea B);
plus orice dată în format US găsită în fluxul organizator e trecută pe `formatDate`. Documentează în
PR ce ai ales și ce ai găsit pentru „rest".

---

## Ordinea recomandată de lucru

1. ~~Quick wins de copy: **T8, T2, T1**~~ ✅ făcute. Rămâne **T5** (tot copy/clarificare, fără risc).
2. **T4** (em dash) — sweep global, fă-l într-un commit separat.
3. **T3, T6, T7** — hartă + iconițe (verifică vizual pe `/harta` și `/campanii`).
4. **T10, T11** — componente/pagini noi.
5. **T9** — formular organizator (clarificare UI).
6. **T12, T13** — investigații; deschide întrebări către owner unde e nevoie.

La final: `npm run typecheck`. Nu există test runner — verifică manual în browser paginile atinse
(`/`, `/confirmare`, `/campanii`, `/harta`, `/organizatori`, `/sustine`) pe viewport mobil și desktop.

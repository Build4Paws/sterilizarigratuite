<template>
  <div class="rep">
    <p class="rep__intro">
      Alege un set de date, ajustează filtrele și descarcă un export CSV — se
      deschide direct în Excel sau Google Sheets.
    </p>

    <!-- Step 1 — pick the dataset -->
    <section class="rep__section">
      <h2 class="rep__h2"><span class="rep__step">1</span> Ce vrei să exporți?</h2>
      <div class="rep__cards">
        <button
          v-for="r in reports"
          :key="r.type"
          type="button"
          :class="['rcard', { 'rcard--active': reportType === r.type }]"
          :aria-pressed="reportType === r.type"
          @click="reportType = r.type"
        >
          <span class="rcard__icon"><component :is="r.icon" :size="20" /></span>
          <span class="rcard__body">
            <span class="rcard__title">{{ r.title }}</span>
            <span class="rcard__desc">{{ r.desc }}</span>
            <span class="rcard__cols">{{ r.columns }}</span>
          </span>
          <Check v-if="reportType === r.type" :size="18" class="rcard__check" />
        </button>
      </div>
      <UiAlert v-if="reportType === 'citizens'" variant="info">
        Conține date personale (nume, județ, localitate). Generarea este
        înregistrată în jurnalul de audit; contactele directe nu sunt incluse.
      </UiAlert>
    </section>

    <!-- Step 2 — filters -->
    <section class="rep__section">
      <h2 class="rep__h2"><span class="rep__step">2</span> Filtrează</h2>
      <div class="rep__panel">
        <div class="rep__field">
          <span class="rep__label">Perioadă</span>
          <div class="rep__presets">
            <button
              v-for="p in presets"
              :key="p.key"
              type="button"
              :class="['chip', { 'chip--active': activePreset === p.key }]"
              @click="applyPreset(p.key)"
            >{{ p.label }}</button>
          </div>
          <div class="rep__dates">
            <UiInput id="rep-from" v-model="from" label="De la" type="date" />
            <UiInput id="rep-to" v-model="to" label="Până la" type="date" />
          </div>
        </div>

        <div class="rep__field-row">
          <UiSelect id="rep-county" v-model="county" label="Județ" :options="countyOptions" />
          <UiSelect
            v-if="statusOptions.length"
            id="rep-status"
            v-model="status"
            label="Status"
            :options="statusOptions"
          />
        </div>

        <UiAlert v-if="dateError" variant="error">{{ dateError }}</UiAlert>
      </div>
    </section>

    <!-- Step 3 — summary + download -->
    <div class="rep__bar">
      <p class="rep__summary">
        <span class="rep__summary-label">Vei exporta</span>
        <strong>{{ activeReport.title }}</strong>
        <span class="rep__chiplet">{{ periodLabel }}</span>
        <span v-if="countyLabel" class="rep__chiplet">{{ countyLabel }}</span>
        <span v-if="statusLabel" class="rep__chiplet">{{ statusLabel }}</span>
      </p>
      <UiButton type="button" variant="primary" :loading="loading" @click="download">
        <Download :size="18" /> Descarcă CSV
      </UiButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import { CalendarCheck, Users, Building2, ScrollText, Download, Check } from 'lucide-vue-next'
import type { ReportType } from '~/types'

definePageMeta({ layout: 'admin', middleware: 'admin-auth' })
useSeoMeta({ title: 'Admin — Rapoarte', robots: 'noindex, nofollow' })

const toast = useToast()
const { counties, init } = useLocationData()
await init()

const reports = [
  { type: 'campaigns' as const, icon: CalendarCheck, title: 'Campanii', desc: 'Toate submisiile, cu status și recenzent.', columns: 'Organizație · localitate · perioadă · status · recenzie' },
  { type: 'citizens' as const, icon: Users, title: 'Cetățeni / înscrieri', desc: 'Înscrieri pe județ, localitate și status.', columns: 'Nume · județ · localitate · canale · dată' },
  { type: 'organizers' as const, icon: Building2, title: 'Organizatori', desc: 'Organizatori cu număr de campanii.', columns: 'Nume · contact · nr. campanii · dată' },
  { type: 'activity' as const, icon: ScrollText, title: 'Activitate', desc: 'Acțiuni din jurnalul de audit.', columns: 'Dată · operator · acțiune · entitate' },
]

const reportType = ref<ReportType>('campaigns')
const activeReport = computed(() => reports.find(r => r.type === reportType.value)!)

const from = ref('')
const to = ref('')
const county = ref('')
const status = ref('')
const loading = ref(false)

// --- Date presets ---
const presets = [
  { key: 'all', label: 'Tot' },
  { key: 'today', label: 'Astăzi' },
  { key: '7d', label: '7 zile' },
  { key: '30d', label: '30 zile' },
  { key: 'month', label: 'Luna aceasta' },
  { key: 'year', label: 'Anul acesta' },
] as const
type PresetKey = typeof presets[number]['key']
const activePreset = ref<PresetKey | ''>('all')

function iso(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

let applyingPreset = false
function applyPreset(key: PresetKey) {
  applyingPreset = true
  const now = new Date()
  const today = iso(now)
  if (key === 'all') { from.value = ''; to.value = '' }
  else if (key === 'today') { from.value = today; to.value = today }
  else if (key === '7d') { const d = new Date(now); d.setDate(d.getDate() - 6); from.value = iso(d); to.value = today }
  else if (key === '30d') { const d = new Date(now); d.setDate(d.getDate() - 29); from.value = iso(d); to.value = today }
  else if (key === 'month') { from.value = iso(new Date(now.getFullYear(), now.getMonth(), 1)); to.value = today }
  else if (key === 'year') { from.value = iso(new Date(now.getFullYear(), 0, 1)); to.value = today }
  activePreset.value = key
  nextTick(() => { applyingPreset = false })
}
// Manual edits clear the active preset highlight.
watch([from, to], () => { if (!applyingPreset) activePreset.value = '' })

// --- County + status filters ---
const countyOptions = computed(() => [{ value: '', label: 'Toate județele' }, ...counties.value])

const CAMPAIGN_STATUSES = [
  { value: '', label: 'Toate statusurile' },
  { value: 'pending', label: 'În așteptare' },
  { value: 'approved', label: 'Aprobate' },
  { value: 'rejected', label: 'Respinse' },
  { value: 'cancelled', label: 'Anulate' },
  { value: 'finished', label: 'Finalizate' },
]
const CITIZEN_STATUSES = [
  { value: '', label: 'Toate statusurile' },
  { value: 'active', label: 'Active' },
  { value: 'pending_confirm', label: 'Neconfirmate' },
  { value: 'unsubscribed', label: 'Dezabonate' },
]
const statusOptions = computed(() => {
  if (reportType.value === 'campaigns') return CAMPAIGN_STATUSES
  if (reportType.value === 'citizens') return CITIZEN_STATUSES
  return []
})
watch(reportType, () => { if (!statusOptions.value.length) status.value = '' })

// --- Summary labels ---
const dateError = computed(() =>
  from.value && to.value && from.value > to.value ? 'Data de început este după data de sfârșit.' : '')

const periodLabel = computed(() => {
  const preset = presets.find(p => p.key === activePreset.value)
  if (preset && preset.key !== 'all') return preset.label.toLowerCase()
  if (from.value && to.value) return `${from.value} → ${to.value}`
  if (from.value) return `din ${from.value}`
  if (to.value) return `până la ${to.value}`
  return 'toată perioada'
})
const countyLabel = computed(() => counties.value.find(c => c.value === county.value)?.label ?? '')
const statusLabel = computed(() => statusOptions.value.find(s => s.value === status.value && s.value)?.label ?? '')

/** Filename from a `Content-Disposition` header. */
function filenameFrom(disposition: string | null, fallback: string): string {
  const match = disposition?.match(/filename\*?=(?:UTF-8'')?"?([^"';]+)"?/i)
  return match?.[1] ? decodeURIComponent(match[1]) : fallback
}

const REPORT_ERRORS: Record<string, string> = {
  unauthorized: 'Sesiune expirată. Conectează-te din nou.',
  not_found: 'Tip de raport necunoscut.',
  rate_limited: 'Prea multe cereri. Așteaptă un moment.',
  server_error: 'Eroare de server. Încearcă din nou.',
}

async function download() {
  if (dateError.value) return
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (from.value) params.set('from', from.value)
    if (to.value) params.set('to', to.value)
    if (county.value) params.set('county', county.value)
    if (status.value) params.set('status', status.value)
    const qs = params.toString()

    // Same-origin fetch — the httpOnly session cookie rides along automatically.
    const res = await fetch(`/api/admin/reports/${reportType.value}${qs ? `?${qs}` : ''}`)
    if (!res.ok) {
      let code = 'server_error'
      try { code = (await res.json())?.data?.error ?? code } catch { /* non-JSON error */ }
      toast.error(REPORT_ERRORS[code] ?? 'Nu am putut genera raportul. Încearcă din nou.')
      return
    }

    const blob = await res.blob()
    const today = new Date().toISOString().slice(0, 10)
    const name = filenameFrom(res.headers.get('content-disposition'), `raport-${reportType.value}-${today}.csv`)

    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = name
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
    toast.success('Raport generat.')
  } catch {
    toast.error('Nu am putut genera raportul. Verifică conexiunea și încearcă din nou.')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.rep { display: flex; flex-direction: column; gap: var(--space-xl); max-width: 760px; }
.rep__intro { font-size: var(--font-size-sm); color: var(--color-text-muted); margin: 0; max-width: 60ch; }

.rep__section { display: flex; flex-direction: column; gap: var(--space-md); }
.rep__h2 {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-family: var(--font-heading, var(--font-body));
  font-size: var(--font-size-base);
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
}
.rep__step {
  width: 1.5rem;
  height: 1.5rem;
  border-radius: var(--radius-full);
  background: var(--color-primary);
  color: var(--color-text-light);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-sm);
  font-weight: 800;
}

/* --- Report cards --- */
.rep__cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-md);
}
.rcard {
  position: relative;
  display: flex;
  gap: var(--space-sm);
  text-align: left;
  padding: var(--space-md);
  background: var(--color-bg);
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: border-color 0.16s ease, box-shadow 0.16s ease, transform 0.16s ease;
}
.rcard:hover { border-color: var(--color-primary); transform: translateY(-2px); }
.rcard--active {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(249, 89, 5, 0.14);
}
.rcard__icon {
  flex-shrink: 0;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: var(--radius-md);
  background: var(--color-slate-100);
  color: var(--color-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.rcard--active .rcard__icon { background: var(--color-accent); color: var(--color-text-light); }
.rcard__body { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.rcard__title { font-weight: 700; color: var(--color-text); }
.rcard__desc { font-size: var(--font-size-sm); color: var(--color-text-muted); }
.rcard__cols {
  font-size: 0.6875rem;
  color: var(--color-slate-600);
  margin-top: var(--space-xs);
  opacity: 0.85;
}
.rcard__check { position: absolute; top: var(--space-sm); right: var(--space-sm); color: var(--color-accent); }

/* --- Filters panel --- */
.rep__panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
  padding: var(--space-lg);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}
.rep__field { display: flex; flex-direction: column; gap: var(--space-sm); }
.rep__label { font-size: var(--font-size-sm); font-weight: 600; color: var(--color-text); }
.rep__presets { display: flex; flex-wrap: wrap; gap: var(--space-xs); }
.chip {
  padding: 0.375rem 0.75rem;
  border-radius: var(--radius-full);
  border: 1px solid var(--color-border);
  background: var(--color-bg);
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.14s ease;
}
.chip:hover { border-color: var(--color-primary); color: var(--color-primary); }
.chip--active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-text-light);
}
.rep__dates, .rep__field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-md);
}

/* --- Summary bar --- */
.rep__bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
  padding: var(--space-md) var(--space-lg);
  background: var(--color-slate-50);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  position: sticky;
  bottom: var(--space-md);
}
.rep__summary {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-xs);
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text);
}
.rep__summary-label { color: var(--color-text-muted); }
.rep__chiplet {
  padding: 0.125rem 0.5rem;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

@media (max-width: 600px) {
  .rep__cards { grid-template-columns: 1fr; }
  .rep__dates, .rep__field-row { grid-template-columns: 1fr; }
}
@media (prefers-reduced-motion: reduce) {
  .rcard:hover { transform: none; }
}
</style>

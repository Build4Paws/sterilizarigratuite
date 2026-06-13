<template>
  <div class="page">
    <header class="page__head">
      <div>
        <h1 class="page__title">SMS — messengeros</h1>
        <p class="page__note">Contacte, liste și statistici, direct din admin.</p>
      </div>
    </header>

    <!-- ───────── Dashboard stats (last 30d) ───────── -->
    <section class="stats">
      <article v-for="s in statCards" :key="s.label" class="stat">
        <span class="stat__value">{{ s.value }}</span>
        <span class="stat__label">{{ s.label }}</span>
        <span v-if="s.delta != null" :class="['stat__delta', { up: s.delta > 0 }]">
          {{ s.delta > 0 ? '+' : '' }}{{ s.delta }} vs. perioada anterioară
        </span>
      </article>
    </section>

    <nav class="tabs">
      <button v-for="t in tabs" :key="t.key" type="button"
              :class="['tabs__tab', { 'tabs__tab--active': tab === t.key }]" @click="tab = t.key">{{ t.label }}</button>
    </nav>

    <!-- ═══════════════════ Contacts ═══════════════════ -->
    <section v-if="tab === 'contacts'" class="panel">
      <div class="toolbar">
        <div class="search">
          <Search :size="16" class="search__icon" />
          <input v-model="cq" type="search" class="search__input" placeholder="Caută în pagina curentă…" aria-label="Caută" />
        </div>
        <select v-model="cStatus" class="select" aria-label="Filtrează după status">
          <option value="">Toate statusurile</option>
          <option value="sub">Abonați</option>
          <option value="unsub">Dezabonați</option>
          <option value="none">Fără telefon</option>
        </select>
        <span class="toolbar__count">{{ contactsTotal }} contacte</span>
        <UiButton variant="ghost" :loading="contactsPending" @click="refreshContacts()"><RefreshCw :size="15" /> Reîncarcă</UiButton>
      </div>

      <UiAlert v-if="contactsError" variant="error">{{ extractApiError(contactsError) }}</UiAlert>

      <AdminTable
        :columns="['Nume', 'Telefon', 'Email', 'Status', 'Acțiuni']"
        :empty="!contactsPending && filteredContacts.length === 0"
        :empty-text="contactsPending ? 'Se încarcă…' : 'Niciun contact.'"
      >
        <tr v-for="c in filteredContacts" :key="c.__cid">
          <td>{{ contactName(c) }}</td>
          <td>{{ c.phone ? formatPhone(String(c.phone)) : '—' }}</td>
          <td>{{ c.email || '—' }}</td>
          <td><span :class="['pill', `pill--${statusTone(c)}`]">{{ statusLabel(c) }}</span></td>
          <td class="actions">
            <form v-if="mode.id === c.__cid && (mode.kind === 'edit' || mode.kind === 'add')" class="inline" @submit.prevent="savePhone(c)">
              <input v-model="phoneInput" type="tel" class="inline__input" placeholder="+40…" />
              <button type="submit" class="link" :disabled="busy">Salvează</button>
              <button type="button" class="link link--muted" :disabled="busy" @click="closeMode">Anulează</button>
            </form>
            <div v-else-if="mode.id === c.__cid && mode.kind === 'delete'" class="inline">
              <span class="inline__q">Ștergi telefonul?</span>
              <button type="button" class="link link--danger" :disabled="busy" @click="doDelete(c)">Da</button>
              <button type="button" class="link link--muted" :disabled="busy" @click="closeMode">Nu</button>
            </div>
            <div v-else class="inline">
              <template v-if="c.__pid">
                <button type="button" class="link" @click="openEdit(c)">Telefon</button>
                <button v-if="c.phoneUnsubscribed" type="button" class="link" :disabled="busy" @click="toggleSub(c, true)">Abonează</button>
                <button v-else type="button" class="link" :disabled="busy" @click="toggleSub(c, false)">Dezabonează</button>
                <button type="button" class="link link--danger" @click="mode = { id: c.__cid, kind: 'delete' }">Șterge</button>
              </template>
              <button v-else type="button" class="link" @click="openAdd(c)">Adaugă telefon</button>
            </div>
          </td>
        </tr>
      </AdminTable>

      <div class="pager">
        <UiButton variant="ghost" :disabled="cPage <= 1 || contactsPending" @click="cPage--">← Anterior</UiButton>
        <span class="pager__n">Pagina {{ cPage }}<template v-if="contactPages"> / {{ contactPages }}</template></span>
        <UiButton variant="ghost" :disabled="contactsPending || (contactPages ? cPage >= contactPages : contactRows.length < cLimit)" @click="cPage++">Următor →</UiButton>
      </div>
    </section>

    <!-- ═══════════════════ Lists (grouped by county) ═══════════════════ -->
    <section v-else class="panel">
      <div class="toolbar">
        <select v-model="county" class="select" aria-label="Județ">
          <option value="">Alege un județ…</option>
          <option v-for="c in counties" :key="c.value" :value="c.value">{{ c.label }} ({{ c.value }})</option>
        </select>
        <div class="search">
          <Search :size="16" class="search__icon" />
          <input v-model="lq" type="search" class="search__input" placeholder="Caută listă după nume…" aria-label="Caută listă" />
        </div>
        <span v-if="county || committedLq" class="toolbar__count">{{ lists.length }} liste</span>
      </div>

      <UiAlert v-if="listsError" variant="error">{{ extractApiError(listsError) }}</UiAlert>
      <p v-if="!county && !committedLq" class="empty">Alege un județ (sau caută) pentru a vedea listele de distribuție.</p>
      <p v-else-if="listsPending" class="empty">Se încarcă…</p>

      <AdminTable
        v-else
        :columns="['Listă', 'Contacte', 'Creat', '']"
        :empty="lists.length === 0"
        empty-text="Nicio listă pentru acest filtru."
      >
        <tr v-for="l in lists" :key="l.id" class="is-clickable" :class="{ 'is-active': selected?.id === l.id }" @click="openList(l)">
          <td>{{ l.name }}</td>
          <td>{{ l.contactCount ?? '—' }}</td>
          <td class="nowrap">{{ fmtDate(l.createdAt) }}</td>
          <td><span class="link">Detalii →</span></td>
        </tr>
      </AdminTable>

      <!-- list detail drawer -->
      <section v-if="selected" class="detail">
        <header class="detail__head">
          <h2 class="detail__title">{{ selected.name }}</h2>
          <button type="button" class="link link--muted" @click="selected = null">Închide ✕</button>
        </header>
        <UiAlert v-if="detailError" variant="error">{{ extractApiError(detailError) }}</UiAlert>
        <p v-else-if="detailPending" class="empty">Se încarcă…</p>
        <template v-else>
          <div class="stats">
            <article class="stat"><span class="stat__value">{{ phoneStat('total') }}</span><span class="stat__label">Telefoane</span></article>
            <article class="stat"><span class="stat__value">{{ phoneStat('subscribed') }}</span><span class="stat__label">Abonate</span></article>
            <article class="stat"><span class="stat__value">{{ phoneStat('unsubscribed') }}</span><span class="stat__label">Dezabonate</span></article>
          </div>
          <AdminTable
            :columns="['Nume', 'Telefon', 'Email']"
            :empty="members.length === 0"
            empty-text="Niciun contact în această listă."
          >
            <tr v-for="(m, mi) in members" :key="String(m.id ?? mi)">
              <td>{{ contactName({ ...m, __cid: '' }) }}</td>
              <td>{{ m.phone ? formatPhone(String(m.phone)) : '—' }}</td>
              <td>{{ m.email || '—' }}</td>
            </tr>
          </AdminTable>
          <div class="pager">
            <UiButton variant="ghost" :disabled="mPage <= 1 || detailPending" @click="mPage--">← Anterior</UiButton>
            <span class="pager__n">Pagina {{ mPage }}</span>
            <UiButton variant="ghost" :disabled="detailPending || members.length < mLimit" @click="mPage++">Următor →</UiButton>
          </div>
        </template>
      </section>
    </section>
  </div>
</template>

<script setup lang="ts">
import { Search, RefreshCw } from 'lucide-vue-next'

definePageMeta({ layout: 'admin', middleware: 'admin-auth' })
useSeoMeta({ title: 'Admin — SMS (messengeros)', robots: 'noindex, nofollow' })

const toast = useToast()
const { counties, init: initCounties } = useLocationData()
await initCounties()

type Tab = 'contacts' | 'lists'
const tabs = [{ key: 'contacts' as const, label: 'Contacte' }, { key: 'lists' as const, label: 'Liste de distribuție' }]
const tab = ref<Tab>('contacts')

type Row = Record<string, unknown>
const unwrap = (d: unknown): Row[] => {
  if (Array.isArray(d)) return d as Row[]
  const o = (d ?? {}) as Record<string, unknown>
  return (Array.isArray(o.data) ? o.data : []) as Row[]
}
const totalOf = (d: unknown): number => Number((d as { total?: number })?.total ?? 0)

function contactName(c: Row): string {
  if (c.name) return String(c.name)
  const full = [c.firstName ?? c.first_name, c.lastName ?? c.last_name].filter(Boolean).join(' ')
  return full || '—'
}
function statusLabel(c: Row): string {
  if (!c.phone && !c.phoneNumberId) return 'Fără telefon'
  if (c.phoneSuppressed) return 'Suprimat'
  return c.phoneUnsubscribed ? 'Dezabonat' : 'Abonat'
}
function statusTone(c: Row): string {
  if (!c.phone && !c.phoneNumberId) return 'neutral'
  if (c.phoneSuppressed) return 'danger'
  return c.phoneUnsubscribed ? 'muted' : 'ok'
}
function fmtDate(v: unknown): string {
  if (!v) return '—'
  const d = new Date(String(v))
  return Number.isNaN(d.getTime()) ? String(v) : d.toLocaleDateString('ro-RO')
}

// ── Contacts ──
const cLimit = 20
const cPage = ref(1)
const cq = ref('')
const cStatus = ref('')
const { data: contactsData, pending: contactsPending, error: contactsError, refresh: refreshContacts } =
  await useFetch('/api/admin/messengeros/contacts', { query: { page: cPage, limit: cLimit }, server: false, lazy: true, key: 'mgo-contacts' })

const contactRows = computed<(Row & { __cid: string; __pid: string })[]>(() =>
  unwrap(contactsData.value).map(c => ({ ...c, __cid: String(c.id ?? ''), __pid: c.phoneNumberId ? String(c.phoneNumberId) : '' })))
const contactsTotal = computed(() => totalOf(contactsData.value) || contactRows.value.length)
const contactPages = computed(() => (totalOf(contactsData.value) ? Math.ceil(totalOf(contactsData.value) / cLimit) : 0))

const filteredContacts = computed(() => {
  let rows = contactRows.value
  const needle = cq.value.trim().toLowerCase()
  if (needle) rows = rows.filter(c => Object.values(c).some(v => v != null && String(v).toLowerCase().includes(needle)))
  if (cStatus.value === 'sub') rows = rows.filter(c => (c.phone || c.phoneNumberId) && !c.phoneUnsubscribed)
  else if (cStatus.value === 'unsub') rows = rows.filter(c => c.phoneUnsubscribed)
  else if (cStatus.value === 'none') rows = rows.filter(c => !c.phone && !c.phoneNumberId)
  return rows
})

// contact phone actions
const mode = ref<{ id: string; kind: '' | 'edit' | 'add' | 'delete' }>({ id: '', kind: '' })
const phoneInput = ref('')
const busy = ref(false)
function closeMode() { mode.value = { id: '', kind: '' } }
function openEdit(c: Row & { __cid: string }) { phoneInput.value = String(c.phone ?? ''); mode.value = { id: c.__cid, kind: 'edit' } }
function openAdd(c: Row & { __cid: string }) { phoneInput.value = ''; mode.value = { id: c.__cid, kind: 'add' } }

async function savePhone(c: Row & { __cid: string; __pid: string }) {
  const v = phoneInput.value.trim()
  if (!v) return
  busy.value = true
  try {
    if (mode.value.kind === 'add') await $fetch(`/api/admin/messengeros/contacts/${c.__cid}/phone`, { method: 'POST', body: { phone: v } })
    else await $fetch(`/api/admin/messengeros/contacts/phone/${c.__pid}`, { method: 'PUT', body: { value: v } })
    toast.success('Telefon salvat.'); closeMode(); await refreshContacts()
  } catch (err) { toast.error(extractApiError(err)) } finally { busy.value = false }
}
async function toggleSub(c: Row & { __pid: string }, subscribe: boolean) {
  busy.value = true
  try {
    await $fetch(`/api/admin/messengeros/contacts/phone/${c.__pid}/${subscribe ? 'subscribe' : 'unsubscribe'}`, { method: 'POST' })
    toast.success(subscribe ? 'Abonat.' : 'Dezabonat.'); await refreshContacts()
  } catch (err) { toast.error(extractApiError(err)) } finally { busy.value = false }
}
async function doDelete(c: Row & { __pid: string }) {
  busy.value = true
  try {
    await $fetch(`/api/admin/messengeros/contacts/phone/${c.__pid}`, { method: 'DELETE' })
    toast.success('Telefon șters.'); closeMode(); await refreshContacts()
  } catch (err) { toast.error(extractApiError(err)) } finally { busy.value = false }
}

// ── Lists (county-grouped) ──
const county = ref('')
const lq = ref('')
const committedLq = ref('')
let lqTimer: ReturnType<typeof setTimeout> | undefined
watch(lq, () => { clearTimeout(lqTimer); lqTimer = setTimeout(() => { committedLq.value = lq.value.trim() }, 350) })

const { data: listsData, pending: listsPending, error: listsError } =
  await useFetch('/api/admin/messengeros/distribution-lists', { query: { county, q: committedLq }, server: false, lazy: true, key: 'mgo-lists' })
const lists = computed<{ id: number; name: string; contactCount?: number; createdAt?: string }[]>(() => unwrap(listsData.value) as never)

// list detail + members
const selected = ref<{ id: number; name: string } | null>(null)
const mLimit = 20
const mPage = ref(1)
const listDetail = ref<Row | null>(null)
const members = ref<Row[]>([])
const detailPending = ref(false)
const detailError = ref<unknown>(null)

function openList(l: { id: number; name: string }) { selected.value = { id: l.id, name: l.name }; mPage.value = 1; loadDetail() }
async function loadDetail() {
  if (!selected.value) return
  detailPending.value = true; detailError.value = null
  try {
    const [d, m] = await Promise.all([
      $fetch<{ data?: Row }>(`/api/admin/messengeros/distribution-lists/${selected.value.id}`),
      $fetch(`/api/admin/messengeros/distribution-lists/${selected.value.id}/contacts`, { query: { page: mPage.value, limit: mLimit } }),
    ])
    listDetail.value = d?.data ?? (d as Row)
    members.value = unwrap(m)
  } catch (err) { detailError.value = err } finally { detailPending.value = false }
}
watch(mPage, loadDetail)
function phoneStat(k: 'total' | 'subscribed' | 'unsubscribed'): number {
  const stats = (listDetail.value?.stats ?? {}) as { phone?: Record<string, number> }
  return stats.phone?.[k] ?? 0
}

// ── Dashboard stats ──
const { data: statsData } = await useFetch<Record<string, number>>('/api/admin/messengeros/dashboard/stats', { query: { period: '30d' }, server: false, lazy: true, key: 'mgo-stats' })
const statCards = computed(() => {
  const s = statsData.value ?? {}
  return [
    { label: 'Contacte', value: s.totalContacts ?? '—', delta: null as number | null },
    { label: `Noi (${s.days ?? 30}z)`, value: s.newContacts ?? '—', delta: null },
    { label: 'SMS trimise', value: s.smsSent ?? '—', delta: s.smsSent != null && s.smsSentPrev != null ? s.smsSent - s.smsSentPrev : null },
    { label: 'Email trimise', value: s.emailSent ?? '—', delta: s.emailSent != null && s.emailSentPrev != null ? s.emailSent - s.emailSentPrev : null },
  ]
})
</script>

<style scoped>
.page { display: flex; flex-direction: column; gap: var(--space-md); max-width: 1040px; }
.page__title { font-family: var(--font-heading, var(--font-body)); font-size: var(--font-size-lg); color: var(--color-text); margin: 0; }
.page__note { font-size: var(--font-size-sm); color: var(--color-text-muted); margin: 0.25rem 0 0; }

.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: var(--space-md); }
.stat { display: flex; flex-direction: column; gap: 2px; padding: var(--space-md); background: var(--color-bg); border: 1px solid var(--color-border); border-radius: var(--radius-md); }
.stat__value { font-family: var(--font-heading, var(--font-body)); font-size: 1.75rem; font-weight: 800; color: var(--color-primary); line-height: 1; }
.stat__label { font-size: var(--font-size-sm); color: var(--color-text-muted); }
.stat__delta { font-size: 0.7rem; color: var(--color-text-muted); }
.stat__delta.up { color: var(--color-success, #10b981); }

.tabs { display: flex; flex-wrap: wrap; gap: var(--space-xs); }
.tabs__tab { padding: 0.375rem 0.75rem; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-bg); font-size: var(--font-size-sm); font-weight: 600; color: var(--color-text-muted); cursor: pointer; }
.tabs__tab--active { background: var(--color-primary); color: var(--color-text-light); border-color: var(--color-primary); }

.panel { display: flex; flex-direction: column; gap: var(--space-md); }
.toolbar { display: flex; align-items: center; gap: var(--space-md); flex-wrap: wrap; }
.search { position: relative; flex: 1 1 240px; min-width: 180px; }
.search__icon { position: absolute; left: 0.7rem; top: 50%; transform: translateY(-50%); color: var(--color-text-muted); pointer-events: none; }
.search__input, .select {
  width: 100%; font-family: var(--font-body); font-size: var(--font-size-sm);
  padding: 0.5rem 0.75rem; border: 1px solid var(--color-border); border-radius: var(--radius-md);
  background: var(--color-bg); color: var(--color-text);
}
.search__input { padding-left: 2.25rem; }
.select { width: auto; min-width: 180px; cursor: pointer; }
.toolbar__count { font-size: var(--font-size-sm); color: var(--color-text-muted); margin-left: auto; }

.pill { display: inline-block; padding: 0.125rem 0.5rem; border-radius: var(--radius-full); font-size: 0.75rem; font-weight: 600; }
.pill--ok { background: #ecfdf5; color: #065f46; }
.pill--danger { background: #fef2f2; color: #991b1b; }
.pill--muted { background: var(--color-slate-50); color: var(--color-slate-500, #64748b); }
.pill--neutral { background: var(--color-slate-100); color: var(--color-text-muted); }

.inline { display: flex; align-items: center; gap: var(--space-sm); flex-wrap: wrap; }
.inline__q { font-size: var(--font-size-sm); color: var(--color-text); }
.inline__input { width: 9.5rem; font-size: var(--font-size-sm); padding: 0.3rem 0.5rem; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-bg); color: var(--color-text); }
.link { background: none; border: 0; padding: 0; cursor: pointer; color: var(--color-primary); font-weight: 600; font-size: var(--font-size-sm); white-space: nowrap; }
.link:hover { text-decoration: underline; }
.link:disabled { opacity: 0.5; cursor: not-allowed; }
.link--danger { color: var(--color-error); }
.link--muted { color: var(--color-text-muted); }

.pager { display: flex; align-items: center; gap: var(--space-md); }
.pager__n { font-size: var(--font-size-sm); color: var(--color-text-muted); }
.nowrap { white-space: nowrap; }
.empty { color: var(--color-text-muted); }

.detail { display: flex; flex-direction: column; gap: var(--space-md); padding: var(--space-lg); background: var(--color-slate-50); border: 1px solid var(--color-border); border-radius: var(--radius-md); }
.detail__head { display: flex; justify-content: space-between; align-items: center; gap: var(--space-md); }
.detail__title { font-size: var(--font-size-base); color: var(--color-text); margin: 0; font-weight: 700; }
</style>

<template>
  <div class="page">
    <NuxtLink to="/admin/cetateni" class="back">← Înapoi la cetățeni</NuxtLink>

    <UiAlert v-if="error" variant="error">{{ extractApiError(error) }}</UiAlert>

    <div v-if="z" class="detail">
      <header class="detail__head">
        <h1 class="detail__title">{{ z.name }}</h1>
        <AdminStatusBadge :status="z.status" />
      </header>

      <section class="card">
        <div class="card__titlerow">
          <h2 class="card__title">Date de contact</h2>
          <button type="button" class="reveal" @click="revealed = !revealed">
            {{ revealed ? 'Ascunde' : 'Arată' }}
          </button>
        </div>
        <dl class="kv">
          <div><dt>Telefon</dt><dd>{{ z.phone ? (revealed ? formatPhone(z.phone) : mask(z.phone)) : '–' }}</dd></div>
          <div><dt>Email</dt><dd>{{ z.email ? (revealed ? z.email : maskEmail(z.email)) : '–' }}</dd></div>
          <div><dt>Localitate</dt><dd>{{ z.locality }}, {{ z.countyName }}</dd></div>
          <div><dt>Animale</dt><dd>{{ animalsText }}</dd></div>
          <div><dt>Consimțământ GDPR</dt><dd>{{ formatDateTime(z.gdprConsentAt) }}</dd></div>
          <div><dt>Înscris</dt><dd>{{ formatDateTime(z.createdAt) }}</dd></div>
        </dl>
        <p v-if="z.notes" class="notes">{{ z.notes }}</p>
      </section>

      <section v-if="z.status !== 'deleted'" class="card">
        <h2 class="card__title">Acțiuni</h2>
        <div class="actions__row">
          <UiButton
            v-if="z.status !== 'unsubscribed'"
            variant="ghost"
            :loading="busy === 'unsub'"
            @click="unsubscribe"
          >
            Dezabonează
          </UiButton>
          <UiButton variant="ghost" :disabled="!!busy" @click="erasing = !erasing">
            Șterge definitiv (GDPR)
          </UiButton>
        </div>

        <form v-if="erasing" class="erase" @submit.prevent="erase">
          <UiAlert variant="error">
            Ștergerea este <strong>ireversibilă</strong>: datele personale sunt
            anonimizate (GDPR Art. 17) și tokenurile sunt revocate.
          </UiAlert>
          <UiTextarea
            id="erase-reason"
            v-model="reason"
            label="Motiv (pentru jurnalul de audit)"
            :rows="2"
            :maxlength="500"
            required
          />
          <div class="actions__row">
            <UiButton type="submit" variant="primary" :loading="busy === 'erase'">Confirmă ștergerea</UiButton>
            <UiButton type="button" variant="ghost" :disabled="!!busy" @click="erasing = false">Anulează</UiButton>
          </div>
        </form>
      </section>
    </div>

    <p v-else-if="!pending" class="empty">Cetățeanul nu a fost găsit.</p>
  </div>
</template>

<script setup lang="ts">
import type { AdminCitizenDetail } from '~/types'

definePageMeta({ layout: 'admin', middleware: 'admin-auth' })
useSeoMeta({ title: 'Admin · Detalii cetățean', robots: 'noindex, nofollow' })

const route = useRoute()
const id = computed(() => String(route.params.id))
const toast = useToast()

const { data: z, pending, error, refresh } = await useFetch<AdminCitizenDetail>(
  () => `/api/admin/citizens/${id.value}`,
  { key: `admin-citizen-${id.value}` },
)

const revealed = ref(false)
const erasing = ref(false)
const reason = ref('')
const busy = ref<'' | 'unsub' | 'erase'>('')

const animalsText = computed(() => {
  const s = z.value?.species ?? {}
  const parts: string[] = []
  if (s.dog != null) parts.push(`${s.dog} câini`)
  if (s.cat != null) parts.push(`${s.cat} pisici`)
  return parts.join(', ') || '–'
})

function mask(v: string) {
  return v.length <= 4 ? '••••' : `${'•'.repeat(Math.max(0, v.length - 4))}${v.slice(-4)}`
}
function maskEmail(v: string) {
  const [user, domain] = v.split('@')
  if (!domain || !user) return '••••'
  return `${user[0]}•••@${domain}`
}

async function unsubscribe() {
  busy.value = 'unsub'
  try {
    await $fetch(`/api/admin/citizens/${id.value}/unsubscribe`, { method: 'POST' })
    toast.success('Cetățeanul a fost dezabonat.')
    await refresh()
  } catch (err) {
    toast.error(extractApiError(err))
  } finally {
    busy.value = ''
  }
}

async function erase() {
  if (!reason.value.trim()) return
  busy.value = 'erase'
  try {
    await $fetch(`/api/admin/citizens/${id.value}/erase`, { method: 'POST', body: { reason: reason.value.trim() } })
    toast.success('Datele au fost șterse.')
    erasing.value = false
    reason.value = ''
    await refresh()
  } catch (err) {
    toast.error(extractApiError(err))
  } finally {
    busy.value = ''
  }
}
</script>

<style scoped>
.page { display: flex; flex-direction: column; gap: var(--space-md); max-width: 720px; }
.back { font-size: var(--font-size-sm); color: var(--color-primary); text-decoration: none; }
.back:hover { text-decoration: underline; }

.detail { display: flex; flex-direction: column; gap: var(--space-md); }
.detail__head { display: flex; justify-content: space-between; align-items: center; gap: var(--space-md); }
.detail__title {
  font-family: var(--font-heading, var(--font-body));
  font-size: var(--font-size-xl);
  color: var(--color-text);
  margin: 0;
}

.card {
  background: var(--color-input-bg, #fff);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-lg);
}
.card__titlerow { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-sm); }
.card__title { font-size: var(--font-size-base); color: var(--color-text); margin: 0; }
.reveal {
  border: 1px solid var(--color-border);
  background: var(--color-input-bg, #fff);
  border-radius: var(--radius-md);
  padding: 0.2rem 0.6rem;
  font-size: var(--font-size-sm);
  cursor: pointer;
  color: var(--color-primary);
}

.kv { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: var(--space-sm) var(--space-lg); margin: 0; }
.kv dt { font-size: var(--font-size-sm); color: var(--color-slate-500, #64748b); }
.kv dd { margin: 0.125rem 0 0; color: var(--color-text); }
.notes { margin-top: var(--space-md); font-size: var(--font-size-sm); color: var(--color-text); }

.actions__row { display: flex; gap: var(--space-sm); flex-wrap: wrap; }
.erase { display: flex; flex-direction: column; gap: var(--space-sm); margin-top: var(--space-md); }
.empty { color: var(--color-slate-500, #64748b); }
</style>

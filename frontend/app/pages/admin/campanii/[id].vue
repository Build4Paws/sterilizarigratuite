<template>
  <div class="page">
    <NuxtLink to="/admin/campanii" class="back">← Înapoi la campanii</NuxtLink>

    <UiAlert v-if="error" variant="error">{{ extractApiError(error) }}</UiAlert>

    <div v-if="c" class="detail">
      <header class="detail__head">
        <div>
          <h1 class="detail__title">{{ c.organizationName }}</h1>
          <p class="detail__sub">{{ c.locality }}, {{ c.countyName }}</p>
        </div>
        <AdminStatusBadge :status="c.status" />
      </header>

      <section class="card">
        <dl class="kv">
          <div><dt>Perioadă</dt><dd>{{ formatDateRange(c.dateStart, c.dateEnd ?? undefined) }}</dd></div>
          <div><dt>Interval orar</dt><dd>{{ c.timeStart }}–{{ c.timeEnd }}</dd></div>
          <div><dt>Adresă</dt><dd>{{ c.address }}</dd></div>
          <div><dt>Telefon public</dt><dd>{{ formatPhone(c.phonePublic) }}</dd></div>
          <div><dt>Medic</dt><dd>{{ c.doctor || '–' }}</dd></div>
          <div><dt>Locuri</dt><dd>{{ slotsText }}</dd></div>
        </dl>
      </section>

      <section class="card">
        <h2 class="card__title">Contact privat (organizator)</h2>
        <dl class="kv">
          <div><dt>Email</dt><dd>{{ c.contactEmail }}</dd></div>
          <div><dt>Telefon</dt><dd>{{ formatPhone(c.contactPhone) }}</dd></div>
        </dl>
      </section>

      <section v-if="c.reviewedBy || c.rejectionReason" class="card">
        <h2 class="card__title">Verificare</h2>
        <dl class="kv">
          <div v-if="c.reviewedBy"><dt>De către</dt><dd>{{ c.reviewedBy }}</dd></div>
          <div v-if="c.reviewedAt"><dt>La</dt><dd>{{ formatDateTime(c.reviewedAt) }}</dd></div>
          <div v-if="c.rejectionReason"><dt>Motiv respingere</dt><dd>{{ c.rejectionReason }}</dd></div>
        </dl>
      </section>

      <!-- Moderation actions — only meaningful while pending -->
      <section v-if="c.status === 'pending'" class="card actions">
        <h2 class="card__title">Moderare</h2>
        <div v-if="!rejecting" class="actions__row">
          <UiButton variant="primary" :loading="busy" @click="approve">Aprobă</UiButton>
          <UiButton variant="ghost" :disabled="busy" @click="rejecting = true">Respinge</UiButton>
        </div>
        <form v-else class="actions__reject" @submit.prevent="reject">
          <UiTextarea
            id="reject-reason"
            v-model="reason"
            label="Motivul respingerii"
            placeholder="Ex: date incomplete, dată în trecut…"
            :rows="3"
            :maxlength="500"
            required
          />
          <div class="actions__row">
            <UiButton type="submit" variant="primary" :loading="busy">Confirmă respingerea</UiButton>
            <UiButton type="button" variant="ghost" :disabled="busy" @click="rejecting = false">Anulează</UiButton>
          </div>
        </form>
      </section>
    </div>

    <p v-else-if="!pending" class="empty">Campania nu a fost găsită.</p>
  </div>
</template>

<script setup lang="ts">
import type { AdminCampaignDetail, AdminCampaignStatus } from '~/types'

definePageMeta({ layout: 'admin', middleware: 'admin-auth' })
useSeoMeta({ title: 'Admin · Detalii campanie', robots: 'noindex, nofollow' })

const route = useRoute()
const id = computed(() => String(route.params.id))
const toast = useToast()
const { me } = useAdminAuth()

const { data: c, pending, error } = await useFetch<AdminCampaignDetail>(
  () => `/api/admin/campaigns/${id.value}`,
  { key: `admin-campaign-${id.value}` },
)

/**
 * Apply the result of a moderation action locally instead of immediately
 * re-reading the backend. A successful POST is authoritative (it hit the
 * writer), but an immediate GET can race replica propagation and return the
 * pre-action `pending` row — which made approvals appear to "revert". We patch
 * the known new state here, and invalidate the shared list + sidebar-badge
 * caches so they refetch fresh on next view.
 */
function applyReviewed(status: AdminCampaignStatus, rejectionReason?: string) {
  if (c.value) {
    c.value = {
      ...c.value,
      status,
      reviewedBy: me.value?.email ?? c.value.reviewedBy ?? null,
      reviewedAt: new Date().toISOString(),
      ...(rejectionReason ? { rejectionReason } : {}),
    }
  }
  refreshNuxtData(['admin-campaigns', 'admin-overview'])
}

const busy = ref(false)
const rejecting = ref(false)
const reason = ref('')

const slotsText = computed(() => {
  const s = c.value?.species ?? {}
  const parts: string[] = []
  if (s.dog != null) parts.push(`${s.dog} câini`)
  if (s.cat != null) parts.push(`${s.cat} pisici`)
  return parts.join(', ') || '–'
})

async function approve() {
  busy.value = true
  try {
    await $fetch(`/api/admin/campaigns/${id.value}/approve`, { method: 'POST' })
    applyReviewed('approved')
    toast.success('Campania a fost aprobată.')
  } catch (err) {
    toast.error(extractApiError(err))
  } finally {
    busy.value = false
  }
}

async function reject() {
  const why = reason.value.trim()
  if (!why) return
  busy.value = true
  try {
    await $fetch(`/api/admin/campaigns/${id.value}/reject`, { method: 'POST', body: { reason: why } })
    applyReviewed('rejected', why)
    toast.success('Campania a fost respinsă.')
    rejecting.value = false
    reason.value = ''
  } catch (err) {
    toast.error(extractApiError(err))
  } finally {
    busy.value = false
  }
}
</script>

<style scoped>
.page { display: flex; flex-direction: column; gap: var(--space-md); max-width: 760px; }
.back { font-size: var(--font-size-sm); color: var(--color-primary); text-decoration: none; }
.back:hover { text-decoration: underline; }

.detail { display: flex; flex-direction: column; gap: var(--space-md); }
.detail__head { display: flex; justify-content: space-between; align-items: flex-start; gap: var(--space-md); }
.detail__title {
  font-family: var(--font-heading, var(--font-body));
  font-size: var(--font-size-xl);
  color: var(--color-text);
  margin: 0;
}
.detail__sub { color: var(--color-slate-500, #64748b); margin: 0.25rem 0 0; }

.card {
  background: var(--color-input-bg, #fff);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-lg);
}
.card__title { font-size: var(--font-size-base); color: var(--color-text); margin: 0 0 var(--space-sm); }

.kv { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: var(--space-sm) var(--space-lg); margin: 0; }
.kv dt { font-size: var(--font-size-sm); color: var(--color-slate-500, #64748b); }
.kv dd { margin: 0.125rem 0 0; color: var(--color-text); }

.actions__row { display: flex; gap: var(--space-sm); flex-wrap: wrap; }
.actions__reject { display: flex; flex-direction: column; gap: var(--space-sm); }
.empty { color: var(--color-slate-500, #64748b); }
</style>

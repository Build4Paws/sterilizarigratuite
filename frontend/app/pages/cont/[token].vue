<template>
  <div class="manage">
    <div class="manage__card">
      <NuxtLink to="/" class="manage__brand">
        <img src="/favicon.svg" alt="" width="28" height="28" />
        <span>sterilizarigratuite.ro</span>
      </NuxtLink>

      <h1 class="manage__title">Gestionează înscrierea ta</h1>

      <!-- Invalid / expired / already-used token -->
      <UiAlert v-if="fetchError" variant="error">{{ extractApiError(fetchError) }}</UiAlert>

      <!-- Erased (final state) -->
      <template v-else-if="done === 'deleted' || citizen?.status === 'deleted'">
        <UiAlert variant="success">
          Datele tale au fost șterse complet din sistemul nostru. Nu te vom mai contacta.
        </UiAlert>
        <NuxtLink to="/" class="manage__home">Înapoi la pagina principală</NuxtLink>
      </template>

      <!-- Active management -->
      <template v-else-if="citizen">
        <p class="manage__hi">Bună, <strong>{{ citizen.name }}</strong>!</p>
        <p class="manage__info">
          Ești pe lista de așteptare pentru
          <strong>{{ citizen.locality }}</strong> — te anunțăm când apare o campanie
          de sterilizare gratuită în zona ta.
        </p>

        <UiAlert
          v-if="done === 'unsubscribed' || citizen.status === 'unsubscribed'"
          variant="info"
        >
          Ești dezabonat — nu îți mai trimitem notificări. Dacă vrei, poți cere și
          ștergerea completă a datelor mai jos.
        </UiAlert>

        <!-- Erase confirmation -->
        <div v-if="confirmErase" class="manage__confirm">
          <UiAlert variant="error">
            Ștergerea este <strong>ireversibilă</strong>: datele tale personale sunt
            eliminate definitiv (GDPR Art. 17) și nu te vom mai putea contacta.
          </UiAlert>
          <div class="manage__actions">
            <UiButton variant="primary" :loading="busy === 'erase'" @click="erase">
              Da, șterge-mi datele
            </UiButton>
            <UiButton variant="ghost" :disabled="!!busy" @click="confirmErase = false">
              Anulează
            </UiButton>
          </div>
        </div>

        <!-- Default actions -->
        <div v-else class="manage__actions">
          <UiButton
            v-if="citizen.status !== 'unsubscribed' && done !== 'unsubscribed'"
            variant="secondary"
            :loading="busy === 'unsub'"
            @click="unsubscribe"
          >
            Dezabonează-te
          </UiButton>
          <UiButton variant="ghost" :disabled="!!busy" @click="confirmErase = true">
            Șterge-mi datele definitiv
          </UiButton>
        </div>
      </template>

      <p v-else class="manage__loading">Se încarcă…</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { CitizenStatus } from '~/types'

interface ManageResponse {
  valid: boolean
  citizen: { citizenId: string; name: string; locality: string; status: CitizenStatus }
}

definePageMeta({ layout: 'default' })
useSeoMeta({ title: 'Gestionează înscrierea · Sterilizări Gratuite', robots: 'noindex, nofollow' })

const route = useRoute()
const token = String(route.params.token)
const toast = useToast()

const { data, error: fetchError } = await useFetch<ManageResponse>(
  () => `/api/m/${token}`,
  { key: `manage-${token}` },
)

// Local, mutable copy so actions update the view without a re-fetch.
const citizen = ref(data.value?.citizen ?? null)
const busy = ref<'' | 'unsub' | 'erase'>('')
const confirmErase = ref(false)
const done = ref<'' | 'unsubscribed' | 'deleted'>('')

async function unsubscribe() {
  busy.value = 'unsub'
  try {
    await $fetch(`/api/m/${token}/unsubscribe`, { method: 'POST' })
    if (citizen.value) citizen.value = { ...citizen.value, status: 'unsubscribed' }
    done.value = 'unsubscribed'
    toast.success('Te-am dezabonat.')
  } catch (err) {
    toast.error(extractApiError(err))
  } finally {
    busy.value = ''
  }
}

async function erase() {
  busy.value = 'erase'
  try {
    await $fetch(`/api/m/${token}/erase`, { method: 'POST' })
    done.value = 'deleted'
    confirmErase.value = false
    toast.success('Datele tale au fost șterse.')
  } catch (err) {
    toast.error(extractApiError(err))
  } finally {
    busy.value = ''
  }
}
</script>

<style scoped>
.manage {
  display: flex;
  justify-content: center;
  padding: var(--space-2xl) var(--space-md);
}
.manage__card {
  width: 100%;
  max-width: 520px;
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  padding: var(--space-xl);
  background: var(--color-input-bg, #fff);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}
.manage__brand {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  color: var(--color-primary);
  font-weight: 700;
  text-decoration: none;
}
.manage__title {
  font-family: var(--font-heading, var(--font-body));
  font-size: var(--font-size-lg);
  color: var(--color-text);
  margin: 0;
}
.manage__hi { font-size: var(--font-size-base); color: var(--color-text); margin: 0; }
.manage__info { color: var(--color-text-muted); margin: 0; line-height: var(--line-height-base); }
.manage__actions { display: flex; flex-wrap: wrap; gap: var(--space-sm); margin-top: var(--space-xs); }
.manage__confirm { display: flex; flex-direction: column; gap: var(--space-sm); }
.manage__home { color: var(--color-accent); font-weight: 600; text-decoration: none; }
.manage__home:hover { text-decoration: underline; }
.manage__loading { color: var(--color-text-muted); }
</style>

<template>
  <div class="manage">
    <div class="manage__card">
      <NuxtLink to="/" class="manage__brand">
        <img src="/favicon.svg" alt="" width="28" height="28" />
        <span>{{ siteHost }}</span>
      </NuxtLink>

      <h1 class="manage__title">Gestionează campania</h1>

      <!-- Invalid / expired token -->
      <UiAlert v-if="fetchError" variant="error">{{ extractApiError(fetchError) }}</UiAlert>

      <template v-else-if="campaign">
        <!-- Campaign summary -->
        <div class="manage__summary">
          <p class="manage__org">{{ campaign.organizationName }}</p>
          <p class="manage__where">{{ campaign.locality }}, {{ campaign.countyName }}</p>
          <p class="manage__when">
            {{ formatDateRange(campaign.dateStart, campaign.dateEnd ?? undefined) }},
            {{ campaign.timeStart }}–{{ campaign.timeEnd }}
          </p>
        </div>

        <!-- Sold out (final state) -->
        <template v-if="campaign.soldOut">
          <UiAlert variant="success">
            Înscrierile sunt oprite. Vizitatorii văd
            <strong>„⛔ Locuri ocupate. Mulțumim!”</strong> în locul numărului de telefon.
          </UiAlert>
          <p class="manage__hint">
            Ai făcut o greșeală sau mai ai locuri? Poți redeschide înscrierile.
          </p>
          <div class="manage__actions">
            <UiButton variant="ghost" :loading="busy === 'reopen'" @click="setSoldOut(false)">
              Redeschide înscrierile
            </UiButton>
          </div>
        </template>

        <!-- Confirmation before stopping -->
        <template v-else-if="confirmStop">
          <UiAlert variant="info">
            Confirmi? Numărul de telefon public dispare din pagina campaniei și
            vizitatorii văd „⛔ Locuri ocupate. Mulțumim!”. Poți redeschide oricând.
          </UiAlert>
          <div class="manage__actions">
            <UiButton variant="primary" :loading="busy === 'mark'" @click="setSoldOut(true)">
              Da, oprește înscrierile
            </UiButton>
            <UiButton variant="ghost" :disabled="!!busy" @click="confirmStop = false">
              Anulează
            </UiButton>
          </div>
        </template>

        <!-- Default: offer to stop registrations -->
        <template v-else>
          <p class="manage__info">
            Când toate locurile sunt ocupate, oprește înscrierile ca oamenii să nu
            mai sune. Campania rămâne vizibilă, dar cu mențiunea „Locuri ocupate”.
          </p>
          <div class="manage__actions">
            <UiButton variant="primary" @click="confirmStop = true">
              Marchează Sold Out — oprește înscrierile
            </UiButton>
          </div>
        </template>
      </template>

      <p v-else class="manage__loading">Se încarcă…</p>
    </div>
  </div>
</template>

<script setup lang="ts">
interface ManageCampaign {
  submissionId: string
  organizationName: string
  countyName: string
  locality: string
  address: string
  dateStart: string
  dateEnd: string | null
  timeStart: string
  timeEnd: string
  status: string
  soldOut: boolean
}
interface ManageResponse { valid: boolean; campaign: ManageCampaign }

definePageMeta({ layout: 'default' })
useSeoMeta({ title: 'Gestionează campania · Sterilizări Gratuite', robots: 'noindex, nofollow' })

const route = useRoute()
const token = String(route.params.token)
const toast = useToast()

const siteConfig = useSiteConfig()
const siteHost = computed(() => siteConfig.url.replace(/^https?:\/\//, '').replace(/\/$/, ''))

const { data, error: fetchError } = await useFetch<ManageResponse>(
  () => `/api/campaigns/manage/${token}`,
  { key: `campaign-manage-${token}` },
)

// Local, mutable copy so the action updates the view without a re-fetch.
const campaign = ref(data.value?.campaign ?? null)
const busy = ref<'' | 'mark' | 'reopen'>('')
const confirmStop = ref(false)

async function setSoldOut(value: boolean) {
  busy.value = value ? 'mark' : 'reopen'
  try {
    const res = await $fetch<{ soldOut: boolean; message: string }>(
      `/api/campaigns/manage/${token}/sold-out`,
      { method: 'POST', body: { soldOut: value } },
    )
    if (campaign.value) campaign.value = { ...campaign.value, soldOut: res.soldOut }
    confirmStop.value = false
    toast.success(res.message)
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
.manage__summary {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: var(--space-md);
  background: rgba(4, 26, 73, 0.04);
  border-left: 3px solid var(--color-primary);
  border-radius: var(--radius-sm);
}
.manage__org { font-weight: 700; color: var(--color-primary); margin: 0; }
.manage__where { color: var(--color-text-muted); font-size: var(--font-size-sm); margin: 0; }
.manage__when { color: var(--color-text); font-weight: 500; margin: 2px 0 0; }
.manage__info { color: var(--color-text-muted); margin: 0; line-height: var(--line-height-base); }
.manage__hint { color: var(--color-text-muted); font-size: var(--font-size-sm); margin: 0; }
.manage__actions { display: flex; flex-wrap: wrap; gap: var(--space-sm); margin-top: var(--space-xs); }
.manage__loading { color: var(--color-text-muted); }
</style>

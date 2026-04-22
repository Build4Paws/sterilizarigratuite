import type { MaybeRefOrGetter } from 'vue'
import type { LocalityWaitingStats } from '~/types'

/**
 * Reactive composable that fetches the "people waiting" stats for a given
 * (county, locality) pair via the Nuxt server route `/api/stats/locality`.
 *
 * Re-fetches whenever either input changes. When either input is empty the
 * counts reset to 0 without hitting the network.
 */
export function useLocalityWaitingCount(
  county: MaybeRefOrGetter<string>,
  locality: MaybeRefOrGetter<string>,
) {
  const stats = ref<LocalityWaitingStats | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const localityCount = computed(() => stats.value?.registeredInLocality ?? 0)
  const countyCount = computed(() => stats.value?.registeredInCounty ?? 0)

  async function fetchStats(c: string, l: string) {
    if (!c || !l) {
      stats.value = null
      error.value = null
      return
    }
    loading.value = true
    error.value = null
    try {
      stats.value = await $fetch<LocalityWaitingStats>('/api/stats/locality', {
        query: { county: c, locality: l },
      })
    } catch (err: unknown) {
      const e = err as { statusMessage?: string; message?: string }
      error.value = e.statusMessage || e.message || 'Eroare la încărcarea statisticilor.'
      stats.value = null
    } finally {
      loading.value = false
    }
  }

  watch(
    [() => toValue(county), () => toValue(locality)],
    ([c, l]) => { fetchStats(c, l) },
    { immediate: true },
  )

  return { stats, localityCount, countyCount, loading, error, fetchStats }
}

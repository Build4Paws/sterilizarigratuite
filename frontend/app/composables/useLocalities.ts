import type { JudeteData } from '~/types'

interface LocalityOption {
  value: string
  label: string
}

interface LocalitiesApiResponse {
  localities: Array<{ id: string; name: string }>
}

let judeteCache: JudeteData | null = null

async function loadLocalFallback(countyCode: string): Promise<LocalityOption[]> {
  if (!judeteCache) {
    const mod = await import('~/assets/data/judete.json')
    judeteCache = mod.default as JudeteData
  }
  const judet = judeteCache.judete.find(j => j.auto === countyCode.toUpperCase())
  return (judet?.localitati ?? []).map(l => ({ value: l.nume, label: l.nume }))
}

/**
 * Async locality typeahead backed by GET /api/counties/{code}/localities.
 * Falls back to local judete.json on network failure so form submission
 * is never blocked.
 *
 * Usage:
 *   const { localities, loading, search } = useLocalities(() => form.county)
 *
 * Wire `search` to the UiCombobox `@search` event (async mode).
 * The initial list for the selected county is fetched automatically
 * when `countyCode()` becomes non-empty.
 */
export function useLocalities(countyCode: () => string) {
  const localities = ref<LocalityOption[]>([])
  const loading = ref(false)

  let debounceTimer: ReturnType<typeof setTimeout> | null = null

  async function doFetch(code: string, q: string) {
    if (!code) {
      localities.value = []
      return
    }
    loading.value = true
    try {
      const params = q ? `?q=${encodeURIComponent(q.slice(0, 50))}` : ''
      const res = await $fetch<LocalitiesApiResponse>(`/api/counties/${code}/localities${params}`)
      localities.value = res.localities.map(l => ({ value: l.name, label: l.name }))
    } catch {
      // Degrade gracefully — serve the local judete.json list.
      localities.value = await loadLocalFallback(code)
    } finally {
      loading.value = false
    }
  }

  /**
   * Called by UiCombobox `@search` event (debounced internally).
   * The empty-query case (user opens dropdown) re-loads the full list.
   */
  function search(q: string) {
    if (debounceTimer) clearTimeout(debounceTimer)
    const code = countyCode()
    if (!code) return
    debounceTimer = setTimeout(() => doFetch(code, q), 250)
  }

  // Fetch all localities immediately when the county changes.
  watch(countyCode, (newCode) => {
    if (debounceTimer) clearTimeout(debounceTimer)
    localities.value = []
    if (newCode) doFetch(newCode, '')
  })

  onUnmounted(() => {
    if (debounceTimer) clearTimeout(debounceTimer)
  })

  return { localities, loading, search }
}

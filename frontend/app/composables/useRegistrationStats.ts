import type { RegistrationsCountryResponse, CountyStats } from '~/types'

const CACHE_KEY = 'b4p:reg-stats:v1'
const CACHE_TTL = 24 * 60 * 60 * 1000 // 24 hours

interface CacheEntry {
  data: RegistrationsCountryResponse
  savedAt: number
}

function readLocalCache(): RegistrationsCountryResponse | undefined {
  if (!import.meta.client) return undefined
  try {
    const raw = localStorage.getItem(CACHE_KEY)
    if (!raw) return undefined
    const entry = JSON.parse(raw) as CacheEntry
    if (Date.now() - entry.savedAt > CACHE_TTL) {
      localStorage.removeItem(CACHE_KEY)
      return undefined
    }
    return entry.data
  } catch {
    return undefined
  }
}

function writeLocalCache(data: RegistrationsCountryResponse): void {
  if (!import.meta.client) return
  try {
    const entry: CacheEntry = { data, savedAt: Date.now() }
    localStorage.setItem(CACHE_KEY, JSON.stringify(entry))
  } catch {
    // quota exceeded or storage unavailable — silent fail
  }
}

const FETCH_KEY = 'stats-registrations'

export function useRegistrationStats() {
  const { data, error, status } = useAsyncData<RegistrationsCountryResponse>(
    FETCH_KEY,
    () => $fetch<RegistrationsCountryResponse>('/api/stats/registrations'),
    {
      default: () => ({ byCounty: {}, totalRegistrations: 0 } as RegistrationsCountryResponse),
      getCachedData(key, nuxtApp) {
        // Hydration: SSR already fetched — return the SSR payload so the
        // client never re-fetches on first paint. Mirrors Nuxt's own default.
        const fromSSR = (nuxtApp.payload.data[key] ?? nuxtApp.static?.data?.[key]) as
          | RegistrationsCountryResponse
          | undefined
        if (fromSSR !== undefined) return fromSSR

        // Client-side navigation: serve from localStorage if still within 24h.
        return readLocalCache()
      },
    },
  )

  // Persist fresh API responses so the next 24h are served locally.
  watch(data, (val) => {
    if (val && val.totalRegistrations > 0) writeLocalCache(val)
  }, { immediate: true })

  const byCounty = computed<Record<string, CountyStats>>(() => data.value?.byCounty ?? {})
  const totalRegistrations = computed<number>(() => data.value?.totalRegistrations ?? 0)
  const loading = computed(() => status.value === 'pending')

  return { byCounty, totalRegistrations, loading, error }
}

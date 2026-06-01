import type { RegistrationsCountryResponse, CountyStats } from '~/types'

const FETCH_KEY = 'stats-registrations'

/**
 * Country-wide registration stats for the choropleth map. No frontend caching —
 * SSR fetches on first paint and the payload hydrates the client (standard Nuxt
 * behaviour); any later client-side navigation refetches. The data shown always
 * reflects what the backend returns.
 */
export function useRegistrationStats() {
  const { data, error, status } = useAsyncData<RegistrationsCountryResponse>(
    FETCH_KEY,
    () => $fetch<RegistrationsCountryResponse>('/api/stats/map'),
    {
      default: () => ({ byCounty: {}, totalRegistrations: 0 } as RegistrationsCountryResponse),
    },
  )

  const byCounty = computed<Record<string, CountyStats>>(() => data.value?.byCounty ?? {})
  const totalRegistrations = computed<number>(() => data.value?.totalRegistrations ?? 0)
  const loading = computed(() => status.value === 'pending')

  return { byCounty, totalRegistrations, loading, error }
}

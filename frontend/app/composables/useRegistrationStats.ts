import type { RegistrationsCountryResponse, CountyStats } from '~/types'

export function useRegistrationStats() {
  const { data, error, status } = useFetch<RegistrationsCountryResponse>('/api/stats/registrations', {
    default: () => ({ byCounty: {}, totalRegistrations: 0 }),
  })

  const byCounty = computed<Record<string, CountyStats>>(() => data.value?.byCounty ?? {})
  const totalRegistrations = computed<number>(() => data.value?.totalRegistrations ?? 0)
  const loading = computed(() => status.value === 'pending')

  return { byCounty, totalRegistrations, loading, error }
}

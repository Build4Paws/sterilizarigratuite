import type { MaybeRefOrGetter } from 'vue'
import type { Campaign, Species } from '~/types'

interface CampaignsApiResponse {
  campaigns?: Campaign[]
}

interface UseCampaignsFilters {
  /** 2-letter county code, e.g. "AB". Empty string = no county filter. */
  countyCode: MaybeRefOrGetter<string>
  /** "dog" | "cat" | "" (no filter). Applied client-side, never sent to API. */
  species: MaybeRefOrGetter<Species | ''>
}

/**
 * Fetches approved upcoming campaigns from `/api/campaigns`. Re-fetches when
 * `countyCode` changes; species filtering is computed locally over the
 * already-fetched list because the backend doesn't support combined filters.
 */
export function useCampaigns(filters: UseCampaignsFilters) {
  const queryParams = computed<Record<string, string>>(() => {
    const code = toValue(filters.countyCode)
    const out: Record<string, string> = {}
    if (code) out.county = code
    return out
  })

  // useFetch auto-watches reactive options like `query`, so any change to
  // countyCode triggers a refetch. Species is intentionally NOT in `query`
  // — it's filtered locally below.
  const { data, error, status, refresh } = useFetch<CampaignsApiResponse | Campaign[]>(
    '/api/campaigns',
    {
      query: queryParams,
      default: () => ({ campaigns: [] }),
    },
  )

  const allCampaigns = computed<Campaign[]>(() => {
    const d = data.value
    if (!d) return []
    if (Array.isArray(d)) return d
    return d.campaigns ?? []
  })

  const total = computed(() => allCampaigns.value.length)

  const campaigns = computed<Campaign[]>(() => {
    const sp = toValue(filters.species)
    if (!sp) return allCampaigns.value
    return allCampaigns.value.filter(c => c.species.includes(sp))
  })

  const loading = computed(() => status.value === 'pending')

  return {
    campaigns,
    total,
    loading,
    error,
    refresh,
  }
}

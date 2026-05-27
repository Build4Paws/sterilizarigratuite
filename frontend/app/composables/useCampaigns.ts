import type { MaybeRefOrGetter } from 'vue'
import type { Campaign, PublicCampaign, Species } from '~/types'

interface CampaignsApiResponse {
  campaigns?: PublicCampaign[]
}

interface UseCampaignsFilters {
  /** 2-letter county code, e.g. "AB". Empty string = no county filter. */
  countyCode: MaybeRefOrGetter<string>
  /** "dog" | "cat" | "" (no filter). Applied client-side, never sent to API. */
  species: MaybeRefOrGetter<Species | ''>
}

/**
 * Maps a wire `PublicCampaign` (species = object of slot counts) to the UI
 * `Campaign` type (species = string array, separate slot fields).
 */
function normalizePublicCampaign(p: PublicCampaign): Campaign {
  const species: Species[] = (Object.keys(p.species) as Species[]).filter(
    (k): k is Species => k === 'dog' || k === 'cat',
  )
  return {
    id: p.submissionId,
    organizationName: p.organizationName,
    county: p.county,
    countyName: p.countyName,
    locality: p.locality,
    address: p.address,
    dateStart: p.dateStart,
    dateEnd: p.dateEnd ?? undefined,
    timeStart: p.timeStart,
    timeEnd: p.timeEnd,
    species,
    slotsDogs: p.species.dog,
    slotsCats: p.species.cat,
    doctor: p.doctor ?? undefined,
    phonePublic: p.phonePublic,
    status: 'APPROVED',
    createdAt: '',
  }
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
  const { data, error, status, refresh } = useFetch<CampaignsApiResponse | PublicCampaign[]>(
    '/api/campaigns',
    {
      query: queryParams,
      default: () => ({ campaigns: [] }),
    },
  )

  const allCampaigns = computed<Campaign[]>(() => {
    const d = data.value
    if (!d) return []
    const raw: PublicCampaign[] = Array.isArray(d) ? d : (d.campaigns ?? [])
    return raw.map(normalizePublicCampaign)
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

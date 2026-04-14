import type { County, Locality } from '~/types'

export function useLocationData() {
  const counties = useState<County[]>('counties', () => [])
  const localities = useState<Locality[]>('localities', () => [])
  const selectedCounty = useState<string>('selectedCounty', () => '')
  const loadingCounties = useState('loadingCounties', () => false)
  const loadingLocalities = useState('loadingLocalities', () => false)

  async function fetchCounties() {
    if (counties.value.length > 0) return
    loadingCounties.value = true
    try {
      const data = await $api<County[]>('/locations/counties')
      counties.value = data
    } finally {
      loadingCounties.value = false
    }
  }

  async function fetchLocalities(countyCode: string) {
    if (!countyCode) {
      localities.value = []
      return
    }
    selectedCounty.value = countyCode
    loadingLocalities.value = true
    try {
      const data = await $api<Locality[]>(`/locations/counties/${countyCode}/localities`)
      localities.value = data
    } finally {
      loadingLocalities.value = false
    }
  }

  return {
    counties,
    localities,
    selectedCounty,
    loadingCounties,
    loadingLocalities,
    fetchCounties,
    fetchLocalities,
  }
}

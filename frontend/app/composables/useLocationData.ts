import type { JudeteData } from '~/types'

let cachedData: JudeteData | null = null

async function loadData(): Promise<JudeteData> {
  if (cachedData) return cachedData
  const mod = await import('~/assets/data/judete.json')
  cachedData = mod.default as JudeteData
  return cachedData
}

export function useLocationData() {
  const selectedCounty = ref('')
  const judete = ref<JudeteData['judete']>([])
  const loaded = ref(false)

  const counties = computed(() =>
    judete.value.map(j => ({
      value: j.auto,
      label: j.nume,
    }))
  )

  const localities = computed(() => {
    if (!selectedCounty.value) return []
    const judet = judete.value.find(j => j.auto === selectedCounty.value)
    if (!judet) return []
    return judet.localitati.map(l => ({
      value: l.nume,
      label: l.nume,
    }))
  })

  function setCounty(code: string) {
    selectedCounty.value = code
  }

  async function init() {
    if (loaded.value) return
    const data = await loadData()
    judete.value = data.judete
    loaded.value = true
  }

  return {
    counties,
    localities,
    selectedCounty,
    setCounty,
    init,
  }
}

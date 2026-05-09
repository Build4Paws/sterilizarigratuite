import type { JudeteData } from '~/types'

let cachedData: JudeteData | null = null

async function loadData(): Promise<JudeteData> {
  if (cachedData) return cachedData
  const mod = await import('~/assets/data/judete.json')
  cachedData = mod.default as JudeteData
  return cachedData
}

/**
 * Strip Romanian diacritics (ă â î ș ț + cedilla variants) and lowercase.
 * NFD splits e.g. "ț" into "t" + combining comma below; we drop the combining
 * marks (Unicode block U+0300–U+036F).
 */
function makeSlug(name: string): string {
  return name
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
    .replace(/\s+/g, '-')
    .replace(/[^a-z0-9-]/g, '')
}

let slugToCode: Record<string, string> | null = null
let codeToSlug: Record<string, string> | null = null
let codeToName: Record<string, string> | null = null

async function ensureIndexes() {
  if (slugToCode && codeToSlug && codeToName) return
  const data = await loadData()
  slugToCode = {}
  codeToSlug = {}
  codeToName = {}
  for (const j of data.judete) {
    const slug = makeSlug(j.nume)
    slugToCode[slug] = j.auto
    codeToSlug[j.auto] = slug
    codeToName[j.auto] = j.nume
  }
}

/** URL slug (e.g. "alba", "bistrita-nasaud") → 2-letter code (e.g. "AB"). */
export async function slugToCountyCode(slug: string): Promise<string> {
  if (!slug) return ''
  await ensureIndexes()
  return slugToCode![slug.toLowerCase()] ?? ''
}

/** 2-letter code → URL slug. */
export async function countyCodeToSlug(code: string): Promise<string> {
  if (!code) return ''
  await ensureIndexes()
  return codeToSlug![code.toUpperCase()] ?? ''
}

/** 2-letter code → display name (e.g. "AB" → "Alba"). */
export async function countyCodeToName(code: string): Promise<string> {
  if (!code) return ''
  await ensureIndexes()
  return codeToName![code.toUpperCase()] ?? ''
}

/**
 * Eagerly load + index judete data so synchronous lookups below work in
 * templates. Call once during page setup (SSR-safe).
 */
export async function ensureLocationIndexes(): Promise<void> {
  await ensureIndexes()
}

/** Sync version — returns '' if indexes haven't loaded yet. */
export function countyCodeToNameSync(code: string): string {
  if (!code || !codeToName) return ''
  return codeToName[code.toUpperCase()] ?? ''
}

/** Sync version — returns '' if indexes haven't loaded yet. */
export function countyCodeToSlugSync(code: string): string {
  if (!code || !codeToSlug) return ''
  return codeToSlug[code.toUpperCase()] ?? ''
}

/** Sync version — returns '' if indexes haven't loaded yet. */
export function slugToCountyCodeSync(slug: string): string {
  if (!slug || !slugToCode) return ''
  return slugToCode[slug.toLowerCase()] ?? ''
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

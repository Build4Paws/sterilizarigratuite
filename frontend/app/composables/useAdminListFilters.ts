/**
 * Shared filter state for the admin list pages (campanii / cetateni / organizatori).
 *
 * The URL query string is the source of truth — filters are shareable, survive a
 * refresh, and the page's `useFetch` reads `route.query` reactively to refetch.
 * This composable mirrors the relevant query keys into local refs (so inputs are
 * snappy), debounces the free-text search, and writes everything back to the URL.
 * Any pre-existing keys it doesn't own (e.g. `status` from the tabs) are preserved.
 */
export function useAdminListFilters(opts: { county?: boolean; locality?: boolean } = {}) {
  const route = useRoute()
  const router = useRouter()
  const { counties, localities, selectedCounty, init } = useLocationData()

  const search = ref(String(route.query.q ?? ''))
  const county = ref(String(route.query.county ?? ''))
  const locality = ref(String(route.query.locality ?? ''))

  // Feed the county into useLocationData so its `localities` list tracks it.
  selectedCounty.value = county.value
  watch(county, (c) => {
    selectedCounty.value = c
    if (!c) locality.value = '' // clearing the county clears its locality.
  })

  let timer: ReturnType<typeof setTimeout> | undefined

  function sync() {
    const query: Record<string, string> = {}
    // Preserve keys we don't own (status, page, …).
    for (const [k, v] of Object.entries(route.query)) {
      if (['q', 'county', 'locality'].includes(k)) continue
      if (v != null) query[k] = String(v)
    }
    if (search.value.trim()) query.q = search.value.trim()
    if (opts.county && county.value) query.county = county.value
    if (opts.locality && locality.value) query.locality = locality.value
    router.replace({ query })
  }

  // Debounce the text search; county/locality apply immediately.
  watch(search, () => {
    clearTimeout(timer)
    timer = setTimeout(sync, 350)
  })
  watch([county, locality], sync)

  function reset() {
    clearTimeout(timer)
    search.value = ''
    county.value = ''
    locality.value = ''
    sync()
  }

  const hasActive = computed(() =>
    !!(search.value || (opts.county && county.value) || (opts.locality && locality.value)))

  return { search, county, locality, counties, localities, init, reset, hasActive }
}

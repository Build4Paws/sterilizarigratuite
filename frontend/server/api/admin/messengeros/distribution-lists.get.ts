/**
 * GET messengeros distribution lists, filtered server-side.
 *
 * messengeros returns ALL lists (~13.7k once per-locality lists exist) in one
 * response, so we filter HERE — by county (the `(XX)` suffix in the name) and/or
 * a name search — and return only the matching subset. With neither filter we
 * return an empty set, so the browser never has to load the whole thing.
 *
 * The full list is cached in-process for a short TTL to avoid refetching the
 * multi-MB payload from messengeros on every keystroke.
 */
interface MgoList { id: number; name: string; contactCount?: number; createdAt?: string }

const COUNTY_RE = /\(([A-Z]{1,2})\)\s*$/
const TTL_MS = 60_000
let _cache: { at: number; lists: MgoList[] } | null = null

async function allLists(event: import('h3').H3Event): Promise<MgoList[]> {
  const now = Date.now()
  if (_cache && now - _cache.at < TTL_MS) return _cache.lists
  const res = await messengerosFetch<{ data?: MgoList[] } | MgoList[]>(event, '/distribution-lists')
  const lists = Array.isArray(res) ? res : (res?.data ?? [])
  _cache = { at: now, lists }
  return lists
}

export default defineEventHandler(async (event) => {
  const q = getQuery(event)
  const county = String(q.county ?? '').trim().toUpperCase()
  const search = String(q.q ?? '').trim().toLowerCase()

  // No filter → don't ship the whole catalogue to the browser.
  if (!county && !search) return { data: [], total: 0 }

  let lists = await allLists(event)
  if (county) lists = lists.filter(l => (l?.name?.match(COUNTY_RE)?.[1] ?? '') === county)
  if (search) lists = lists.filter(l => String(l?.name ?? '').toLowerCase().includes(search))

  return { data: lists, total: lists.length }
})

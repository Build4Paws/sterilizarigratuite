/** GET the contacts (members) of a distribution list, paged. Admin-gated proxy. */
export default defineEventHandler((event) => {
  const id = getRouterParam(event, 'id') ?? ''
  const q = getQuery(event)
  const page = Math.max(1, Number(q.page ?? 1) || 1)
  const limit = Math.min(100, Math.max(1, Number(q.limit ?? 20) || 20))
  return messengerosFetch(event, `/distribution-lists/${encodeURIComponent(id)}/contacts?page=${page}&limit=${limit}`)
})

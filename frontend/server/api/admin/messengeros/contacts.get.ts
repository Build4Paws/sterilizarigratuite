/** GET messengeros contacts (paged). Admin-gated proxy. */
export default defineEventHandler((event) => {
  const q = getQuery(event)
  const page = Math.max(1, Number(q.page ?? 1) || 1)
  const limit = Math.min(100, Math.max(1, Number(q.limit ?? 20) || 20))
  return messengerosFetch(event, `/contacts?page=${page}&limit=${limit}`)
})

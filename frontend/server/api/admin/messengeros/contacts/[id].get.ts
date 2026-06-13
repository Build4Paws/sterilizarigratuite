/** GET a single messengeros contact (full detail). Admin-gated proxy. */
export default defineEventHandler((event) => {
  const id = getRouterParam(event, 'id') ?? ''
  return messengerosFetch(event, `/contacts/${encodeURIComponent(id)}`)
})

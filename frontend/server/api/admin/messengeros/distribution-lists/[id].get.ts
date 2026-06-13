/** GET a distribution list's detail (incl. per-channel stats). Admin-gated proxy. */
export default defineEventHandler((event) => {
  const id = getRouterParam(event, 'id') ?? ''
  return messengerosFetch(event, `/distribution-lists/${encodeURIComponent(id)}`)
})

/**
 * Proxy for GET /m/{token} — validate a citizen magic-link token and return the
 * citizen summary ({ valid, citizen: { citizenId, name, locality, status } }).
 * Public AWS route (SigV4-signed). The `/cont/[token]` page consumes this.
 */
export default defineEventHandler((event) => {
  const token = getRouterParam(event, 'token') ?? ''
  return proxyAws(event, `/m/${encodeURIComponent(token)}`)
})

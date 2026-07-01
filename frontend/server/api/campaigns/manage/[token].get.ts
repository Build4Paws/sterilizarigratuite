/**
 * Proxy for GET /campaigns/manage/{token} — validate a campaign-management magic
 * link (issued to the organizer on approval) and return the campaign summary
 * ({ valid, campaign: { ..., soldOut } }). Public AWS route (SigV4-signed).
 * The `/gestionare-campanie/[token]` page consumes this.
 */
export default defineEventHandler((event) => {
  const token = getRouterParam(event, 'token') ?? ''
  return proxyAws(event, `/campaigns/manage/${encodeURIComponent(token)}`)
})

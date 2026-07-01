/**
 * Proxy for POST /campaigns/manage/{token}/sold-out — the organizer stops (or
 * reopens) registrations for their campaign. Forwards the JSON body
 * ({ soldOut?: boolean }, default true) unchanged. Public AWS route (SigV4-signed).
 */
export default defineEventHandler(async (event) => {
  const token = getRouterParam(event, 'token') ?? ''
  const body = await readBody(event).catch(() => ({}))
  return proxyAws(
    event,
    `/campaigns/manage/${encodeURIComponent(token)}/sold-out`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body ?? {}),
    },
    15_000,
  )
})

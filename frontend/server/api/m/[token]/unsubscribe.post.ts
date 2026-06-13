/**
 * Proxy for POST /m/{token}/unsubscribe — stop notifications for this citizen
 * (data kept for audit). Public AWS route (SigV4-signed).
 */
export default defineEventHandler((event) => {
  const token = getRouterParam(event, 'token') ?? ''
  return proxyAws(
    event,
    `/m/${encodeURIComponent(token)}/unsubscribe`,
    { method: 'POST', headers: { 'Content-Type': 'application/json' } },
    15_000,
  )
})

/**
 * Proxy for POST /m/{token}/erase — GDPR Art. 17 self-service erasure: nulls the
 * citizen's PII, marks them deleted, revokes their tokens. Public AWS route
 * (SigV4-signed). Irreversible — the page gates this behind a confirm step.
 */
export default defineEventHandler((event) => {
  const token = getRouterParam(event, 'token') ?? ''
  return proxyAws(
    event,
    `/m/${encodeURIComponent(token)}/erase`,
    { method: 'POST', headers: { 'Content-Type': 'application/json' } },
    15_000,
  )
})

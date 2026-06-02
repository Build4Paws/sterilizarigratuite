const buckets = new Map<string, { count: number; resetAt: number }>()

const LIMITS: Record<string, { max: number; windowMs: number }> = {
  '/api/register': { max: 5, windowMs: 60_000 },
  '/api/campaigns/submit': { max: 3, windowMs: 60_000 },
  // Brute-force guard on admin login (per IP). Generous enough for a fat-finger
  // + MFA retry, tight enough to make credential stuffing impractical.
  '/api/admin/auth/login': { max: 10, windowMs: 60_000 },
  // CSV report generation is heavier (and the citizens export touches PII) —
  // throttle per IP. Generous for normal use, tight against scripted bulk pulls.
  '/api/admin/reports': { max: 20, windowMs: 60_000 },
}

// Prune expired buckets periodically so the Map doesn't grow unbounded.
setInterval(() => {
  const now = Date.now()
  for (const [key, bucket] of buckets) {
    if (bucket.resetAt < now) buckets.delete(key)
  }
}, 60_000)

export default defineEventHandler((event) => {
  // Match + bucket on the pathname only — otherwise a varying query string
  // (e.g. report filters) would spawn a fresh bucket per request and bypass the limit.
  const path = (event.node.req.url ?? '').split('?')[0] ?? ''
  const limit = Object.entries(LIMITS).find(([prefix]) => path.startsWith(prefix))?.[1]
  if (!limit) return

  const ip = getRequestIP(event, { xForwardedFor: true }) ?? 'unknown'
  const key = `${path}:${ip}`
  const now = Date.now()
  const bucket = buckets.get(key)

  if (!bucket || bucket.resetAt < now) {
    buckets.set(key, { count: 1, resetAt: now + limit.windowMs })
    return
  }

  bucket.count++
  if (bucket.count > limit.max) {
    throw createError({
      statusCode: 429,
      statusMessage: 'Prea multe cereri.',
      data: { error: 'rate_limited' },
    })
  }
})

const buckets = new Map<string, { count: number; resetAt: number }>()

const LIMITS: Record<string, { max: number; windowMs: number }> = {
  '/api/register': { max: 5, windowMs: 60_000 },
  '/api/campaigns/submit': { max: 3, windowMs: 60_000 },
}

// Prune expired buckets periodically so the Map doesn't grow unbounded.
setInterval(() => {
  const now = Date.now()
  for (const [key, bucket] of buckets) {
    if (bucket.resetAt < now) buckets.delete(key)
  }
}, 60_000)

export default defineEventHandler((event) => {
  const url = event.node.req.url ?? ''
  const limit = Object.entries(LIMITS).find(([prefix]) => url.startsWith(prefix))?.[1]
  if (!limit) return

  const ip = getRequestIP(event, { xForwardedFor: true }) ?? 'unknown'
  const key = `${url}:${ip}`
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

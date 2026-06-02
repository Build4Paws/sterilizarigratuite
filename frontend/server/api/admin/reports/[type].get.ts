import { forwardAdmin } from '~~/server/utils/admin-auth'
import type { ReportType } from '~/types'

/**
 * GET /api/admin/reports/{type}?from=&to=&county=&status= → CSV download.
 *
 * SECURITY / GDPR: gated on the admin session (forwardAdmin → requireAdminSession).
 * The CSV bytes are shaped entirely by the backend (`/admin/reports/{type}`),
 * which also writes the audit_log entry for the export — important for the
 * `citizens` report, which touches PII. This proxy is a thin auth + passthrough
 * layer: it never caches, and it forwards the upstream's own filename.
 */
const ALLOWED: ReportType[] = ['campaigns', 'citizens', 'organizers', 'activity']

// Only these query keys are forwarded upstream — anything else is dropped so a
// crafted query can't reach the backend.
const FORWARD_KEYS = ['from', 'to', 'county', 'status'] as const

export default defineEventHandler(async (event) => {
  const type = getRouterParam(event, 'type') ?? ''
  if (!ALLOWED.includes(type as ReportType)) {
    throw createError({ statusCode: 404, statusMessage: 'Tip de raport necunoscut', data: { error: 'not_found' } })
  }

  const q = getQuery(event)
  const params = new URLSearchParams()
  for (const key of FORWARD_KEYS) {
    const v = q[key]
    if (typeof v === 'string' && v.trim()) params.set(key, v.trim())
  }
  const qs = params.toString()

  const res = await forwardAdmin(event, `/reports/${type}${qs ? `?${qs}` : ''}`, {
    headers: { Accept: 'text/csv' },
  })

  if (!res.ok) {
    const text = await res.text()
    let data: unknown = text
    try { data = JSON.parse(text) } catch { /* upstream returned non-JSON error */ }
    throw createError({ statusCode: res.status, statusMessage: res.statusText || 'Upstream error', data })
  }

  // Pass the CSV through verbatim. Prefer the backend's filename; fall back to a
  // dated default so the browser still saves something sensible.
  const today = new Date().toISOString().slice(0, 10)
  const disposition = res.headers.get('content-disposition')
    ?? `attachment; filename="raport-${type}-${today}.csv"`

  setResponseHeader(event, 'content-type', res.headers.get('content-type') ?? 'text/csv; charset=utf-8')
  setResponseHeader(event, 'content-disposition', disposition)
  setResponseHeader(event, 'cache-control', 'no-store')

  // Stream the body straight through (reports can be large); h3 accepts a Web
  // ReadableStream. Fall back to buffering if the upstream gave no stream.
  return res.body ?? (await res.text())
})

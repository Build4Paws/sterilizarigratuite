import { adminProxySend } from '~~/server/utils/admin-auth'

/**
 * POST /admin/citizens/{id}/erase — GDPR Art. 17. Irreversible: backend nulls PII
 * and revokes tokens. Requires a reason for the audit trail.
 */
export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id') ?? ''
  const body = (await readBody(event)) as { reason?: string } | null
  const reason = String(body?.reason ?? '').trim()
  if (!reason) {
    throw createError({ statusCode: 400, statusMessage: 'Motiv lipsă', data: { error: 'validation_failed' } })
  }
  return adminProxySend(event, `/citizens/${encodeURIComponent(id)}/erase`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason }),
  })
})

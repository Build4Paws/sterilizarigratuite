import { adminProxySend } from '~~/server/utils/admin-auth'

/** POST /admin/campaigns/{id}/reject — pending → rejected, with a reason. */
export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id') ?? ''
  const body = (await readBody(event)) as { reason?: string } | null
  const reason = String(body?.reason ?? '').trim()
  if (!reason) {
    throw createError({ statusCode: 400, statusMessage: 'Motiv lipsă', data: { error: 'validation_failed' } })
  }
  return adminProxySend(event, `/campaigns/${encodeURIComponent(id)}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason }),
  })
})

/** POST: add a phone number to a contact (by contact id). Admin-gated proxy.
 * Body: { phone: "+40..." }. Used when a contact has no phoneNumberId yet. */
export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id') ?? ''
  const body = (await readBody(event)) as { phone?: string } | null
  const phone = String(body?.phone ?? '').trim()
  if (!phone) {
    throw createError({ statusCode: 400, statusMessage: 'Phone required', data: { error: 'validation_failed' } })
  }
  return messengerosFetch(event, `/contacts/${encodeURIComponent(id)}/phone`, {
    method: 'POST',
    body: JSON.stringify({ phone }),
  })
})

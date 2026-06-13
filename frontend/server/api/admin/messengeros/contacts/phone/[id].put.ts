/** PUT a contact's phone number. Admin-gated proxy. Body: { value: "+40..." }. */
export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id') ?? ''
  const body = (await readBody(event)) as { value?: string } | null
  const value = String(body?.value ?? '').trim()
  if (!value) {
    throw createError({ statusCode: 400, statusMessage: 'Phone value required', data: { error: 'validation_failed' } })
  }
  return messengerosFetch(event, `/contacts/phone/${encodeURIComponent(id)}`, {
    method: 'PUT',
    body: JSON.stringify({ value }),
  })
})

/** POST: unsubscribe a contact (by phone-contact id). Admin-gated proxy. */
export default defineEventHandler((event) => {
  const id = getRouterParam(event, 'id') ?? ''
  return messengerosFetch(event, `/contacts/phone/${encodeURIComponent(id)}/unsubscribe`, { method: 'POST' })
})

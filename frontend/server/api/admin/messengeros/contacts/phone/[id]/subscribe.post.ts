/** POST: re-subscribe a contact's phone (by phone-record id). Admin-gated proxy. */
export default defineEventHandler((event) => {
  const id = getRouterParam(event, 'id') ?? ''
  return messengerosFetch(event, `/contacts/phone/${encodeURIComponent(id)}/subscribe`, { method: 'POST' })
})

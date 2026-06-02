import { adminProxySend } from '~~/server/utils/admin-auth'

/** POST /admin/citizens/{id}/unsubscribe — status → unsubscribed. */
export default defineEventHandler((event) => {
  const id = getRouterParam(event, 'id') ?? ''
  return adminProxySend(event, `/citizens/${encodeURIComponent(id)}/unsubscribe`, { method: 'POST' })
})

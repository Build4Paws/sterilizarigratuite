import { adminProxySend } from '~~/server/utils/admin-auth'

/** POST /admin/campaigns/{id}/approve — pending → approved. */
export default defineEventHandler((event) => {
  const id = getRouterParam(event, 'id') ?? ''
  return adminProxySend(event, `/campaigns/${encodeURIComponent(id)}/approve`, { method: 'POST' })
})

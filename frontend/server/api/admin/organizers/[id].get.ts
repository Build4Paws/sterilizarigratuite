import { adminProxyGet } from '~~/server/utils/admin-auth'
import type { AdminOrganizerDetail } from '~/types'

/** GET /admin/organizers/{id} — detail + their campaigns. */
export default defineEventHandler((event) => {
  const id = getRouterParam(event, 'id') ?? ''
  return adminProxyGet<AdminOrganizerDetail>(event, `/organizers/${encodeURIComponent(id)}`)
})

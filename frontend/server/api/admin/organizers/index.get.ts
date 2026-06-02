import { adminProxyGet } from '~~/server/utils/admin-auth'
import type { AdminOrganizerList } from '~/types'

/** GET /admin/organizers — list/search ?q=&page=&limit=. */
export default defineEventHandler((event) => {
  const q = getQuery(event)
  const params = new URLSearchParams()
  for (const key of ['q', 'page', 'limit']) {
    const v = q[key]
    if (v != null && String(v).length) params.set(key, String(v))
  }
  const suffix = params.toString() ? `?${params}` : ''
  return adminProxyGet<AdminOrganizerList>(event, `/organizers${suffix}`)
})

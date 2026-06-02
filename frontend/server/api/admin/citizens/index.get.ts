import { adminProxyGet } from '~~/server/utils/admin-auth'
import type { AdminCitizenList } from '~/types'

/** GET /admin/citizens — minimized list (no raw phone/email), ?status=&county=&q=&page=. */
export default defineEventHandler((event) => {
  const q = getQuery(event)
  const params = new URLSearchParams()
  for (const key of ['status', 'county', 'locality', 'q', 'page', 'limit']) {
    const v = q[key]
    if (v != null && String(v).length) params.set(key, String(v))
  }
  const suffix = params.toString() ? `?${params}` : ''
  return adminProxyGet<AdminCitizenList>(event, `/citizens${suffix}`)
})

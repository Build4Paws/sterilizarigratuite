import { adminProxyGet } from '~~/server/utils/admin-auth'
import type { AdminCampaignList } from '~/types'

/** GET /admin/campaigns — moderation list, optional ?status=&county=&q=&page=&limit=. */
export default defineEventHandler((event) => {
  const q = getQuery(event)
  const params = new URLSearchParams()
  for (const key of ['status', 'county', 'q', 'page', 'limit']) {
    const v = q[key]
    if (v != null && String(v).length) params.set(key, String(v))
  }
  const suffix = params.toString() ? `?${params}` : ''
  return adminProxyGet<AdminCampaignList>(event, `/campaigns${suffix}`)
})

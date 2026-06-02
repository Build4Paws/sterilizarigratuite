import { adminProxyGet } from '~~/server/utils/admin-auth'
import type { AuditList } from '~/types'

/** GET /admin/audit — audit log feed, ?entityType=&entityId=&action=&page=. */
export default defineEventHandler((event) => {
  const q = getQuery(event)
  const params = new URLSearchParams()
  for (const key of ['entityType', 'entityId', 'action', 'actor', 'page', 'limit']) {
    const v = q[key]
    if (v != null && String(v).length) params.set(key, String(v))
  }
  const suffix = params.toString() ? `?${params}` : ''
  return adminProxyGet<AuditList>(event, `/audit${suffix}`)
})

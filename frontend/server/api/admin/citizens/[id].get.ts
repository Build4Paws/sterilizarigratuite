import { adminProxyGet } from '~~/server/utils/admin-auth'
import type { AdminCitizenDetail } from '~/types'

/** GET /admin/citizens/{id} — detail incl. PII (access is audited backend-side). */
export default defineEventHandler((event) => {
  const id = getRouterParam(event, 'id') ?? ''
  return adminProxyGet<AdminCitizenDetail>(event, `/citizens/${encodeURIComponent(id)}`)
})

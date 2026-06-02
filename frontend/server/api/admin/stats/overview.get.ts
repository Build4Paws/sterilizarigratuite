import { adminProxyGet } from '~~/server/utils/admin-auth'
import type { AdminOverview } from '~/types'

/** GET /admin/stats/overview — dashboard tiles. */
export default defineEventHandler((event) => {
  return adminProxyGet<AdminOverview>(event, '/stats/overview')
})

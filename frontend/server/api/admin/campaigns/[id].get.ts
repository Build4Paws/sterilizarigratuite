import { adminProxyGet } from '~~/server/utils/admin-auth'
import type { AdminCampaignDetail } from '~/types'

/** GET /admin/campaigns/{id} — full detail incl. private contact + audit fields. */
export default defineEventHandler((event) => {
  const id = getRouterParam(event, 'id') ?? ''
  return adminProxyGet<AdminCampaignDetail>(event, `/campaigns/${encodeURIComponent(id)}`)
})

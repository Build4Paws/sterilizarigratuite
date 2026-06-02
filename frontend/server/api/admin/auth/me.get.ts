import { getAdminSession } from '~~/server/utils/admin-auth'

/**
 * Current admin identity, from the session cookie. 401 if not signed in.
 * Used by the route middleware and the admin layout header. Returns only
 * non-sensitive claims (email + groups), never the token.
 */
export default defineEventHandler((event) => {
  const claims = getAdminSession(event)
  if (!claims) {
    throw createError({ statusCode: 401, statusMessage: 'Neautentificat', data: { error: 'unauthorized' } })
  }
  setResponseHeader(event, 'cache-control', 'no-store')
  return { email: claims.email, groups: claims.groups }
})

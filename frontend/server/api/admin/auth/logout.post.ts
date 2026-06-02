import { cognitoIdp, clearAdminSession, ACCESS_COOKIE } from '~~/server/utils/admin-auth'

/**
 * Clear the session cookies and best-effort revoke the tokens at Cognito
 * (GlobalSignOut). Cookie clearing is what actually logs the admin out of this
 * app; the Cognito call is hardening so a leaked refresh token can't be reused.
 */
export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const region = config.cognitoRegion as string
  const accessToken = getCookie(event, ACCESS_COOKIE)

  clearAdminSession(event)

  if (accessToken && region) {
    try {
      await cognitoIdp('GlobalSignOut', { AccessToken: accessToken }, region)
    } catch {
      // Token may already be expired/invalid — the local logout already succeeded.
    }
  }

  return { ok: true }
})

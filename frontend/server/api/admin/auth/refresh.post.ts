import {
  cognitoIdp,
  secretHash,
  setAdminSession,
  clearAdminSession,
  REFRESH_COOKIE,
  USER_COOKIE,
  type CognitoTokens,
} from '~~/server/utils/admin-auth'

/**
 * Mint fresh ID/access tokens from the stored refresh token. The refresh token
 * itself is not rotated by Cognito's REFRESH_TOKEN_AUTH flow, so we keep it.
 * SECRET_HASH for this flow is still computed from the original username, which
 * we stored in the `b4p_usr` cookie at login.
 */
export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const region = config.cognitoRegion as string
  const clientId = config.cognitoClientId as string
  const clientSecret = config.cognitoClientSecret as string

  const refreshToken = getCookie(event, REFRESH_COOKIE)
  const username = getCookie(event, USER_COOKIE)
  if (!refreshToken || !username) {
    clearAdminSession(event)
    throw createError({ statusCode: 401, statusMessage: 'Sesiune expirată', data: { error: 'unauthorized' } })
  }

  let result: { AuthenticationResult?: { IdToken: string; AccessToken: string; ExpiresIn: number } }
  try {
    result = await cognitoIdp('InitiateAuth', {
      AuthFlow: 'REFRESH_TOKEN_AUTH',
      ClientId: clientId,
      AuthParameters: {
        REFRESH_TOKEN: refreshToken,
        SECRET_HASH: secretHash(username, clientId, clientSecret),
      },
    }, region)
  } catch (err) {
    clearAdminSession(event)
    throw err
  }

  const auth = result.AuthenticationResult
  if (!auth?.IdToken) {
    clearAdminSession(event)
    throw createError({ statusCode: 401, statusMessage: 'Sesiune expirată', data: { error: 'unauthorized' } })
  }

  const tokens: CognitoTokens = {
    idToken: auth.IdToken,
    accessToken: auth.AccessToken,
    refreshToken, // unchanged — keep the existing one
    expiresIn: auth.ExpiresIn,
  }
  setAdminSession(event, tokens, username)

  return { ok: true }
})

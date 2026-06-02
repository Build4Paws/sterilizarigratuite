import { createHmac } from 'node:crypto'
import type { H3Event } from 'h3'

/**
 * Server-side Amazon Cognito helpers for the admin auth flow.
 * See docs/ADMIN-PLAN.md. The browser never holds AWS creds or the client
 * secret — it only ever gets httpOnly session cookies it cannot read.
 *
 * SECURITY: Cognito's InitiateAuth/RespondToAuthChallenge are *unauthenticated*
 * APIs (the app authenticates with the SECRET_HASH), so these calls use plain
 * fetch — no SigV4. The real authorization gate is the Cognito authorizer on the
 * backend's `/admin/**` API Gateway routes; this module only manages the session.
 */

const ID_COOKIE = 'b4p_id'
const ACCESS_COOKIE = 'b4p_at'
const REFRESH_COOKIE = 'b4p_refresh'
const USER_COOKIE = 'b4p_usr' // Cognito username — needed to compute SECRET_HASH on refresh.

const isProd = process.env.NODE_ENV === 'production'

const baseCookie = {
  httpOnly: true,
  secure: isProd,
  sameSite: 'lax' as const,
  path: '/',
}

export interface AdminClaims {
  email: string
  username: string
  groups: string[]
  exp: number
}

export interface CognitoTokens {
  idToken: string
  accessToken: string
  refreshToken?: string
  expiresIn: number
}

interface CognitoConfig {
  region: string
  clientId: string
  clientSecret: string
}

function cognitoConfig(): CognitoConfig {
  const config = useRuntimeConfig()
  const region = config.cognitoRegion as string
  const clientId = config.cognitoClientId as string
  const clientSecret = config.cognitoClientSecret as string
  if (!region || !clientId || !clientSecret) {
    throw createError({
      statusCode: 500,
      statusMessage: 'Cognito is not configured (COGNITO_* env vars missing).',
    })
  }
  return { region, clientId, clientSecret }
}

/** SECRET_HASH = base64(HMAC-SHA256(username + clientId, clientSecret)). */
export function secretHash(username: string, clientId: string, clientSecret: string): string {
  return createHmac('sha256', clientSecret).update(username + clientId).digest('base64')
}

/** Low-level call to the Cognito IDP JSON API. Throws a clean H3 error on failure. */
export async function cognitoIdp<T = any>(action: string, payload: Record<string, unknown>, region: string): Promise<T> {
  let res: Response
  try {
    res = await fetch(`https://cognito-idp.${region}.amazonaws.com/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-amz-json-1.1',
        'X-Amz-Target': `AWSCognitoIdentityProviderService.${action}`,
      },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(10_000),
    })
  } catch (err) {
    if (err instanceof Error && err.name === 'TimeoutError') {
      throw createError({ statusCode: 503, statusMessage: 'Cognito timeout.', data: { error: 'server_error' } })
    }
    throw err
  }

  const text = await res.text()
  const data = text ? JSON.parse(text) : {}

  if (!res.ok) {
    // Cognito errors look like { __type: "NotAuthorizedException", message: "..." }.
    // Map the common ones to a stable code the client maps to RO copy; never echo
    // the raw Cognito message (it can leak whether a user exists).
    const type = String(data.__type ?? '')
    const codeByType: Record<string, string> = {
      NotAuthorizedException: 'invalid_credentials',
      UserNotFoundException: 'invalid_credentials',
      CodeMismatchException: 'mfa_invalid',
      ExpiredCodeException: 'mfa_invalid',
      InvalidPasswordException: 'weak_password',
      TooManyRequestsException: 'rate_limited',
      TooManyFailedAttemptsException: 'rate_limited',
      PasswordResetRequiredException: 'password_reset_required',
    }
    throw createError({
      statusCode: res.status === 400 ? 401 : res.status,
      statusMessage: 'Cognito auth error',
      data: { error: codeByType[type] ?? 'auth_failed' },
    })
  }

  return data as T
}

/** Decode a JWT payload WITHOUT verifying the signature (UX/exp checks only). */
export function decodeJwt(token: string): Record<string, any> | null {
  const part = token.split('.')[1]
  if (!part) return null
  try {
    return JSON.parse(Buffer.from(part, 'base64url').toString('utf8'))
  } catch {
    return null
  }
}

/** Persist the session in httpOnly cookies. */
export function setAdminSession(event: H3Event, tokens: CognitoTokens, username: string): void {
  // Cookie lifetime tracks the refresh token (a staff shift); the idToken inside
  // is short-lived and refreshed in place. We still re-check `exp` on every read.
  const maxAge = 60 * 60 * 12
  setCookie(event, ID_COOKIE, tokens.idToken, { ...baseCookie, maxAge })
  setCookie(event, ACCESS_COOKIE, tokens.accessToken, { ...baseCookie, maxAge })
  if (tokens.refreshToken) {
    setCookie(event, REFRESH_COOKIE, tokens.refreshToken, { ...baseCookie, maxAge })
  }
  setCookie(event, USER_COOKIE, username, { ...baseCookie, maxAge })
}

export function clearAdminSession(event: H3Event): void {
  for (const name of [ID_COOKIE, ACCESS_COOKIE, REFRESH_COOKIE, USER_COOKIE]) {
    deleteCookie(event, name, { ...baseCookie })
  }
}

/**
 * Read + validate the current session from cookies. Returns claims if the
 * idToken is present, decodable, not expired, and carries the `admins` group.
 * NOTE: signature is NOT cryptographically verified here — the backend's Cognito
 * authorizer is the real gate. This is sufficient for UX redirects + to prevent
 * unauthenticated proxy calls (a forged token is rejected upstream, leaking nothing).
 * Hardening TODO: verify RS256 against the pool JWKS for defense in depth.
 */
export function getAdminSession(event: H3Event): AdminClaims | null {
  const idToken = getCookie(event, ID_COOKIE)
  if (!idToken) return null
  const claims = decodeJwt(idToken)
  if (!claims) return null
  const now = Math.floor(Date.now() / 1000)
  if (typeof claims.exp === 'number' && claims.exp <= now) return null
  const groups: string[] = Array.isArray(claims['cognito:groups']) ? claims['cognito:groups'] : []
  if (!groups.includes('admins')) return null
  return {
    email: String(claims.email ?? claims['cognito:username'] ?? ''),
    username: String(claims['cognito:username'] ?? claims.email ?? ''),
    groups,
    exp: Number(claims.exp ?? 0),
  }
}

/** Guard for `server/api/admin/**` routes. Returns the idToken to forward upstream, or throws 401. */
export function requireAdminSession(event: H3Event): { idToken: string; claims: AdminClaims } {
  const claims = getAdminSession(event)
  const idToken = getCookie(event, ID_COOKIE)
  if (!claims || !idToken) {
    throw createError({ statusCode: 401, statusMessage: 'Neautentificat', data: { error: 'unauthorized' } })
  }
  return { idToken, claims }
}

/**
 * Proxy a request to a backend `/admin/**` endpoint, authenticated with the
 * admin's Cognito idToken (Bearer). Mirrors the shape of the public proxy routes
 * but uses the Cognito authorizer instead of SigV4. Returns the raw Response.
 */
export async function forwardAdmin(
  event: H3Event,
  path: string,
  init: RequestInit = {},
  timeoutMs = 10_000,
): Promise<Response> {
  const { idToken } = requireAdminSession(event)
  const config = useRuntimeConfig()
  const apiBase = config.awsApiBase as string
  if (!apiBase) {
    throw createError({ statusCode: 500, statusMessage: 'Server is missing API base URL' })
  }
  const baseUrl = /^https?:\/\//i.test(apiBase) ? apiBase : `https://${apiBase}`
  try {
    return await fetch(`${baseUrl}/admin${path}`, {
      ...init,
      headers: {
        Accept: 'application/json',
        ...(init.headers ?? {}),
        Authorization: `Bearer ${idToken}`,
      },
      signal: AbortSignal.timeout(timeoutMs),
    })
  } catch (err) {
    if (err instanceof Error && err.name === 'TimeoutError') {
      throw createError({ statusCode: 503, statusMessage: 'Upstream timeout.', data: { error: 'server_error' } })
    }
    throw err
  }
}

/**
 * GET proxy for `/admin/**` reads. Gates on the admin session (401 if absent),
 * forwards to the backend `/admin{path}` with the Cognito Bearer token, and
 * returns the parsed body — or re-throws the upstream error with its body so the
 * client error mapper can render Romanian copy.
 */
export async function adminProxyGet<T>(event: H3Event, path: string): Promise<T> {
  const res = await forwardAdmin(event, path) // requireAdminSession runs inside
  setResponseHeader(event, 'cache-control', 'no-store')
  const text = await res.text()
  if (!res.ok) {
    let data: unknown = text
    try { data = JSON.parse(text) } catch { /* keep raw text */ }
    throw createError({ statusCode: res.status, statusMessage: res.statusText || 'Upstream error', data })
  }
  return (text ? JSON.parse(text) : {}) as T
}

/**
 * Mutation proxy (POST/PATCH). Gates on the admin session, forwards to the
 * backend, and re-throws upstream errors with their body so the client error
 * mapper can render Romanian copy. No stub — mutations must hit the real backend.
 */
export async function adminProxySend<T = unknown>(
  event: H3Event,
  path: string,
  init: RequestInit,
): Promise<T> {
  const res = await forwardAdmin(event, path, init)
  const text = await res.text()
  if (!res.ok) {
    let data: unknown = text
    try { data = JSON.parse(text) } catch { /* keep raw text */ }
    throw createError({ statusCode: res.status, statusMessage: res.statusText || 'Upstream error', data })
  }
  setResponseHeader(event, 'cache-control', 'no-store')
  return (text ? JSON.parse(text) : {}) as T
}

export { ID_COOKIE, ACCESS_COOKIE, REFRESH_COOKIE, USER_COOKIE }

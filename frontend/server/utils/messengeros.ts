import { requireAdminSession } from '~~/server/utils/admin-auth'

/**
 * Server-side proxy to the messengeros `/backend/*` API. Admin-gated; the
 * browser never talks to messengeros directly (same boundary as the AWS proxy).
 *
 * Auth: `/backend/*` requires a Bearer JWT from `POST /backend/auth/login`
 * (the `x-api-key` is only for the `/2.0/send` endpoint). We log in once with a
 * server-only service account and cache the JWT in memory (the EC2 Nuxt process
 * is long-lived), re-logging in when it expires or is rejected. Credentials and
 * the token never reach the browser.
 */
const BASE = 'https://app.messengeros.com/backend'

let _token: string | null = null
let _exp = 0 // token expiry, epoch seconds
let _loginInFlight: Promise<string> | null = null

function decodeExp(jwt: string): number {
  try {
    const claims = JSON.parse(Buffer.from(jwt.split('.')[1] ?? '', 'base64url').toString('utf8'))
    return typeof claims.exp === 'number' ? claims.exp : 0
  } catch {
    return 0
  }
}

async function login(): Promise<string> {
  const { messengerosEmail, messengerosPassword } = useRuntimeConfig()
  if (!messengerosEmail || !messengerosPassword) {
    throw createError({
      statusCode: 500,
      statusMessage: 'Messengeros credentials not configured',
      data: { error: 'server_error' },
    })
  }
  const res = await fetch(`${BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({
      email: messengerosEmail,
      password: messengerosPassword,
      rememberMe: true,
      trustedDeviceToken: '',
    }),
    signal: AbortSignal.timeout(10_000),
  })
  if (!res.ok) {
    throw createError({ statusCode: 502, statusMessage: 'Messengeros login failed', data: { error: 'messengeros_auth_failed' } })
  }
  const body = (await res.json()) as { token?: string }
  if (!body?.token) {
    throw createError({ statusCode: 502, statusMessage: 'Messengeros login returned no token', data: { error: 'messengeros_auth_failed' } })
  }
  _token = body.token
  _exp = decodeExp(body.token) || Math.floor(Date.now() / 1000) + 3000
  return _token
}

/** Cached JWT, refreshed when missing/near-expiry (60s margin) or `force`d. */
async function getToken(force = false): Promise<string> {
  const now = Math.floor(Date.now() / 1000)
  if (!force && _token && now < _exp - 60) return _token
  if (!_loginInFlight) {
    _loginInFlight = login().finally(() => { _loginInFlight = null })
  }
  return _loginInFlight
}

function call(path: string, init: RequestInit, token: string): Promise<Response> {
  return fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...(init.headers ?? {}),
    },
    signal: AbortSignal.timeout(10_000),
  })
}

export async function messengerosFetch<T = unknown>(
  event: import('h3').H3Event,
  path: string,
  init: RequestInit = {},
): Promise<T> {
  requireAdminSession(event) // throws 401 unless an authenticated admin

  let res: Response
  try {
    res = await call(path, init, await getToken())
    if (res.status === 401) {
      // Token rejected/expired → re-login once and retry.
      res = await call(path, init, await getToken(true))
    }
  } catch (err) {
    if (err instanceof Error && err.name === 'TimeoutError') {
      throw createError({ statusCode: 503, statusMessage: 'Messengeros timeout', data: { error: 'server_error' } })
    }
    throw err
  }

  const text = await res.text()
  setResponseHeader(event, 'cache-control', 'no-store')
  if (!res.ok) {
    let detail: unknown = text
    try { detail = JSON.parse(text) } catch { /* keep raw text */ }
    throw createError({
      statusCode: res.status,
      statusMessage: res.statusText || 'Messengeros error',
      data: { error: 'messengeros_error', detail },
    })
  }
  return (text ? JSON.parse(text) : {}) as T
}

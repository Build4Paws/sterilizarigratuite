import { AwsClient } from 'aws4fetch'
import type { H3Event } from 'h3'

/**
 * Proxy a request to a PUBLIC AWS API Gateway route, SigV4-signed (service
 * `execute-api`). Same pattern as register.post.ts, factored out so the
 * magic-link routes (`/m/**`) stay tiny. Server-only AWS creds — the browser
 * never reaches AWS directly.
 *
 * Re-throws upstream non-2xx with the backend body attached as `data` so the
 * client's `extractApiError` can map codes (e.g. `token_invalid`) to Romanian
 * copy. Sets `cache-control: no-store` on success (token-scoped, never cache).
 */
export async function proxyAws<T = unknown>(
  event: H3Event,
  path: string,
  init: RequestInit = {},
  timeoutMs?: number,
): Promise<T> {
  const {
    awsAccessKeyId,
    awsSecretAccessKey,
    awsSessionToken,
    awsRegion,
    awsApiBase,
  } = useRuntimeConfig()

  if (!awsAccessKeyId || !awsSecretAccessKey || !awsApiBase) {
    throw createError({
      statusCode: 500,
      statusMessage: 'Server is missing AWS credentials or API base URL',
    })
  }

  const aws = new AwsClient({
    accessKeyId: awsAccessKeyId as string,
    secretAccessKey: awsSecretAccessKey as string,
    sessionToken: (awsSessionToken as string) || undefined,
    region: awsRegion as string,
    service: 'execute-api',
  })

  const apiBase = awsApiBase as string
  const baseUrl = /^https?:\/\//i.test(apiBase) ? apiBase : `https://${apiBase}`

  const res = await fetchUpstream(aws, `${baseUrl}${path}`, init, timeoutMs)
  const text = await res.text()

  if (!res.ok) {
    let data: unknown = text
    try { data = JSON.parse(text) } catch { /* keep raw text */ }
    throw createError({ statusCode: res.status, statusMessage: res.statusText || 'Upstream error', data })
  }

  setResponseHeader(event, 'cache-control', 'no-store')
  return (text ? JSON.parse(text) : {}) as T
}

import { AwsClient } from 'aws4fetch'

/**
 * Signed proxy for GET /counties/{code}/localities?q=...
 *
 * Returns { localities: [{ id, name }] } from the backend as-is.
 * Cached 24 h — locality lists rarely change.
 * No captcha needed (read endpoint).
 */
export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const {
    awsAccessKeyId,
    awsSecretAccessKey,
    awsSessionToken,
    awsRegion,
    awsApiBase,
  } = config

  if (!awsAccessKeyId || !awsSecretAccessKey || !awsApiBase) {
    throw createError({
      statusCode: 500,
      statusMessage: 'Server is missing AWS credentials or API base URL',
    })
  }

  // Validate county code — 1-2 uppercase letters (e.g. "SV", "IF").
  const rawCode = getRouterParam(event, 'code') ?? ''
  if (!rawCode || !/^[A-Za-z]{1,2}$/.test(rawCode)) {
    throw createError({ statusCode: 400, statusMessage: 'Invalid county code' })
  }
  const code = rawCode.toUpperCase()

  // Optional search query — trimmed, capped at 50 chars.
  const qs = getQuery(event)
  const q = String(qs.q ?? '').trim().slice(0, 50)

  const aws = new AwsClient({
    accessKeyId: awsAccessKeyId as string,
    secretAccessKey: awsSecretAccessKey as string,
    sessionToken: (awsSessionToken as string) || undefined,
    region: awsRegion as string,
    service: 'execute-api',
  })

  const baseUrl = /^https?:\/\//i.test(awsApiBase as string)
    ? (awsApiBase as string)
    : `https://${awsApiBase}`

  const upstream = `${baseUrl}/counties/${code}/localities${q ? `?q=${encodeURIComponent(q)}` : ''}`

  const res = await fetchUpstream(aws, upstream, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  })

  const text = await res.text()

  if (!res.ok) {
    throw createError({
      statusCode: res.status,
      statusMessage: res.statusText || 'Upstream error',
      data: text,
    })
  }

  // No frontend caching — always serve what the backend returns.
  setResponseHeader(event, 'cache-control', 'no-store')

  try {
    return JSON.parse(text)
  } catch {
    setResponseHeader(event, 'content-type', res.headers.get('content-type') ?? 'application/json')
    return text
  }
})

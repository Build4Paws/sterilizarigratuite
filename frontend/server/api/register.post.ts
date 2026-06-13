import { AwsClient } from 'aws4fetch'

/**
 * Proxy for POST /register.
 * Cloudflare Turnstile is verified HERE (this box has internet egress; the
 * VPC Lambda does not), then we forward the body — including the now-verified
 * turnstileToken — to the backend SigV4-signed. The Lambda runs with
 * TURNSTILE_ENABLED=false so it trusts this proxy and doesn't re-verify.
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

  const body = (await readBody(event)) as Record<string, unknown> | null

  // Captcha gate (before signing/forwarding). Maps to RO copy via captcha_failed.
  const ok = await verifyTurnstile(
    body?.turnstileToken as string | undefined,
    getRequestIP(event, { xForwardedFor: true }),
  )
  if (!ok) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Captcha invalid',
      data: { error: 'captcha_failed' },
    })
  }

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

  const res = await fetchUpstream(aws, `${baseUrl}/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body ?? {}),
  })

  const text = await res.text()

  if (!res.ok) {
    throw createError({
      statusCode: res.status,
      statusMessage: res.statusText || 'Upstream error',
      data: text,
    })
  }

  try {
    return JSON.parse(text)
  } catch {
    setResponseHeader(event, 'content-type', res.headers.get('content-type') ?? 'application/json')
    return text
  }
})

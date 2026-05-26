import { AwsClient } from 'aws4fetch'

/**
 * Proxy for POST /register.
 * hCaptcha verification is handled exclusively by the AWS backend —
 * we forward the full body (including hcaptchaToken) as-is and sign
 * the request with SigV4 so the backend trusts the origin.
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

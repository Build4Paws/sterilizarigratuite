import { AwsClient } from 'aws4fetch'

/**
 * Public read of approved + upcoming campaigns. Optional `?county=AB` filter
 * (2-letter `auto` code). The backend already filters by status and end date,
 * so the frontend trusts the response.
 *
 * No hCaptcha here — this is a read endpoint.
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

  const query = getQuery(event)
  const county = String(query.county ?? '').trim().toUpperCase()

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

  const url = county
    ? `${baseUrl}/campaigns?county=${encodeURIComponent(county)}`
    : `${baseUrl}/campaigns`

  const res = await aws.fetch(url, {
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

  setResponseHeader(event, 'cache-control', 'public, max-age=60, s-maxage=300')

  try {
    return JSON.parse(text)
  } catch {
    setResponseHeader(event, 'content-type', res.headers.get('content-type') ?? 'application/json')
    return text
  }
})

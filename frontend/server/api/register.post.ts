import { AwsClient } from 'aws4fetch'

interface HcaptchaVerifyResponse {
  success: boolean
  'error-codes'?: string[]
}

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const {
    awsAccessKeyId,
    awsSecretAccessKey,
    awsSessionToken,
    awsRegion,
    awsApiBase,
    hcaptchaSecretKey,
  } = config

  if (!awsAccessKeyId || !awsSecretAccessKey || !awsApiBase) {
    throw createError({
      statusCode: 500,
      statusMessage: 'Server is missing AWS credentials or API base URL',
    })
  }

  const body = (await readBody(event)) as Record<string, unknown> | null
  const { hcaptchaToken, ...registration } = body ?? {}

  const secret = hcaptchaSecretKey as string
  if (!secret && !import.meta.dev) {
    throw createError({ statusCode: 500, statusMessage: 'Captcha not configured.' })
  }
  if (secret) {
    if (typeof hcaptchaToken !== 'string' || !hcaptchaToken) {
      throw createError({
        statusCode: 400,
        statusMessage: 'Captcha token lipsă.',
        data: { error: 'captcha_failed' },
      })
    }
    let verify: HcaptchaVerifyResponse
    try {
      verify = await $fetch<HcaptchaVerifyResponse>('https://api.hcaptcha.com/siteverify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ secret, response: hcaptchaToken }).toString(),
        signal: AbortSignal.timeout(5_000),
      })
    } catch (err) {
      if (err instanceof Error && err.name === 'TimeoutError') {
        throw createError({ statusCode: 503, statusMessage: 'Upstream timeout.', data: { error: 'server_error' } })
      }
      throw err
    }
    if (!verify.success) {
      throw createError({
        statusCode: 400,
        statusMessage: 'Verificarea captcha a eșuat.',
        data: { error: 'captcha_failed', codes: verify['error-codes'] },
      })
    }
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
    body: JSON.stringify(registration),
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

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

  // Fail-closed when the secret is configured; skip when it's empty (dev mode).
  const secret = hcaptchaSecretKey as string
  if (secret) {
    if (typeof hcaptchaToken !== 'string' || !hcaptchaToken) {
      throw createError({ statusCode: 400, statusMessage: 'Captcha token lipsă.' })
    }
    const verify = await $fetch<HcaptchaVerifyResponse>('https://api.hcaptcha.com/siteverify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ secret, response: hcaptchaToken }).toString(),
    })
    if (!verify.success) {
      throw createError({
        statusCode: 400,
        statusMessage: 'Verificarea captcha a eșuat.',
        data: verify['error-codes'],
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

  const res = await aws.fetch(`${baseUrl}/register`, {
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

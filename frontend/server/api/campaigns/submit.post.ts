import { AwsClient } from 'aws4fetch'
import type { CampaignSubmissionResponse } from '~/types'

interface HcaptchaVerifyResponse {
  success: boolean
  'error-codes'?: string[]
}

interface OrganizersApiResponse {
  message?: string
  campaignId?: string
  [key: string]: unknown
}

export default defineEventHandler(async (event): Promise<CampaignSubmissionResponse> => {
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
  const { hcaptchaToken, ...submission } = body ?? {}

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

  const res = await fetchUpstream(aws, `${baseUrl}/organizers`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(submission),
  })

  const text = await res.text()

  if (!res.ok) {
    throw createError({
      statusCode: res.status,
      statusMessage: res.statusText || 'Upstream error',
      data: text,
    })
  }

  const apiResponse: OrganizersApiResponse = JSON.parse(text)

  return {
    message: String(apiResponse.message ?? 'Submitted'),
    campaignId: String(apiResponse.campaignId ?? crypto.randomUUID()),
    status: 'pending',
  }
})

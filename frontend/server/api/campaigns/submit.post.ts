import { AwsClient } from 'aws4fetch'
import type { CampaignSubmissionResponse } from '~/types'

interface SubmitApiResponse {
  message?: string
  submissionId?: string
  status?: string
  stats?: {
    registeredInLocality: number
    registeredInCounty: number
  }
  [key: string]: unknown
}

/**
 * Proxy for POST /campaigns/submit.
 * hCaptcha verification is handled exclusively by the AWS backend —
 * we forward the full body (including hcaptchaToken) as-is and sign
 * the request with SigV4 so the backend trusts the origin.
 */
export default defineEventHandler(async (event): Promise<CampaignSubmissionResponse> => {
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

  // Campaign submissions are slower than register: the backend verifies hCaptcha
  // (outbound call) + writes to DB + may cold-start a separate Lambda.
  // AWS API Gateway's own hard limit is 29 s, so 25 s gives us a clean 503
  // before Gateway would return its own opaque timeout.
  const res = await fetchUpstream(aws, `${baseUrl}/campaigns/submit`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(body ?? {}),
  }, 25_000)

  const text = await res.text()

  if (!res.ok) {
    throw createError({
      statusCode: res.status,
      statusMessage: res.statusText || 'Upstream error',
      data: text,
    })
  }

  const apiResponse: SubmitApiResponse = JSON.parse(text)

  return {
    message: String(apiResponse.message ?? 'Trimis cu succes'),
    submissionId: String(apiResponse.submissionId),
    status: 'pending',
    stats: apiResponse.stats,
  }
})

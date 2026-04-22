import { randomUUID } from 'node:crypto'
import type { CampaignSubmissionResponse } from '~/types'

interface HcaptchaVerifyResponse {
  success: boolean
  'error-codes'?: string[]
}

/**
 * MOCK — backend endpoint not yet implemented.
 *
 * When the real `POST /campaigns/submit` endpoint is available, replace the
 * mock body below with the AwsClient SigV4 proxy pattern from
 * `server/api/register.post.ts` (read `awsApiBase` from runtime config,
 * sign+forward the request, return the parsed JSON).
 *
 * Mock contract matches docs/CAMPAIGNS-FLOW-PLAN.md §5.1.
 */
export default defineEventHandler(async (event): Promise<CampaignSubmissionResponse> => {
  const config = useRuntimeConfig()
  const { hcaptchaSecretKey } = config

  const body = (await readBody(event)) as Record<string, unknown> | null
  const { hcaptchaToken, ...submission } = body ?? {}

  // hCaptcha verification — same fail-closed-when-secret-set pattern as register.
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

  // Mock-only: simulate a duplicate-submission conflict if the org name
  // contains the word "duplicate" — useful for testing the 409 branch.
  const orgName = String((submission as { organizationName?: unknown }).organizationName ?? '')
  if (/duplicate/i.test(orgName)) {
    throw createError({
      statusCode: 409,
      statusMessage: 'O campanie identică există deja pentru această locație și dată.',
      data: { error: 'duplicate_submission', existingSubmissionId: 'mock-existing-id' },
    })
  }

  // Pull county+locality so we can return a coherent stats block.
  const county = String((submission as { county?: unknown }).county ?? '')
  const locality = String((submission as { locality?: unknown }).locality ?? '')
  const stats = county && locality ? mockStatsFor(county, locality) : undefined

  return {
    message: 'Campaign submitted for review',
    submissionId: randomUUID(),
    status: 'pending',
    stats,
  }
})

function mockStatsFor(county: string, locality: string) {
  const localityCount = hashTo(`${county}:${locality}`, 25)
  const extraInCounty = hashTo(`${county}#`, 60)
  return {
    registeredInLocality: localityCount,
    registeredInCounty: localityCount + extraInCounty,
  }
}

function hashTo(input: string, ceiling: number): number {
  let hash = 0
  for (let i = 0; i < input.length; i++) {
    hash = (hash * 31 + input.charCodeAt(i)) >>> 0
  }
  return hash % ceiling
}

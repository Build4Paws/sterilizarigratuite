import { AwsClient } from 'aws4fetch'
import type { RegistrationsCountryResponse } from '~/types'

export default defineEventHandler(async (event): Promise<RegistrationsCountryResponse> => {
  const config = useRuntimeConfig()
  const { awsAccessKeyId, awsSecretAccessKey, awsSessionToken, awsRegion, awsApiBase } = config

  const rawBase = (awsApiBase as string) || 'https://api.sterilizarigratuite.ro'
  const baseUrl = /^https?:\/\//i.test(rawBase) ? rawBase : `https://${rawBase}`
  const upstreamUrl = `${baseUrl}/stats/registrations`

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
    region: (awsRegion as string) || 'eu-central-1',
    service: 'execute-api',
  })
  const res = await aws.fetch(upstreamUrl)
  if (!res.ok) {
    throw createError({
      statusCode: res.status,
      statusMessage: res.statusText || 'Upstream error',
      data: await res.text(),
    })
  }
  const data = (await res.json()) as RegistrationsCountryResponse

  // Normalize Ilfov: backend may return the full name instead of the 2-letter code.
  // Remove once backend ships strict ISO codes.
  if (data.byCounty && 'Ilfov' in data.byCounty && !('IF' in data.byCounty)) {
    if (process.dev) console.warn('[registrations] Backend returned "Ilfov" key — normalizing to "IF"')
    data.byCounty.IF = data.byCounty.Ilfov!
    delete data.byCounty.Ilfov
  }

  setResponseHeader(event, 'cache-control', 'public, max-age=60, s-maxage=300')

  return data
})

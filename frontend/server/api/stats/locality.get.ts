import { AwsClient } from 'aws4fetch'
import type { LocalityWaitingStats } from '~/types'

interface RegistrationsResponse {
  county: string
  registeredInCounty: number
  byLocality: Record<string, number>
  bySpecies: Record<string, number>
}

export default defineEventHandler(async (event): Promise<LocalityWaitingStats> => {
  const query = getQuery(event)
  const county = String(query.county ?? '').trim()
  const locality = String(query.locality ?? '').trim()

  if (!county || !locality) {
    throw createError({
      statusCode: 400,
      statusMessage: 'county și locality sunt obligatorii.',
    })
  }

  const config = useRuntimeConfig()
  const { awsAccessKeyId, awsSecretAccessKey, awsSessionToken, awsRegion, awsApiBase } = config

  const rawBase = (awsApiBase as string) || 'https://api.sterilizarigratuite.ro'
  const baseUrl = /^https?:\/\//i.test(rawBase) ? rawBase : `https://${rawBase}`
  const upstreamUrl = `${baseUrl}/stats/registrations?county=${encodeURIComponent(county)}`

  let data: RegistrationsResponse

  if (awsAccessKeyId && awsSecretAccessKey) {
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
    data = (await res.json()) as RegistrationsResponse
  } else {
    data = await $fetch<RegistrationsResponse>(upstreamUrl)
  }

  return {
    county: data.county,
    locality,
    registeredInLocality: data.byLocality[locality] ?? 0,
    registeredInCounty: data.registeredInCounty,
  }
})

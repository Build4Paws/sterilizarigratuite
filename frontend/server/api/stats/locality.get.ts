import { AwsClient } from 'aws4fetch'
import type { LocalityWaitingStats } from '~/types'

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

  if (!awsAccessKeyId || !awsSecretAccessKey || !awsApiBase) {
    throw createError({
      statusCode: 500,
      statusMessage: 'Server is missing AWS credentials or API base URL',
    })
  }

  const rawBase = (awsApiBase as string) || ''
  const baseUrl = /^https?:\/\//i.test(rawBase) ? rawBase : `https://${rawBase}`

  const upstreamUrl = `${baseUrl}/stats/locality?county=${encodeURIComponent(county)}&locality=${encodeURIComponent(locality)}`

  const aws = new AwsClient({
    accessKeyId: awsAccessKeyId as string,
    secretAccessKey: awsSecretAccessKey as string,
    sessionToken: (awsSessionToken as string) || undefined,
    region: (awsRegion as string) || 'eu-central-1',
    service: 'execute-api',
  })

  const res = await fetchUpstream(aws, upstreamUrl)

  if (!res.ok) {
    throw createError({
      statusCode: res.status,
      statusMessage: res.statusText || 'Upstream error',
      data: await res.text(),
    })
  }

  // No frontend caching — always serve what the backend returns.
  setResponseHeader(event, 'cache-control', 'no-store')

  return (await res.json()) as LocalityWaitingStats
})

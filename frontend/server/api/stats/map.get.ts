import { AwsClient } from 'aws4fetch'
import type { MapStats, RegistrationsCountryResponse } from '~/types'

export default defineEventHandler(async (event): Promise<RegistrationsCountryResponse> => {
  const config = useRuntimeConfig()
  const { awsAccessKeyId, awsSecretAccessKey, awsSessionToken, awsRegion, awsApiBase } = config

  if (!awsAccessKeyId || !awsSecretAccessKey || !awsApiBase) {
    throw createError({
      statusCode: 500,
      statusMessage: 'Server is missing AWS credentials or API base URL',
    })
  }

  const query = getQuery(event)
  const view = String(query.view ?? '').trim()

  const rawBase = (awsApiBase as string) || ''
  const baseUrl = /^https?:\/\//i.test(rawBase) ? rawBase : `https://${rawBase}`
  const upstreamUrl = view
    ? `${baseUrl}/stats/map?view=${encodeURIComponent(view)}`
    : `${baseUrl}/stats/map`

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

  const mapStats = (await res.json()) as MapStats

  // Reshape MapStats → RegistrationsCountryResponse so /harta stays stable.
  // byCounty[code].cerere already has the { total, localities, species } shape
  // that CountyStats expects. Guard against null/undefined if the endpoint is
  // not yet fully deployed or returns a partial payload.
  const byCounty: RegistrationsCountryResponse['byCounty'] = {}
  for (const [code, countyData] of Object.entries(mapStats.byCounty ?? {})) {
    if (countyData?.cerere) byCounty[code] = countyData.cerere
  }

  // Normalize Ilfov: backend may return the full name instead of the 2-letter code.
  // Keep defensively until backend confirms strict ISO codes everywhere.
  if ('Ilfov' in byCounty && !('IF' in byCounty)) {
    if (process.dev) console.warn('[stats/map] Backend returned "Ilfov" key — normalizing to "IF"')
    byCounty.IF = byCounty.Ilfov!
    delete byCounty.Ilfov
  }

  setResponseHeader(event, 'cache-control', 'public, max-age=60, s-maxage=300')

  return {
    byCounty,
    totalRegistrations: mapStats.totals.registrations,
  }
})

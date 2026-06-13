import { AwsClient } from 'aws4fetch'
import type { PublicCampaign } from '~/types'

/**
 * Maps the API v2 wire shape (snake_case, `species_slots`) to the documented
 * camelCase `PublicCampaign` contract the frontend consumes. Shaping the
 * upstream response here keeps the type + `normalizePublicCampaign` mapper
 * stable for every consumer (see CLAUDE.md "data shaping lives in the backend").
 */
function mapCampaign(c: Record<string, any>): PublicCampaign {
  return {
    submissionId: c.submission_id,
    organizationName: c.organization_name,
    phonePublic: c.phone_public,
    county: c.county_code,
    countyName: c.county_name,
    locality: c.locality_name,
    address: c.address,
    dateStart: c.date_start,
    dateEnd: c.date_end ?? null,
    // v2 sends "HH:MM:SS"; the card renders the raw string, so trim to "HH:MM".
    timeStart: (c.time_start ?? '').slice(0, 5),
    timeEnd: (c.time_end ?? '').slice(0, 5),
    doctor: c.doctor ?? null,
    species: c.species_slots ?? {},
  }
}

/**
 * Public read of approved + upcoming campaigns. Optional `?county=AB` filter
 * (2-letter `auto` code). The backend already filters by status and end date,
 * so the frontend trusts the response.
 *
 * No captcha here — this is a read endpoint.
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

  const res = await fetchUpstream(aws, url, {
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

  // No frontend caching — always serve what the backend returns. Caching is
  // the backend's responsibility.
  setResponseHeader(event, 'cache-control', 'no-store')

  try {
    const parsed = JSON.parse(text)
    const campaigns = Array.isArray(parsed?.campaigns) ? parsed.campaigns : []
    return { campaigns: campaigns.map(mapCampaign) }
  } catch {
    setResponseHeader(event, 'content-type', res.headers.get('content-type') ?? 'application/json')
    return text
  }
})

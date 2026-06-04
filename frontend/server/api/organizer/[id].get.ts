import { AwsClient } from 'aws4fetch'
import type { OrganizerCampaign, OrganizerProfile } from '~/types'

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

/**
 * Normalizes one campaign to the camelCase `OrganizerCampaign` contract. The
 * dev backend returns camelCase already, but the `/campaigns` endpoint proves
 * prod can send snake_case — so we read either key. Shaping here keeps the type
 * stable for the page (see CLAUDE.md "data shaping lives in the backend").
 */
function mapCampaign(c: Record<string, any>): OrganizerCampaign {
  return {
    submissionId: c.submissionId ?? c.submission_id ?? '',
    status: c.status ?? '',
    county: c.county ?? c.county_code ?? '',
    locality: c.locality ?? c.locality_name ?? '',
    address: c.address ?? '',
    dateStart: c.dateStart ?? c.date_start ?? '',
    dateEnd: c.dateEnd ?? c.date_end ?? null,
    // Some shapes send "HH:MM:SS" — trim to "HH:MM" to match the card.
    timeStart: (c.timeStart ?? c.time_start ?? '').slice(0, 5),
    timeEnd: (c.timeEnd ?? c.time_end ?? '').slice(0, 5),
    createdAt: c.createdAt ?? c.created_at ?? '',
    species: c.species ?? c.species_slots ?? {},
  }
}

function mapOrganizer(raw: Record<string, any>): OrganizerProfile {
  const campaigns = Array.isArray(raw.campaigns) ? raw.campaigns : []
  return {
    organizationName: raw.organizationName ?? raw.organization_name ?? '',
    campaigns: campaigns.map(mapCampaign),
  }
}

export default defineEventHandler(async (event): Promise<OrganizerProfile> => {
  const id = getRouterParam(event, 'id') ?? ''

  if (!UUID_RE.test(id)) {
    throw createError({
      statusCode: 400,
      statusMessage: 'ID organizator invalid.',
      data: { error: 'invalid_id' },
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

  const aws = new AwsClient({
    accessKeyId: awsAccessKeyId as string,
    secretAccessKey: awsSecretAccessKey as string,
    sessionToken: (awsSessionToken as string) || undefined,
    region: (awsRegion as string) || 'eu-central-1',
    service: 'execute-api',
  })

  const res = await fetchUpstream(aws, `${baseUrl}/organizer/${id}`, {
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

  // No frontend caching — always serve what the backend returns.
  setResponseHeader(event, 'cache-control', 'no-store')

  return mapOrganizer(JSON.parse(text))
})

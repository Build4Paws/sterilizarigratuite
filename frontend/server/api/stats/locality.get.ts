import type { LocalityWaitingStats } from '~/types'

/**
 * MOCK — backend endpoint not yet implemented.
 *
 * When the real `GET /stats/locality?county=...&locality=...` endpoint is
 * available, replace the mock body below with the AwsClient SigV4 proxy
 * pattern from `server/api/register.post.ts` (read `awsApiBase` from
 * runtime config, sign+forward the request, return the parsed JSON).
 *
 * Mock contract matches docs/CAMPAIGNS-FLOW-PLAN.md §5.2.
 */
export default defineEventHandler((event): LocalityWaitingStats => {
  const query = getQuery(event)
  const county = String(query.county ?? '').trim()
  const locality = String(query.locality ?? '').trim()

  if (!county || !locality) {
    throw createError({
      statusCode: 400,
      statusMessage: 'county și locality sunt obligatorii.',
    })
  }

  // Deterministic pseudo-random counts so the same locality always returns
  // the same numbers during dev — easier to eyeball.
  const localityCount = hashTo(`${county}:${locality}`, 25)
  const extraInCounty = hashTo(`${county}#`, 60)
  const countyCount = localityCount + extraInCounty

  return {
    county,
    locality,
    registeredInLocality: localityCount,
    registeredInCounty: countyCount,
  }
})

function hashTo(input: string, ceiling: number): number {
  let hash = 0
  for (let i = 0; i < input.length; i++) {
    hash = (hash * 31 + input.charCodeAt(i)) >>> 0
  }
  return hash % ceiling
}

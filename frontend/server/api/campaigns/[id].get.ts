import { AwsClient } from 'aws4fetch'
import type { PublicCampaign } from '~/types'

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

export default defineEventHandler(async (event): Promise<PublicCampaign> => {
  const id = getRouterParam(event, 'id') ?? ''

  if (!UUID_RE.test(id)) {
    throw createError({
      statusCode: 400,
      statusMessage: 'ID campanie invalid.',
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

  const res = await fetchUpstream(aws, `${baseUrl}/campaigns/${id}`, {
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

  setResponseHeader(event, 'cache-control', 'public, max-age=60')

  return JSON.parse(text) as PublicCampaign
})

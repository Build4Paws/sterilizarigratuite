import type { AwsClient } from 'aws4fetch'

const AWS_TIMEOUT_MS = 10_000

// Wraps aws.fetch with a hard timeout and converts a TimeoutError into a clean 503.
export async function fetchUpstream(aws: AwsClient, url: string, init?: RequestInit): Promise<Response> {
  try {
    return await aws.fetch(url, { ...init, signal: AbortSignal.timeout(AWS_TIMEOUT_MS) })
  } catch (err) {
    if (err instanceof Error && err.name === 'TimeoutError') {
      throw createError({ statusCode: 503, statusMessage: 'Upstream timeout.', data: { error: 'server_error' } })
    }
    throw err
  }
}

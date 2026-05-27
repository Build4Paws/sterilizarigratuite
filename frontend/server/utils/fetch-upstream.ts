import type { AwsClient } from 'aws4fetch'

const DEFAULT_TIMEOUT_MS = 10_000

/**
 * Wraps aws.fetch with a hard timeout and converts a TimeoutError into a clean 503.
 * Pass `timeoutMs` to override the default per-call (e.g. slower write endpoints).
 */
export async function fetchUpstream(
  aws: AwsClient,
  url: string,
  init?: RequestInit,
  timeoutMs = DEFAULT_TIMEOUT_MS,
): Promise<Response> {
  try {
    return await aws.fetch(url, { ...init, signal: AbortSignal.timeout(timeoutMs) })
  } catch (err) {
    if (err instanceof Error && err.name === 'TimeoutError') {
      throw createError({ statusCode: 503, statusMessage: 'Upstream timeout.', data: { error: 'server_error' } })
    }
    throw err
  }
}

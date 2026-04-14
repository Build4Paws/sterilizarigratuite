import type { UseFetchOptions } from 'nuxt/app'

export function useApi<T>(path: string, options?: UseFetchOptions<T>) {
  const config = useRuntimeConfig()

  return useFetch<T>(path, {
    baseURL: config.public.apiBase as string,
    ...options,
  })
}

export function $api<T>(path: string, options?: RequestInit): Promise<T> {
  const config = useRuntimeConfig()
  const baseURL = config.public.apiBase as string

  return $fetch<T>(path, {
    baseURL,
    ...options,
  })
}

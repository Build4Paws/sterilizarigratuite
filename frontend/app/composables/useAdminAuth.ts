import type { AdminMe } from '~/types'

/**
 * Admin identity + logout. `me` is fetched once and shared (Nuxt payload key),
 * so the layout header and any page can read the current admin without refetching.
 */
export function useAdminAuth() {
  const { data: me, refresh } = useFetch<AdminMe>('/api/admin/auth/me', {
    key: 'admin-me',
    // The route middleware already guards access; swallow the 401 here so the
    // layout doesn't throw — it just renders without an email until refreshed.
    default: () => null as unknown as AdminMe,
  })

  async function logout() {
    await $fetch('/api/admin/auth/logout', { method: 'POST' })
    await navigateTo('/admin/login')
  }

  return { me, refresh, logout }
}

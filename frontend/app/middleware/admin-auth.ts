/**
 * Guards every `/admin/**` page except the login screen. Verifies the session
 * via GET /api/admin/auth/me (cookie-based). On failure → redirect to login with
 * a `next` param so we can return the admin after sign-in.
 *
 * `useRequestFetch()` forwards the incoming cookies during SSR so the check works
 * on the server render too — not just on client navigation.
 *
 * Phase 1: no silent refresh here; an expired idToken sends the admin to login.
 * (Refresh-in-place is a later polish — see docs/ADMIN-PLAN.md.)
 */
export default defineNuxtRouteMiddleware(async (to) => {
  if (to.path === '/admin/login') return

  const requestFetch = useRequestFetch()
  try {
    await requestFetch('/api/admin/auth/me')
  } catch {
    return navigateTo(`/admin/login?next=${encodeURIComponent(to.fullPath)}`)
  }
})

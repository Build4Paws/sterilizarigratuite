// GDPR consent state for analytics cookies (Google Analytics / gtag).
//
// The choice is stored in a first-party cookie so it survives reloads and is
// readable during SSR (no banner flash for users who already decided). Values:
//   'granted' → user accepted analytics; GA may set cookies.
//   'denied'  → user refused; GA stays in Consent Mode (cookieless).
//   null      → undecided; the banner is shown.
//
// The analytics plugin (`plugins/analytics.client.ts`) watches this state and
// calls `gtag('consent', 'update', …)` accordingly.

export type ConsentValue = 'granted' | 'denied'

// EU guidance: re-ask for consent roughly every 6 months.
const CONSENT_MAX_AGE = 60 * 60 * 24 * 180

export function useCookieConsent() {
  const consent = useCookie<ConsentValue | null>('analytics-consent', {
    default: () => null,
    maxAge: CONSENT_MAX_AGE,
    sameSite: 'lax',
    // Not `secure` in dev (localhost is http); Nuxt sets it automatically on https.
    path: '/',
  })

  const decided = computed(() => consent.value !== null)
  const granted = computed(() => consent.value === 'granted')

  function accept() {
    consent.value = 'granted'
  }

  function decline() {
    consent.value = 'denied'
  }

  return { consent, decided, granted, accept, decline }
}

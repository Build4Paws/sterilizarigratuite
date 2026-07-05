// Google Analytics 4 (gtag.js), loaded via @nuxt/scripts and gated on GDPR
// consent.
//
// Strict, unambiguous compliance: gtag.js is NOT loaded until the user accepts
// in the cookie banner. The script uses `trigger: 'manual'`, so nothing is
// fetched — no script, no `_ga*` cookies, no network pings — until we call
// `load()`. We only call it once consent is granted (immediately on later
// visits where the stored choice is already 'granted', or when the user accepts
// during this session).
//
// A Consent Mode v2 baseline is declared in `onBeforeGtagStart`; it runs only
// after consent, so analytics storage is granted and ad signals stay denied
// (GA4-only site, no advertising tags).
//
// GA measurement id comes from runtimeConfig.public.googleAnalyticsId
// (env: NUXT_PUBLIC_GA_ID). Empty id → analytics disabled entirely (dev).

export default defineNuxtPlugin(() => {
  const { public: { googleAnalyticsId } } = useRuntimeConfig()
  if (!googleAnalyticsId) return

  const { granted } = useCookieConsent()

  const ga = useScriptGoogleAnalytics({
    id: googleAnalyticsId,
    scriptOptions: {
      trigger: 'manual',
    },
    onBeforeGtagStart: (gtag) => {
      gtag('consent', 'default', {
        ad_storage: 'denied',
        ad_user_data: 'denied',
        ad_personalization: 'denied',
        analytics_storage: 'granted',
      })
    },
  })

  // Load once (and only once) consent has been granted. `once` cleans up the
  // watcher after the script loads so a later revoke can't double-load.
  const stop = watch(
    granted,
    (isGranted) => {
      if (!isGranted) return
      ga.load()
      stop()
    },
    { immediate: true },
  )
})

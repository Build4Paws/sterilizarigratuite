export default defineNuxtConfig({
  compatibilityDate: '2025-05-15',

  future: {
    compatibilityVersion: 4,
  },

  ssr: true,

  app: {
    head: {
      htmlAttrs: { lang: 'ro' },
      charset: 'utf-8',
      viewport: 'width=device-width, initial-scale=1',
      link: [
        {
          rel: 'icon',
          type: 'image/svg+xml',
          href: '/favicon.svg',
        },
        {
          rel: 'preconnect',
          href: 'https://fonts.googleapis.com',
        },
        {
          rel: 'preconnect',
          href: 'https://fonts.gstatic.com',
          crossorigin: '',
        },
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=Funnel+Display:wght@300..800&family=Rethink+Sans:ital,wght@0,400..800;1,400..800&display=swap',
        },
      ],
      meta: [
        { name: 'description', content: 'Găsește campanii de sterilizare gratuită pentru câini și pisici în România. Înscrie-te și te anunțăm când apare o campanie în zona ta.' },
        { property: 'og:type', content: 'website' },
        { property: 'og:locale', content: 'ro_RO' },
      ],
      title: 'Sterilizări Gratuite — Campanii de sterilizare pentru câini și pisici',
    },
  },

  modules: [
    '@nuxtjs/seo',
    '@vueuse/nuxt',
  ],

  site: {
    url: process.env.NUXT_PUBLIC_SITE_URL || 'https://sterilizarigratuite.ro',
    name: 'Sterilizări Gratuite',
    description: 'Găsește campanii de sterilizare gratuită pentru câini și pisici în România.',
    defaultLocale: 'ro',
  },

  robots: {
    disallow: ['/m/', '/r/', '/confirmare', '/confirmare-campanie', '/admin'],
  },

  sitemap: {
    sources: ['/api/__sitemap__/urls'],
  },

  runtimeConfig: {
    awsAccessKeyId: process.env.AWS_ACCESS_KEY_ID || '',
    awsSecretAccessKey: process.env.AWS_SECRET_ACCESS_KEY || '',
    awsSessionToken: process.env.AWS_SESSION_TOKEN || '',
    awsRegion: process.env.AWS_REGION,
    awsApiBase: process.env.AWS_API_BASE,
    // Admin auth — Amazon Cognito User Pool (server-only, never exposed to the
    // browser). See docs/ADMIN-PLAN.md. The client secret stays here and is used
    // server-side to compute the SECRET_HASH; it must never reach `public.*`.
    cognitoRegion: process.env.COGNITO_REGION || process.env.AWS_REGION,
    cognitoUserPoolId: process.env.COGNITO_USER_POOL_ID || '',
    cognitoClientId: process.env.COGNITO_CLIENT_ID || '',
    cognitoClientSecret: process.env.COGNITO_CLIENT_SECRET || '',
    public: {
      hcaptchaSiteKey: process.env.NUXT_PUBLIC_HCAPTCHA_SITE_KEY || '',
    },
  },

  routeRules: {
    '/**': {
      headers: {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
        'Content-Security-Policy': [
          "default-src 'self'",
          "script-src 'self' 'unsafe-inline' https://*.hcaptcha.com https://hcaptcha.com",
          "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
          "font-src 'self' https://fonts.gstatic.com data:",
          "img-src 'self' data: https:",
          "connect-src 'self' https://*.hcaptcha.com https://hcaptcha.com",
          "frame-src https://*.hcaptcha.com https://hcaptcha.com",
          "frame-ancestors 'none'",
          "base-uri 'self'",
        ].join('; '),
      },
    },
    // `/` is prerendered via `nitro.prerender.routes` (below) instead of a
    // route rule: the route-rule form writes a dev-time payload cache under the
    // bare key `payload`, which collides with the `payload/<route>` directory
    // (ENOTDIR). Build-time prerendering is unchanged.
    //
    // NO frontend caching of backend data: `/campanii` and `/harta` render
    // backend API data and are intentionally left as plain SSR (fresh on every
    // request) — they must always reflect what the backend returns. Caching is
    // the backend's responsibility. Only static, data-free pages are prerendered.
    '/organizatori': { prerender: true },
    '/ghid-sterilizare': { prerender: true },
    // Old guide URL → new one (page renamed "Despre sterilizare" → "Ghid sterilizare").
    '/despre-sterilizare': { redirect: '/ghid-sterilizare' },
    '/despre': { redirect: '/harta' },
    '/confirmare': { robots: false, ssr: false },
    '/confirmare-campanie': { robots: false },
    // Authenticated internal admin — never indexed. Plain SSR (auth-gated).
    '/admin/**': { robots: false },
    '/campanie/**': { robots: false },
    '/m/**': { robots: false },
    '/r/**': { robots: false },
  },

  nitro: {
    prerender: {
      routes: ['/'],
    },
  },

  hooks: {
    // `nuxt build` finishes writing `.output` but leaves the esbuild keepalive
    // service running, so the process never exits and `deploy.sh` hangs forever
    // after "Build complete!". Force-exit once the Nuxt instance closes — but
    // only for build/generate; in dev `close` also fires on config-reload
    // restarts, where exiting would kill the dev server.
    close: () => {
      const cmd = process.env.npm_lifecycle_event
      if (cmd === 'build' || cmd === 'generate') {
        process.exit(0)
      }
    },
  },

  css: ['~/assets/css/main.css'],

  ogImage: {
    enabled: false,
  },

  typescript: {
    strict: true,
  },
})

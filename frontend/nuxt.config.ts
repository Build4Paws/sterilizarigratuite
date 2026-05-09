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
    disallow: ['/m/', '/r/', '/confirmare', '/confirmare-campanie'],
  },

  sitemap: {
    sources: ['/api/__sitemap__/urls'],
  },

  runtimeConfig: {
    awsAccessKeyId: process.env.AWS_ACCESS_KEY_ID || '',
    awsSecretAccessKey: process.env.AWS_SECRET_ACCESS_KEY || '',
    awsSessionToken: process.env.AWS_SESSION_TOKEN || '',
    awsRegion: process.env.AWS_REGION || 'eu-central-1',
    awsApiBase: process.env.AWS_API_BASE || 'https://api.sterilizarigratuite.ro',
    hcaptchaSecretKey: process.env.HCAPTCHA_SECRET_KEY || '',
    public: {
      hcaptchaSiteKey: process.env.NUXT_PUBLIC_HCAPTCHA_SITE_KEY || '',
    },
  },

  routeRules: {
    '/': { prerender: true },
    '/campanii': { swr: 300 },
    '/organizatori': { prerender: true },
    '/confirmare': { robots: false, ssr: false },
    '/confirmare-campanie': { robots: false },
    '/m/**': { robots: false },
    '/r/**': { robots: false },
  },

  css: ['~/assets/css/main.css'],

  image: {
    provider: 'none',
  },

  ogImage: {
    enabled: false,
  },

  typescript: {
    strict: true,
  },
})

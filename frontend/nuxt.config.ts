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
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:3001/api',
      hcaptchaSiteKey: process.env.NUXT_PUBLIC_HCAPTCHA_SITE_KEY || '',
    },
  },

  routeRules: {
    '/': { prerender: true },
    '/campanii': { swr: 300 },
    '/organizatori': { prerender: true },
    '/confirmare': { robots: false },
    '/confirmare-campanie': { robots: false },
    '/m/**': { robots: false },
    '/r/**': { robots: false },
  },

  css: ['~/assets/css/main.css'],

  typescript: {
    strict: true,
  },
})

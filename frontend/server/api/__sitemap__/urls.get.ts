import judeteData from '../../../app/assets/data/judete.json'

interface SitemapUrl {
  loc: string
  changefreq?: 'daily' | 'weekly' | 'monthly'
  priority?: number
}

export default defineEventHandler((): SitemapUrl[] => {
  const urls: SitemapUrl[] = [
    { loc: '/despre-sterilizare', changefreq: 'monthly', priority: 0.7 },
  ]

  for (const j of judeteData.judete) {
    const slug = j.nume
      .normalize('NFD')
      .replace(/[̀-ͯ]/g, '')
      .toLowerCase()
      .replace(/\s+/g, '-')

    urls.push({ loc: `/campanii?judet=${slug}`, changefreq: 'daily', priority: 0.8 })
    urls.push({ loc: `/harta?judet=${slug}`, changefreq: 'weekly', priority: 0.6 })
  }

  return urls
})

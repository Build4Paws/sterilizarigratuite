/** GET messengeros dashboard stats for a period (e.g. ?period=30d). Admin-gated proxy. */
export default defineEventHandler((event) => {
  const period = String(getQuery(event).period ?? '30d').trim() || '30d'
  return messengerosFetch(event, `/dashboard/stats?period=${encodeURIComponent(period)}`)
})

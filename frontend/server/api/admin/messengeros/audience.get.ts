/** GET messengeros audiences. Admin-gated proxy. */
export default defineEventHandler((event) => messengerosFetch(event, '/audience'))

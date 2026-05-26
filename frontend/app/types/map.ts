export type CountyMetric = 'cerere' | 'oferta' | 'istoric'

export interface CountyStats {
  total: number
  localities: Record<string, number>
  species: Record<'dog' | 'cat', number>
}

export interface RegistrationsCountryResponse {
  byCounty: Record<string, CountyStats>
  totalRegistrations: number
}

// ---------------------------------------------------------------------------
// Wire shapes for GET /stats/map
// ---------------------------------------------------------------------------

/** One approved campaign entry inside the `oferta` array per county. */
export interface MapOfertaItem {
  submissionId: string
  organizationName: string
  locality: string
  dateStart: string
  dateEnd: string | null
  timeStart: string
  timeEnd: string
  species: Partial<Record<'dog' | 'cat', number>>
}

/** Raw response shape from `GET /stats/map`. */
export interface MapStats {
  byCounty: Record<string, {
    cerere: CountyStats
    oferta: MapOfertaItem[]
  }>
  totals: {
    registrations: number
    campaigns: number
  }
}

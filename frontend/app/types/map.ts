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

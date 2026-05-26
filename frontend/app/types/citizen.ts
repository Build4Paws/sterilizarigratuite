/** UI form state — maps to reactive form fields */
export interface CitizenFormState {
  name: string
  phone?: string
  email?: string
  county: string
  locality: string
  hasDogs: boolean
  hasCats: boolean
  dogCount?: number
  catCount?: number
  gdprConsent: boolean
}

/** API payload — what we POST to /register */
export interface CitizenRegistration {
  name: string
  phone?: string
  email?: string
  county: string
  locality: string
  species: ('dog' | 'cat')[]
  dogCount?: number
  catCount?: number
  gdprConsent: boolean
}

export interface CitizenConfirmation {
  token: string
  channel: 'sms' | 'email' | 'both'
  waitingCount: number
}

/**
 * Aggregated counts returned alongside a successful registration.
 * `county` and `locality` are optional — backend `LocalityStats` shape
 * only guarantees the two count fields; the name fields may be absent.
 */
export interface RegistrationStats {
  county?: string
  locality?: string
  registeredInCounty: number
  registeredInLocality: number
}

/** Response returned by POST /register */
export interface CitizenRegistrationResponse {
  message: string
  citizenId: string
  manageToken: string
  stats: RegistrationStats
}

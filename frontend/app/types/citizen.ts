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

/** Aggregated counts returned alongside a successful registration */
export interface RegistrationStats {
  county: string
  locality: string
  registeredInCounty: number
  registeredInLocality: number
}

/** Response returned by POST /register */
export interface CitizenRegistrationResponse {
  message: string
  stats: RegistrationStats
}

export interface CitizenRegistration {
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

export interface CitizenConfirmation {
  token: string
  channel: 'sms' | 'email' | 'both'
  waitingCount: number
}

export interface CampaignSubmission {
  organizationName: string
  contactEmail: string        // private — we use this to contact the organizer
  contactPhone: string        // private — internal contact
  phonePublic: string         // shown on the public campaign card
  county: string              // county code, e.g. "SV"
  locality: string            // locality name
  address: string             // free text / multiline
  dateStart: string           // YYYY-MM-DD
  dateEnd?: string            // YYYY-MM-DD, only if multi-day
  timeStart: string           // HH:mm
  timeEnd: string             // HH:mm
  species: ('dog' | 'cat')[]
  slotsDogs?: number          // required iff 'dog' in species
  slotsCats?: number          // required iff 'cat' in species
  doctor?: string
  gdprConsent: boolean
}

export interface CampaignSubmissionResponse {
  message: string
  submissionId: string
  status: 'pending'
  stats?: {
    registeredInLocality: number
    registeredInCounty: number
  }
}

export interface LocalityWaitingStats {
  county: string
  locality: string
  registeredInLocality: number
  registeredInCounty: number
}

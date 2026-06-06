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
  /** UUID returned by POST /campaigns/submit (v1.1.1). Was `campaignId` in the legacy proxy. */
  submissionId: string
  status: 'pending'
  stats?: {
    registeredInLocality: number
    registeredInCounty: number
  }
}

/**
 * One campaign in the `GET /organizer/{id}` response. Unlike `PublicCampaign`,
 * the organizer-scoped shape omits `organizationName` (it's on the parent
 * profile), `phonePublic` and `doctor`, and carries the raw `status` +
 * `createdAt`. `species` is an object of slot counts, like the other endpoints.
 */
export interface OrganizerCampaign {
  submissionId: string
  status: string              // e.g. "approved" (lowercase from this endpoint)
  county: string              // 2-letter code, e.g. "SV"
  locality: string
  address: string
  dateStart: string
  dateEnd: string | null
  timeStart: string
  timeEnd: string
  createdAt: string
  species: Partial<Record<'dog' | 'cat', number>>
}

/** Wire shape of `GET /organizer/{id}` — an organization plus all its campaigns. */
export interface OrganizerProfile {
  organizationName: string
  campaigns: OrganizerCampaign[]
}

export interface LocalityWaitingStats {
  county: string
  locality: string
  registeredInLocality: number
  registeredInCounty: number
}

/** Reactive form state — maps to CampaignSubmission on submit. */
export interface CampaignFormState {
  organizationName: string
  contactEmail: string
  contactPhone: string
  samePublicPhone: boolean
  phonePublic: string
  county: string
  locality: string
  address: string
  dateStart: string
  isMultiDay: boolean
  dateEnd: string
  timeStart: string
  timeEnd: string
  hasDogs: boolean
  hasCats: boolean
  slotsDogs?: number
  slotsCats?: number
  doctor: string
  gdprConsent: boolean
}

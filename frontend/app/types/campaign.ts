/**
 * Wire shape returned by `GET /campaigns` and `GET /campaigns/{id}`.
 * `species` is an **object of slot counts** (not an array) — normalize to
 * `Campaign` via the mapper in `useCampaigns` before passing to the UI.
 */
export interface PublicCampaign {
  submissionId: string
  organizationName: string
  phonePublic: string
  county: string        // 2-letter code, e.g. "SV"
  countyName: string    // backend resolves this
  locality: string
  address: string
  dateStart: string
  dateEnd: string | null
  timeStart: string
  timeEnd: string
  doctor: string | null
  /** Slot counts per species. May be partial if only one species is offered. */
  species: Partial<Record<Species, number>>
}

export interface Campaign {
  id: string
  organizationName: string
  county: string
  /** Resolved county display name — provided by the backend via `PublicCampaign.countyName`. */
  countyName?: string
  locality: string
  address: string
  dateStart: string
  dateEnd?: string
  timeStart: string
  timeEnd: string
  species: Species[]
  slotsDogs?: number | string
  slotsCats?: number | string
  doctor?: string
  phonePublic: string
  status: CampaignStatus
  isSoldOut?: boolean
  createdAt: string
}

export type Species = 'dog' | 'cat'

// Backend returns uppercase. Keep uppercase here to match the wire format.
export type CampaignStatus = 'PENDING' | 'APPROVED' | 'SOLDOUT' | 'COMPLETED'

/**
 * Shape consumed by `<CampaignCard>` — the card is reused on /campanii (where
 * data comes from the API) and in the organizer preview step (where data
 * comes from the form). Callers resolve the county code → display name.
 */
export interface CampaignCardData {
  organizationName: string
  countyName: string
  locality: string
  address: string
  dateStart: string
  dateEnd?: string
  timeStart: string
  timeEnd: string
  species: Species[]
  slotsDogs?: number
  slotsCats?: number
  doctor?: string
  phonePublic: string
  status?: CampaignStatus
  isSoldOut?: boolean
}

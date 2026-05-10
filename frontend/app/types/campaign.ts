export interface Campaign {
  id: string
  organizationName: string
  county: string
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

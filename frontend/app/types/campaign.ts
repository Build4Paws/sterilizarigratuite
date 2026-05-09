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
  slotsDogs?: number
  slotsCats?: number
  doctor?: string
  phonePublic: string
  status: CampaignStatus
  createdAt: string
}

export type Species = 'dog' | 'cat'

export type CampaignStatus = 'pending' | 'approved' | 'soldout' | 'completed'

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
}

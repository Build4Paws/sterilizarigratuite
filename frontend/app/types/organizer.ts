export interface CampaignSubmission {
  organizationName: string
  county: string
  locality: string
  address: string
  dateStart: string
  dateEnd?: string
  timeStart: string
  timeEnd: string
  species: ('dog' | 'cat')[]
  slotsDogs?: number
  slotsCats?: number
  doctor?: string
  phonePublic: string
  emailContact: string
}

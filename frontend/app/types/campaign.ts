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
  status: 'pending' | 'approved' | 'soldout' | 'completed'
  createdAt: string
}

export type Species = 'dog' | 'cat'

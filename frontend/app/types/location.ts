export interface County {
  code: string
  name: string
}

export interface Locality {
  id: string
  name: string
  countyCode: string
}

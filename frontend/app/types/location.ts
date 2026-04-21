export interface County {
  auto: string
  nume: string
}

export interface Locality {
  nume: string
  simplu?: string
}

export interface JudeteData {
  judete: (County & { localitati: Locality[] })[]
}

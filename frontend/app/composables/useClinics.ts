export interface Clinic {
  name: string
  locality: string
  county: string
  phone?: string
}

/**
 * Lookup permanent (free) sterilization clinics for a given location.
 * Stub — returns empty until a data source is wired up (JSON file or API endpoint).
 * The confirmation page's clinics section is gated on a non-empty result.
 */
export function useClinics(_countyCode: string, _locality: string) {
  const clinics = ref<Clinic[]>([])
  const loading = ref(false)
  return { clinics, loading }
}

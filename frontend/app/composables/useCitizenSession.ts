import type { RegistrationStats } from '~/types'

export type ContactChannel = 'sms' | 'email' | 'both'

export interface CitizenSession {
  name: string
  channel: ContactChannel
  phone?: string
  email?: string
  countyCode: string
  countyName: string
  locality: string
  species: ('dog' | 'cat')[]
  dogCount?: number
  catCount?: number
  submittedAt: string
  stats?: RegistrationStats
  /** Persisted for a future "manage my subscription" link (magic-link UI deferred). */
  citizenId?: string
  manageToken?: string
}

const STORAGE_KEY = 'citizen-session'
const session = ref<CitizenSession | null>(null)
let hydrated = false

function hydrate() {
  if (hydrated || !import.meta.client) return
  hydrated = true
  const raw = sessionStorage.getItem(STORAGE_KEY)
  if (!raw) return
  try {
    session.value = JSON.parse(raw) as CitizenSession
  } catch {
    sessionStorage.removeItem(STORAGE_KEY)
  }
}

export function useCitizenSession() {
  hydrate()

  function setSession(data: CitizenSession) {
    session.value = data
    if (import.meta.client) {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(data))
    }
  }

  function clearSession() {
    session.value = null
    if (import.meta.client) {
      sessionStorage.removeItem(STORAGE_KEY)
    }
  }

  return { session, setSession, clearSession }
}

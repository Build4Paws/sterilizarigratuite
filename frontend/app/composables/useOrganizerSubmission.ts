import type { CampaignSubmission, CampaignSubmissionResponse } from '~/types'

export interface OrganizerSubmissionSession {
  campaign: CampaignSubmission
  countyName: string
  submissionId: string
  status: 'pending'
  stats?: CampaignSubmissionResponse['stats']
  submittedAt: string
}

const STORAGE_KEY = 'organizer-submission'
const session = ref<OrganizerSubmissionSession | null>(null)
let hydrated = false

function hydrate() {
  if (hydrated || !import.meta.client) return
  hydrated = true
  const raw = sessionStorage.getItem(STORAGE_KEY)
  if (!raw) return
  try {
    session.value = JSON.parse(raw) as OrganizerSubmissionSession
  } catch {
    sessionStorage.removeItem(STORAGE_KEY)
  }
}

export function useOrganizerSubmission() {
  hydrate()

  function setSession(data: OrganizerSubmissionSession) {
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

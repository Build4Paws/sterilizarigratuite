import type { PublicCampaign } from '~/types'
import { useIntervalFn, useDocumentVisibility } from '@vueuse/core'

// We need to know when an admin approves a campaign so the confirmation page can
// flip its status live. The single `GET /campaigns/{id}` is NOT usable for this:
// it returns 200 for ANY status (pending included) and carries no `status` field,
// so a 200 there does not mean "approved". The LIST endpoint
// `GET /campaigns?county=` is what the backend filters to "approved + upcoming",
// so a campaign appears in it ONLY once approved. We poll that and look for our
// own submissionId — its presence is the authoritative "now public" signal.

const POLL_INTERVAL_MS = 5_000
// Stop auto-polling after this long so a tab left open for hours doesn't keep
// hitting the backend forever. The user can still re-check manually.
const MAX_POLL_MS = 15 * 60 * 1_000

export function useCampaignApproval(
  getId: () => string | undefined,
  getCounty: () => string | undefined,
) {
  const approved = ref(false)
  const campaign = ref<PublicCampaign | null>(null)
  const checking = ref(false) // a request is currently in flight (for subtle UI)
  const stopped = ref(false) // gave up after MAX_POLL_MS, still pending

  let startedAt = 0
  let inFlight = false

  async function checkOnce() {
    const id = getId()
    if (!id || approved.value || inFlight) return
    inFlight = true
    checking.value = true
    try {
      const county = getCounty()
      const url = county
        ? `/api/campaigns?county=${encodeURIComponent(county)}`
        : '/api/campaigns'
      const { campaigns } = await $fetch<{ campaigns: PublicCampaign[] }>(url)
      const match = campaigns?.find(c => c.submissionId === id)
      if (match) {
        // In the approved + upcoming list ⟺ approved and public.
        campaign.value = match
        approved.value = true
        pause()
        return
      }
      // 200 but not in the list yet → still pending. Fall through to the cap check.
    }
    catch {
      // Transient error — keep trying until the cap.
    }
    finally {
      inFlight = false
      checking.value = false
    }

    if (startedAt && Date.now() - startedAt > MAX_POLL_MS) {
      stopped.value = true
      pause()
    }
  }

  const { pause, resume, isActive } = useIntervalFn(checkOnce, POLL_INTERVAL_MS, {
    immediate: false,
  })

  // Don't hammer the backend from a hidden tab; re-check instantly on return so
  // an organizer who tabbed away sees the result the moment they come back.
  const visibility = useDocumentVisibility()
  watch(visibility, (v) => {
    if (approved.value || stopped.value) return
    if (v === 'visible') {
      checkOnce()
      if (!isActive.value) resume()
    }
    else {
      pause()
    }
  })

  function start() {
    if (approved.value || isActive.value) return
    startedAt = Date.now()
    stopped.value = false
    checkOnce() // immediate first check, then every POLL_INTERVAL_MS
    resume()
  }

  function checkNow() {
    if (approved.value) return
    // Manual retry also reopens the polling window if it had given up.
    if (stopped.value) {
      stopped.value = false
      startedAt = Date.now()
      resume()
    }
    checkOnce()
  }

  onBeforeUnmount(pause)

  return { approved, campaign, checking, stopped, isPolling: isActive, start, checkNow }
}

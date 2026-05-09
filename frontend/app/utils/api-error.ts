/**
 * Maps backend error codes (returned in `error.data.error`) to user-facing
 * Romanian copy. Keys must stay in sync with the codes documented in
 * docs/CAMPAIGNS-FLOW-PLAN.md §5 and the citizen registration contract.
 */
const ERROR_MESSAGES: Record<string, string> = {
  duplicate_submission:
    'O campanie identică există deja pentru această locație și dată. Verifică pagina de campanii sau contactează-ne.',
  duplicate_registration:
    'Această adresă de email sau număr de telefon este deja înregistrată în zona ta.',
  validation_failed:
    'Datele trimise nu sunt valide. Te rugăm să verifici câmpurile și să încerci din nou.',
  captcha_failed:
    'Verificarea anti-spam a eșuat. Te rugăm să reîncarci pagina și să încerci din nou.',
  rate_limited:
    'Ai trimis prea multe cereri într-un timp scurt. Te rugăm să aștepți câteva minute.',
  server_error:
    'A apărut o problemă pe server. Te rugăm să încerci din nou peste câteva minute.',
}

const FALLBACK = 'A apărut o eroare. Te rugăm să încerci din nou.'

interface ApiErrorShape {
  data?: unknown
  statusMessage?: string
  message?: string
  statusCode?: number
}

/**
 * Extracts a user-facing message from an error thrown by `$fetch`/`createError`.
 *
 * Priority:
 *   1. Mapped Romanian copy for a known `data.error` code
 *   2. Backend-provided `data.errors[]` list (joined) or `data.message`
 *   3. The handler's `statusMessage` (already in Romanian for our routes)
 *   4. Generic fallback
 */
export function extractApiError(err: unknown): string {
  if (!err || typeof err !== 'object') return FALLBACK

  const e = err as ApiErrorShape

  let data: unknown = e.data
  if (typeof data === 'string') {
    const raw = data
    try { data = JSON.parse(raw) }
    catch { return raw || e.statusMessage || FALLBACK }
  }

  if (data && typeof data === 'object') {
    const d = data as { errors?: string[]; message?: string; error?: string }

    if (d.error) {
      const mapped = ERROR_MESSAGES[d.error]
      if (mapped) return mapped
    }

    if (Array.isArray(d.errors) && d.errors.length) return d.errors.join('. ')
    if (d.message) return d.message
    if (d.error) return d.error
  }

  return e.statusMessage || e.message || FALLBACK
}

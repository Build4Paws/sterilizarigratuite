/**
 * Maps backend error codes to user-facing Romanian copy. Keys must stay in sync
 * with the codes documented in docs/CAMPAIGNS-FLOW-PLAN.md §5 and the citizen
 * registration contract.
 *
 * NOTE on shape: when a Nitro server route throws `createError({ data })`, the
 * error response body is the *envelope*
 *   { error: true, statusCode, statusMessage, message, data: <payload> }
 * so the backend code lives at `error.data.data`, not `error.data`. `<payload>`
 * is whatever we passed as `data` — an object (`{ error, errors? }`) or a raw
 * JSON string (the public proxies forward the upstream body verbatim).
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
  // v1.1.1 additions
  invalid_json:
    'Cererea trimisă nu este validă. Te rugăm să reîncarci pagina și să încerci din nou.',
  invalid_id:
    'Identificatorul furnizat nu este valid.',
  not_found:
    'Resursa solicitată nu a fost găsită.',
  token_invalid:
    'Link-ul a expirat sau a fost deja folosit. Te rugăm să soliciți un link nou.',
  internal_error:
    'A apărut o problemă pe server. Te rugăm să încerci din nou peste câteva minute.',
  // Admin
  unauthorized: 'Sesiune expirată. Te rugăm să te autentifici din nou.',
  forbidden: 'Nu ai permisiunea necesară pentru această acțiune.',
  invalid_state: 'Acțiunea nu este permisă pentru starea curentă.',
  unknown_host: 'Configurare invalidă a serverului. Contactează un administrator.',
  route_not_found: 'Resursa solicitată nu a fost găsită.',
}

const FALLBACK = 'A apărut o eroare. Te rugăm să încerci din nou.'

interface ApiErrorShape {
  data?: unknown
  statusMessage?: string
  message?: string
  statusCode?: number
}

/**
 * Pulls a usable message out of one candidate payload (an object, a JSON string,
 * or anything else). Returns the mapped/derived message, or `null` if this
 * candidate carries nothing usable.
 *
 * Priority within a candidate:
 *   1. Mapped Romanian copy for a known `error` code
 *   2. Backend-provided `errors[]` list (joined) or `message`
 *   3. The raw `error` code as a last resort
 */
function messageFromPayload(raw: unknown): string | null {
  let data = raw
  if (typeof data === 'string') {
    const str = data
    try { data = JSON.parse(str) } catch { return str || null }
  }
  if (!data || typeof data !== 'object') return null

  const d = data as { errors?: string[]; message?: string; error?: string }
  if (d.error) {
    const mapped = ERROR_MESSAGES[d.error]
    if (mapped) return mapped
  }
  if (Array.isArray(d.errors) && d.errors.length) return d.errors.join('. ')
  if (d.message) return d.message
  if (typeof d.error === 'string') return d.error
  return null
}

/**
 * Extracts a user-facing message from an error thrown by `$fetch`/`createError`.
 *
 * `err.data` is the response body, which for our routes is the Nitro error
 * envelope (see the note above). We therefore look at the nested payload
 * (`err.data.data`) first, then fall back to the envelope itself (covers
 * non-wrapped shapes), then the handler's `statusMessage`, then a generic copy.
 */
export function extractApiError(err: unknown): string {
  if (!err || typeof err !== 'object') return FALLBACK

  const e = err as ApiErrorShape
  const envelope = e.data
  const inner = envelope && typeof envelope === 'object'
    ? (envelope as { data?: unknown }).data
    : undefined

  return (
    messageFromPayload(inner)
    || messageFromPayload(envelope)
    || e.statusMessage
    || e.message
    || FALLBACK
  )
}

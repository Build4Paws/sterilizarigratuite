const RO_MONTHS = [
  'ianuarie', 'februarie', 'martie', 'aprilie', 'mai', 'iunie',
  'iulie', 'august', 'septembrie', 'octombrie', 'noiembrie', 'decembrie',
] as const

/**
 * Format an ISO `YYYY-MM-DD` date as Romanian `dd <lună> yyyy` (e.g. `03 iunie 2026`).
 * Parsed component-wise (not via `new Date`) so the displayed day never shifts
 * by timezone. Returns '' for empty input and echoes back anything unparseable.
 */
export function formatDate(iso: string | null | undefined): string {
  if (!iso) return ''
  const parts = iso.split('-').map(Number)
  if (parts.length !== 3 || parts.some(Number.isNaN)) return iso
  const [y, m, d] = parts as [number, number, number]
  const month = RO_MONTHS[m - 1]
  if (!month) return iso
  return `${String(d).padStart(2, '0')} ${month} ${y}`
}

export function formatDateRange(start: string, end?: string): string {
  if (!end || start === end) return formatDate(start)
  return `${formatDate(start)} — ${formatDate(end)}`
}

/**
 * Format a full ISO timestamp as Romanian `dd <lună> yyyy, HH:MM` (local time).
 */
export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return ''
  const dt = new Date(iso)
  if (Number.isNaN(dt.getTime())) return iso
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(dt.getDate())} ${RO_MONTHS[dt.getMonth()]} ${dt.getFullYear()}, ${pad(dt.getHours())}:${pad(dt.getMinutes())}`
}

export function formatPhone(phone: string): string {
  const cleaned = phone.replace(/\s/g, '')
  if (cleaned.startsWith('+40')) {
    return cleaned.replace(/(\+40)(\d{3})(\d{3})(\d{3})/, '$1 $2 $3 $4')
  }
  if (cleaned.startsWith('0')) {
    return cleaned.replace(/^(0\d{3})(\d{3})(\d{3})$/, '$1 $2 $3')
  }
  return phone
}

export function speciesLabel(species: ('dog' | 'cat')[]): string {
  if (species.includes('dog') && species.includes('cat')) return 'Câini și pisici'
  if (species.includes('dog')) return 'Câini'
  return 'Pisici'
}

// Escapes `<` so a `</script>` in the data cannot break out of the surrounding <script> element.
export function safeJsonLd(value: unknown): string {
  return JSON.stringify(value).replace(/</g, '\\u003c')
}

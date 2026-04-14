export function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('ro-RO', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

export function formatDateRange(start: string, end?: string): string {
  if (!end || start === end) return formatDate(start)
  return `${formatDate(start)} — ${formatDate(end)}`
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

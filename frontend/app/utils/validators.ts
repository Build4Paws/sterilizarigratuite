/**
 * Shared validation primitives for forms across the app.
 *
 * Phone format follows the Romanian mobile convention `+40` + 9 digits.
 * Whitespace is allowed in user input (the UiPhoneInput formats with spaces);
 * `stripPhone` normalizes before validation or submission.
 */
export const PHONE_RE = /^\+40[0-9]{9}$/
export const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function stripPhone(phone: string | undefined | null): string {
  return (phone ?? '').replace(/\s/g, '')
}

export function isValidPhone(phone: string | undefined | null): boolean {
  return PHONE_RE.test(stripPhone(phone))
}

export function isValidEmail(email: string | undefined | null): boolean {
  return EMAIL_RE.test((email ?? '').trim())
}

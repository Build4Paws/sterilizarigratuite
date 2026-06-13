/**
 * Cloudflare Turnstile server-side verification, run in the Nuxt proxy (on EC2,
 * which has internet egress) instead of in the API Lambda (which sits in a VPC
 * with no NAT and can't reach challenges.cloudflare.com).
 *
 * SECURITY: the secret is read from a SERVER-ONLY runtime config
 * (`turnstileSecretKey` ← `NUXT_TURNSTILE_SECRET_KEY`) — never `public.*`, never
 * sent to the browser. This is only a valid security boundary because the
 * Lambda is reachable solely via this SigV4-signed proxy (API Gateway AWS_IAM
 * auth); the Lambda itself must run with TURNSTILE_ENABLED=false so it doesn't
 * re-verify the single-use token.
 *
 * Empty secret = dev mode → verification skipped (mirrors the previous backend
 * contract). The call is time-boxed so a Cloudflare hiccup can't stall a submit.
 */
const SITEVERIFY_URL = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'

export async function verifyTurnstile(
  token: string | undefined,
  remoteIp: string | undefined,
): Promise<boolean> {
  const secret = useRuntimeConfig().turnstileSecretKey as string
  if (!secret) return true // dev mode: no secret configured → skip
  if (!token) return false

  const form = new URLSearchParams({ secret, response: token })
  if (remoteIp) form.set('remoteip', remoteIp)

  try {
    const res = await $fetch<{ success?: boolean }>(SITEVERIFY_URL, {
      method: 'POST',
      body: form, // ofetch sends URLSearchParams as application/x-www-form-urlencoded
      timeout: 6000,
    })
    return res?.success === true
  } catch {
    // Network/parse failure → fail closed.
    return false
  }
}

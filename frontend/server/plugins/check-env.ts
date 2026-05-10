export default defineNitroPlugin(() => {
  if (import.meta.dev) return

  const config = useRuntimeConfig()
  const required = ['hcaptchaSecretKey', 'awsAccessKeyId', 'awsSecretAccessKey', 'awsApiBase'] as const
  const missing = required.filter(k => !config[k])

  if (missing.length) {
    throw new Error(`[startup] Missing required env vars: ${missing.join(', ')}`)
  }
})

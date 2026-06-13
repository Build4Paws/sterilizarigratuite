<template>
  <div ref="el" class="turnstile" />
</template>

<script setup lang="ts">
/**
 * Cloudflare Turnstile widget. Dependency-free: loads the official script once
 * and renders explicitly, exposing the same surface the form already expected
 * from the old hCaptcha component — `@verify` / `@expired` / `@error` events and
 * a `reset()` method via template ref.
 *
 * The token is verified server-side by the API Lambda (verify_turnstile); this
 * component only collects it. Wrap usage in <ClientOnly> — it renders on the
 * client only.
 */
const props = defineProps<{ siteKey: string }>()
const emit = defineEmits<{ verify: [token: string]; expired: []; error: [] }>()

const SCRIPT_SRC = 'https://challenges.cloudflare.com/turnstile/v0/api.js'

interface TurnstileApi {
  render: (el: HTMLElement, opts: Record<string, unknown>) => string
  reset: (id?: string) => void
  remove: (id?: string) => void
}
type TurnstileWindow = Window & { turnstile?: TurnstileApi; __turnstileLoading?: Promise<void> }

const el = ref<HTMLElement | null>(null)
let widgetId: string | undefined

function loadScript(): Promise<void> {
  if (typeof window === 'undefined') return Promise.resolve()
  const w = window as TurnstileWindow
  if (w.turnstile) return Promise.resolve()
  if (w.__turnstileLoading) return w.__turnstileLoading
  w.__turnstileLoading = new Promise<void>((resolve, reject) => {
    const existing = document.querySelector(`script[src^="${SCRIPT_SRC}"]`)
    if (existing) {
      existing.addEventListener('load', () => resolve())
      existing.addEventListener('error', () => reject(new Error('turnstile script error')))
      return
    }
    const s = document.createElement('script')
    s.src = SCRIPT_SRC
    s.async = true
    s.defer = true
    s.onload = () => resolve()
    s.onerror = () => reject(new Error('turnstile script error'))
    document.head.appendChild(s)
  })
  return w.__turnstileLoading
}

async function renderWidget() {
  await loadScript()
  const w = window as TurnstileWindow
  if (!w.turnstile || !el.value) return
  widgetId = w.turnstile.render(el.value, {
    sitekey: props.siteKey,
    callback: (token: string) => emit('verify', token),
    'expired-callback': () => emit('expired'),
    'error-callback': () => { emit('error') },
  })
}

function reset() {
  const w = window as TurnstileWindow
  if (w.turnstile && widgetId !== undefined) w.turnstile.reset(widgetId)
}

onMounted(() => { renderWidget().catch(() => emit('error')) })
onBeforeUnmount(() => {
  const w = window as TurnstileWindow
  if (w.turnstile && widgetId !== undefined) {
    try { w.turnstile.remove(widgetId) } catch { /* widget already gone */ }
  }
})

defineExpose({ reset })
</script>

<style scoped>
.turnstile { min-height: 65px; }
</style>

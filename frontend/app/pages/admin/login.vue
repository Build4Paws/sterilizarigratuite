<template>
  <div class="login">
    <div class="login__card">
      <div class="login__brand">
        <img src="/favicon.svg" alt="" class="login__logo" width="30" height="30" />
        <span>Build4Paws <strong>Admin</strong></span>
      </div>

      <h1 class="login__title">{{ title }}</h1>
      <p class="login__subtitle">{{ subtitle }}</p>

      <UiAlert v-if="error" variant="error">{{ error }}</UiAlert>

      <form class="login__form" @submit.prevent="submit">
        <!-- Step 1: credentials -->
        <template v-if="step === 'password'">
          <UiInput
            id="admin-email"
            v-model="email"
            label="Email"
            type="email"
            placeholder="nume@build4paws.ro"
            required
          />
          <UiInput
            id="admin-password"
            v-model="password"
            label="Parolă"
            type="password"
            required
          />
        </template>

        <!-- Step 1b: replace temporary password -->
        <template v-else-if="step === 'newPassword'">
          <UiInput
            id="admin-new-password"
            v-model="newPassword"
            label="Parolă nouă"
            type="password"
            required
          />
          <UiInput
            id="admin-new-password-2"
            v-model="newPassword2"
            label="Confirmă parola"
            type="password"
            required
          />
        </template>

        <!-- Step 2a: first-time TOTP enrollment -->
        <template v-else-if="step === 'setup'">
          <div class="login__setup">
            <p class="login__hint">
              Adaugă acest cont în aplicația ta de autentificare (Google
              Authenticator, 1Password, Authy etc.), apoi introdu codul generat.
            </p>
            <a v-if="otpauthUri" :href="otpauthUri" class="login__otpauth">
              Deschide în aplicația de autentificare
            </a>
            <div class="login__secret">
              <span class="login__secret-label">Sau introdu cheia manual:</span>
              <code class="login__secret-code">{{ secretCode }}</code>
              <button type="button" class="login__copy" @click="copySecret">
                {{ copied ? 'Copiat ✓' : 'Copiază' }}
              </button>
            </div>
          </div>
          <UiInput
            id="admin-setup-code"
            v-model="code"
            label="Cod de verificare (6 cifre)"
            type="text"
            placeholder="123456"
            required
          />
        </template>

        <!-- Step 2b: steady-state TOTP -->
        <template v-else>
          <UiInput
            id="admin-mfa"
            v-model="code"
            label="Cod (6 cifre)"
            type="text"
            placeholder="123456"
            required
          />
        </template>

        <UiButton type="submit" variant="primary" block :loading="loading">
          {{ submitLabel }}
        </UiButton>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
// Standalone screen — no admin chrome, no public nav.
definePageMeta({ layout: false })
useSeoMeta({ title: 'Admin · Autentificare', robots: 'noindex, nofollow' })

const route = useRoute()

type Step = 'password' | 'newPassword' | 'setup' | 'mfa'
const step = ref<Step>('password')

const email = ref('')
const password = ref('')
const newPassword = ref('')
const newPassword2 = ref('')
const code = ref('')
const session = ref('')
const secretCode = ref('')
const otpauthUri = ref('')
const copied = ref(false)
const loading = ref(false)
const error = ref('')

const title = computed(() => {
  if (step.value === 'newPassword') return 'Setează o parolă nouă'
  if (step.value === 'setup') return 'Configurează autentificarea în doi pași'
  if (step.value === 'mfa') return 'Cod de verificare'
  return 'Autentificare'
})
const subtitle = computed(() => {
  if (step.value === 'newPassword') return 'La prima conectare trebuie să îți alegi o parolă proprie.'
  if (step.value === 'setup') return 'Securizează contul cu o aplicație de autentificare.'
  if (step.value === 'mfa') return 'Introdu codul din aplicația ta de autentificare.'
  return 'Acces rezervat echipei. Conectează-te pentru a continua.'
})
const submitLabel = computed(() => {
  switch (step.value) {
    case 'newPassword': return 'Salvează parola'
    case 'setup': return 'Activează și conectează-te'
    case 'mfa': return 'Verifică'
    default: return 'Conectează-te'
  }
})

const ERRORS: Record<string, string> = {
  invalid_credentials: 'Email sau parolă incorecte.',
  mfa_invalid: 'Cod incorect sau expirat. Încearcă din nou.',
  rate_limited: 'Prea multe încercări. Așteaptă un minut și reîncearcă.',
  account_setup_required: 'Contul necesită configurare. Contactează un administrator.',
  password_reset_required: 'Parola trebuie resetată. Contactează un administrator.',
  validation_failed: 'Completează toate câmpurile.',
  weak_password: 'Parola nu respectă cerințele de securitate (minim 12 caractere, litere mari/mici, cifre).',
  password_mismatch: 'Parolele nu coincid.',
  auth_failed: 'Autentificare eșuată. Încearcă din nou.',
}

function messageFor(err: unknown): string {
  const code = (err as { data?: { data?: { error?: string } } })?.data?.data?.error
  return (code && ERRORS[code]) || 'A apărut o eroare. Încearcă din nou.'
}

async function copySecret() {
  try {
    await navigator.clipboard.writeText(secretCode.value)
    copied.value = true
    setTimeout(() => (copied.value = false), 2000)
  } catch {
    // Clipboard may be blocked — the code is visible for manual entry anyway.
  }
}

interface LoginResponse {
  ok?: boolean
  newPasswordRequired?: boolean
  mfaRequired?: boolean
  mfaSetupRequired?: boolean
  session?: string
  secretCode?: string
  otpauthUri?: string
}

async function submit() {
  error.value = ''
  loading.value = true
  try {
    let body: Record<string, string>
    if (step.value === 'newPassword') {
      if (newPassword.value !== newPassword2.value) {
        error.value = ERRORS.password_mismatch!
        return
      }
      body = { email: email.value, session: session.value, newPassword: newPassword.value }
    } else if (step.value === 'setup') {
      body = { email: email.value, session: session.value, setupCode: code.value }
    } else if (step.value === 'mfa') {
      body = { email: email.value, session: session.value, code: code.value }
    } else {
      body = { email: email.value, password: password.value }
    }

    const res = await $fetch<LoginResponse>('/api/admin/auth/login', { method: 'POST', body })

    if (res.newPasswordRequired && res.session) {
      session.value = res.session
      newPassword.value = ''
      newPassword2.value = ''
      step.value = 'newPassword'
      return
    }
    if (res.mfaSetupRequired && res.session && res.secretCode) {
      session.value = res.session
      secretCode.value = res.secretCode
      otpauthUri.value = res.otpauthUri ?? ''
      code.value = ''
      step.value = 'setup'
      return
    }
    if (res.mfaRequired && res.session) {
      session.value = res.session
      code.value = ''
      step.value = 'mfa'
      return
    }

    const next = typeof route.query.next === 'string' ? route.query.next : '/admin'
    // Full reload so SSR pages pick up the fresh session cookie.
    await navigateTo(next.startsWith('/admin') ? next : '/admin', { external: true })
  } catch (err) {
    error.value = messageFor(err)
    if (step.value !== 'password') code.value = ''
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-lg);
  background: var(--color-primary);
}

.login__card {
  width: 100%;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  padding: var(--space-xl) var(--space-lg);
  background: var(--color-input-bg, #fff);
  border-radius: var(--radius-lg, 1rem);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.25);
}

.login__brand {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  color: var(--color-primary);
  font-size: var(--font-size-lg);
}
.login__brand strong { font-weight: 800; }
.login__logo { width: 30px; height: 30px; }

.login__title {
  font-family: var(--font-heading, var(--font-body));
  font-size: var(--font-size-xl);
  color: var(--color-text);
  margin: 0;
}

.login__subtitle {
  font-size: var(--font-size-sm);
  color: var(--color-slate-500, #64748b);
  margin: 0;
}

.login__form {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  margin-top: var(--space-xs);
}

.login__setup {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}
.login__hint { font-size: var(--font-size-sm); color: var(--color-text); margin: 0; }

.login__otpauth {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-accent);
  text-decoration: none;
}
.login__otpauth:hover { text-decoration: underline; }

.login__secret {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm);
  background: var(--color-slate-50);
  border-radius: var(--radius-md);
}
.login__secret-label { font-size: var(--font-size-sm); color: var(--color-slate-500, #64748b); width: 100%; }
.login__secret-code {
  font-family: monospace;
  font-size: var(--font-size-base);
  letter-spacing: 0.08em;
  word-break: break-all;
  color: var(--color-text);
}
.login__copy {
  margin-left: auto;
  border: 1px solid var(--color-border);
  background: var(--color-input-bg, #fff);
  border-radius: var(--radius-md);
  padding: 0.25rem 0.625rem;
  font-size: var(--font-size-sm);
  cursor: pointer;
  color: var(--color-primary);
}
</style>

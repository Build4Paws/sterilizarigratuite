<template>
  <form class="citizen-form" novalidate @submit.prevent="handleSubmit">
    <!-- Să facem cunoștință -->
    <div class="form-section">
      <div class="form-section__header">
        <h3 class="form-section__title">Salut! Cum te numești?</h3>
      </div>
      <UiFormRow>
        <UiFormItem>
          <UiInput
            id="citizen-name"
            v-model="form.name"
            label="Nume complet"
            placeholder="ex: Maria Popescu"
            :required="true"
            :error="submitted ? errors.name : undefined"
          />
        </UiFormItem>
      </UiFormRow>
    </div>

    <!-- Cum te contactăm? -->
    <div class="form-section">
      <div class="form-section__header">
        <h3 class="form-section__title">Cum preferi să te contactăm?</h3>
        <p class="form-section__hint">Lasă-ne un număr de telefon sau o adresă de email, sau ambele</p>
      </div>
      <UiFormRow align="end" :nowrap="!isMobile">
        <UiFormItem basis="140px">
          <UiInput
            id="citizen-email"
            v-model="form.email"
            label="Email"
            type="email"
            placeholder="adresa@email.com"
            :error="submitted ? errors.email : undefined"
          />
        </UiFormItem>
        <UiFormDivider>sau</UiFormDivider>
        <UiFormItem basis="140px">
          <UiPhoneInput
            id="citizen-phone"
            v-model="form.phone"
            label="Telefon"
            :error="submitted ? errors.phone : undefined"
          />
        </UiFormItem>
      </UiFormRow>
    </div>

    <!-- Unde locuiești? -->
    <div class="form-section">
      <div class="form-section__header">
        <h3 class="form-section__title">Unde locuiești?</h3>
        <p class="form-section__hint">Te anunțăm doar când apare o campanie în localitatea ta</p>
      </div>
      <UiFormRow>
        <UiFormItem basis="200px">
          <UiCombobox
            id="citizen-county"
            v-model="form.county"
            label="Județ"
            placeholder="Caută județul"
            :options="counties"
            :required="true"
            :error="submitted ? errors.county : undefined"
            @update:model-value="onCountyChange"
          />
        </UiFormItem>
        <UiFormItem basis="200px">
          <UiCombobox
            id="citizen-locality"
            v-model="form.locality"
            label="Localitate"
            placeholder="Caută localitatea"
            :options="localities"
            :required="true"
            :disabled="!form.county"
            :error="submitted ? errors.locality : undefined"
          />
        </UiFormItem>
      </UiFormRow>
    </div>

    <!-- Ce dorești să sterilizezi?? -->
    <fieldset class="form-section form-section--fieldset">
      <div class="form-section__header">
        <legend class="form-section__title">Ce dorești să sterilizezi?</legend>
        <p class="form-section__hint">Bifează ce prieteni blănoși ai acasă.</p>
      </div>
      <UiFormRow>
        <UiFormItem :grow="false" basis="auto">
          <UiCheckbox id="citizen-dogs" v-model="form.hasDogs">
            Câini
          </UiCheckbox>
        </UiFormItem>
        <UiFormItem :grow="false" basis="auto">
          <UiCheckbox id="citizen-cats" v-model="form.hasCats">
            Pisici
          </UiCheckbox>
        </UiFormItem>
      </UiFormRow>
      <p v-if="submitted && errors.species" class="citizen-form__error" role="alert">
        {{ errors.species }}
      </p>

      <UiFormRow v-if="form.hasDogs || form.hasCats">
        <UiFormItem v-if="form.hasDogs" basis="120px" :grow="false">
          <UiSelect
            id="citizen-dog-count"
            v-model="dogCountStr"
            label="Câți câini?"
            :options="countOptions"
          />
        </UiFormItem>
        <UiFormItem v-if="form.hasCats" basis="120px" :grow="false">
          <UiSelect
            id="citizen-cat-count"
            v-model="catCountStr"
            label="Câte pisici?"
            :options="countOptions"
          />
        </UiFormItem>
      </UiFormRow>
    </fieldset>

    <!-- GDPR + Submit -->
    <div class="form-section form-section--footer">
      <UiFormRow>
        <UiFormItem>
          <UiCheckbox
            id="citizen-gdpr"
            v-model="form.gdprConsent"
            :required="true"
            :error="submitted ? errors.gdprConsent : undefined"
          >
            Sunt de acord cu
            <NuxtLink to="/confidentialitate" target="_blank">politica de confidențialitate</NuxtLink>
            și prelucrarea datelor personale.
          </UiCheckbox>
        </UiFormItem>
      </UiFormRow>

      <UiFormRow v-if="hcaptchaSiteKey">
        <UiFormItem>
          <ClientOnly>
            <VueHcaptcha
              ref="hcaptchaRef"
              :sitekey="hcaptchaSiteKey"
              @verify="onCaptchaVerify"
              @expired="onCaptchaExpired"
              @error="onCaptchaError"
            />
          </ClientOnly>
          <p v-if="submitted && captchaError" class="citizen-form__error" role="alert">
            {{ captchaError }}
          </p>
        </UiFormItem>
      </UiFormRow>

      <UiFormRow>
        <UiFormItem basis="100%">
          <UiButton type="submit" variant="primary" :block="true" :loading="submitting" :disabled="submitting">
            Înscrie-mă
          </UiButton>
        </UiFormItem>
      </UiFormRow>
    </div>
  </form>
</template>

<script setup lang="ts">
import VueHcaptcha from '@hcaptcha/vue3-hcaptcha'
import type { CitizenFormState, CitizenRegistration, CitizenRegistrationResponse } from '~/types'
import type { ContactChannel } from '~/composables/useCitizenSession'

const router = useRouter()
const runtimeConfig = useRuntimeConfig()
const hcaptchaSiteKey = runtimeConfig.public.hcaptchaSiteKey as string
const { counties, localities, setCounty, init: initLocations } = useLocationData()
const citizenSession = useCitizenSession()

const hcaptchaRef = ref<InstanceType<typeof VueHcaptcha> | null>(null)
const hcaptchaToken = ref('')
const captchaError = ref('')

function onCaptchaVerify(token: string) {
  hcaptchaToken.value = token
  captchaError.value = ''
}
function onCaptchaExpired() {
  hcaptchaToken.value = ''
}
function onCaptchaError() {
  hcaptchaToken.value = ''
  captchaError.value = 'Captcha a eșuat. Te rugăm să încerci din nou.'
}
function resetCaptcha() {
  hcaptchaToken.value = ''
  const instance = hcaptchaRef.value as { reset?: () => void } | null
  instance?.reset?.()
}

const isMobile = ref(false)

onMounted(() => {
  initLocations()
  const mq = window.matchMedia('(max-width: 640px)')
  isMobile.value = mq.matches
  mq.addEventListener('change', (e) => { isMobile.value = e.matches })
})

const form = reactive<CitizenFormState>({
  name: '',
  phone: '',
  email: '',
  county: '',
  locality: '',
  hasDogs: false,
  hasCats: false,
  dogCount: 1,
  catCount: 1,
  gdprConsent: false,
})

const dogCountStr = computed({
  get: () => form.dogCount?.toString() ?? '',
  set: (v: string) => { form.dogCount = v ? Number(v) : undefined },
})

const catCountStr = computed({
  get: () => form.catCount?.toString() ?? '',
  set: (v: string) => { form.catCount = v ? Number(v) : undefined },
})

const submitting = ref(false)
const submitted = ref(false)
const toast = useToast()

const errors = ref<Record<string, string>>({})

const countOptions = Array.from({ length: 5 }, (_, i) => ({
  value: String(i + 1),
  label: String(i + 1),
}))

function validate(): boolean {
  const e: Record<string, string> = {}

  if (!form.name.trim()) e.name = 'Numele este obligatoriu.'
  const phoneDigits = form.phone?.replace(/\D/g, '') ?? ''
  const hasPhone = phoneDigits.length > 0
  const hasEmail = !!form.email?.trim()
  if (!hasPhone && !hasEmail) {
    e.phone = 'Completează telefonul sau emailul.'
    e.email = 'Completează telefonul sau emailul.'
  }
  if (hasPhone && !isValidPhone(form.phone)) {
    e.phone = 'Introdu 9 cifre după +40 (ex: 7XX XXX XXX).'
  }
  if (hasEmail && !isValidEmail(form.email)) {
    e.email = 'Adresă de email invalidă.'
  }
  if (!form.county) e.county = 'Alege județul.'
  if (!form.locality) e.locality = 'Alege localitatea.'
  if (!form.hasDogs && !form.hasCats) e.species = 'Alege cel puțin o specie.'
  if (!form.gdprConsent) e.gdprConsent = 'Trebuie să accepți politica de confidențialitate.'

  errors.value = e
  return Object.keys(e).length === 0
}

// Re-validate reactively after first submit so errors clear as user fixes fields
watch(() => ({ ...form }), () => {
  if (submitted.value) validate()
}, { deep: true })

function onCountyChange(code: string) {
  form.locality = ''
  setCounty(code)
}

async function handleSubmit() {
  submitted.value = true

  if (!validate()) return

  if (hcaptchaSiteKey && !hcaptchaToken.value) {
    captchaError.value = 'Te rugăm să confirmi că nu ești robot.'
    return
  }

  submitting.value = true

  try {
    const phoneClean = stripPhone(form.phone) || undefined
    const payload: CitizenRegistration = {
      name: form.name.trim(),
      phone: phoneClean,
      email: form.email?.trim() || undefined,
      county: form.county,
      locality: form.locality,
      species: [
        ...(form.hasDogs ? ['dog' as const] : []),
        ...(form.hasCats ? ['cat' as const] : []),
      ],
      dogCount: form.hasDogs ? (form.dogCount ?? 1) : undefined,
      catCount: form.hasCats ? (form.catCount ?? 1) : undefined,
      gdprConsent: form.gdprConsent,
    }

    const response = await $fetch<CitizenRegistrationResponse>('/api/register', {
      method: 'POST',
      body: { ...payload, hcaptchaToken: hcaptchaToken.value || undefined },
    })

    const emailClean = form.email?.trim() || undefined
    const channel: ContactChannel = phoneClean && emailClean ? 'both' : phoneClean ? 'sms' : 'email'
    const countyName = counties.value.find(c => c.value === form.county)?.label ?? form.county

    citizenSession.setSession({
      name: form.name.trim(),
      channel,
      phone: phoneClean,
      email: emailClean,
      countyCode: form.county,
      countyName,
      locality: form.locality,
      species: payload.species,
      submittedAt: new Date().toISOString(),
      stats: response?.stats,
    })

    await router.push('/confirmare')
  } catch (err: unknown) {
    toast.error(extractApiError(err))
    resetCaptcha()
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.citizen-form {
  display: flex;
  flex-direction: column;
  gap: 0;
  text-align: left;
}

/* ---- Section blocks ---- */
.form-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  padding: var(--space-lg) 0;
  border-bottom: 1px solid var(--color-border-light);
}

.form-section--fieldset {
  border-left: none;
  border-right: none;
  border-top: none;
}

.form-section--footer {
  border-bottom: none;
  gap: var(--space-md);
}

.form-section:first-child {
  padding-top: 0;
}

.form-section__header {
  margin-bottom: var(--space-xs);
}

.form-section__title {
  font-family: var(--font-heading);
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--color-primary);
  margin: 0;
  padding: 0;
}

.form-section__hint {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  margin-top: 2px;
}

/* ---- Error ---- */
.citizen-form__error {
  font-size: var(--font-size-sm);
  color: var(--color-error);
}
</style>

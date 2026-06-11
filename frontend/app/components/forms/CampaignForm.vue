<template>
  <form class="campaign-form" novalidate @submit.prevent="handleSubmit">
    <!-- ============================================================ -->
    <!-- STEP 1 — Fill                                                  -->
    <!-- ============================================================ -->
    <template v-if="step === 1">
      <!-- Despre organizație -->
      <div class="form-section">
        <div class="form-section__header">
          <h3 class="form-section__title">Detalii organizator</h3>
        </div>
        <UiFormRow>
          <UiFormItem>
            <UiInput
              id="campaign-org"
              v-model="form.organizationName"
              label="Nume organizație"
              placeholder="ex: ONG Patrupede"
              :required="true"
              :error="submitted ? errors.organizationName : undefined"
            />
          </UiFormItem>
        </UiFormRow>
        <UiFormRow :nowrap="!isMobile">
          <UiFormItem basis="180px">
            <UiInput
              id="campaign-contact-email"
              v-model="form.contactEmail"
              label="Email de contact"
              type="email"
              placeholder="contact@organizatie.ro"
              :required="true"
              :error="submitted ? errors.contactEmail : undefined"
            />
          </UiFormItem>
          <UiFormItem basis="180px">
            <UiPhoneInput
              id="campaign-contact-phone"
              v-model="form.contactPhone"
              label="Telefon de contact"
              :error="submitted ? errors.contactPhone : undefined"
            />
          </UiFormItem>
        </UiFormRow>
      </div>

      <!-- Unde -->
      <div class="form-section">
        <div class="form-section__header">
          <h3 class="form-section__title">Unde are loc campania?</h3>
        </div>
        <UiFormRow>
          <UiFormItem basis="200px">
            <UiCombobox
              id="campaign-county"
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
              id="campaign-locality"
              v-model="form.locality"
              label="Localitate"
              placeholder="Caută localitatea"
              :options="localities"
              :required="true"
              :disabled="!form.county"
              :async="true"
              :loading="localityLoading"
              :error="submitted ? errors.locality : undefined"
              @search="searchLocality"
            />
          </UiFormItem>
        </UiFormRow>
        <p v-if="waitingParts.length" class="campaign-form__waiting" role="status">
          <Users :size="16" />
          <span>
            <template v-for="(seg, i) in waitingParts" :key="i">
              <strong v-if="seg.b">{{ seg.t }}</strong><template v-else>{{ seg.t }}</template>
            </template>
          </span>
        </p>
        <UiFormRow>
          <UiFormItem>
            <UiTextarea
              id="campaign-address"
              v-model="form.address"
              label="Adresa exactă (stradă, număr, reper)"
              placeholder="ex: Strada Principală nr. 12, lângă școala generală"
              :required="true"
              :rows="3"
              :error="submitted ? errors.address : undefined"
            />
          </UiFormItem>
        </UiFormRow>
      </div>

      <!-- Când -->
      <div class="form-section">
        <div class="form-section__header">
          <h3 class="form-section__title">Când are loc campania?</h3>
        </div>
        <UiFormRow>
          <UiFormItem :grow="false" basis="auto">
            <UiCheckbox id="campaign-multiday" v-model="form.isMultiDay">
              Campania durează mai multe zile
            </UiCheckbox>
          </UiFormItem>
        </UiFormRow>
        <UiFormRow :nowrap="!isMobile">
          <UiFormItem basis="160px">
            <UiInput
              id="campaign-date-start"
              v-model="form.dateStart"
              :label="form.isMultiDay ? 'Data început' : 'Data'"
              type="date"
              :min="todayISO"
              :required="true"
              :error="submitted ? errors.dateStart : undefined"
            />
          </UiFormItem>
          <UiFormItem v-if="form.isMultiDay" basis="160px">
            <UiInput
              id="campaign-date-end"
              v-model="form.dateEnd"
              label="Data sfârșit"
              type="date"
              :min="form.dateStart || todayISO"
              :required="true"
              :error="submitted ? errors.dateEnd : undefined"
            />
          </UiFormItem>
        </UiFormRow>
        <UiFormRow :nowrap="!isMobile">
          <UiFormItem basis="140px">
            <UiSelect
              id="campaign-time-start"
              v-model="form.timeStart"
              label="Ora început"
              :options="timeOptions"
              :required="true"
              :error="submitted ? errors.timeStart : undefined"
            />
          </UiFormItem>
          <UiFormItem basis="140px">
            <UiSelect
              id="campaign-time-end"
              v-model="form.timeEnd"
              label="Ora sfârșit"
              :options="timeOptions"
              :required="true"
              :error="submitted ? errors.timeEnd : undefined"
            />
          </UiFormItem>
        </UiFormRow>
      </div>

      <!-- Specii -->
      <fieldset class="form-section form-section--fieldset">
        <div class="form-section__header">
          <legend class="form-section__title">Ce poți steriliza?</legend>
        </div>
        <UiFormRow>
          <UiFormItem :grow="false" basis="auto">
            <UiCheckbox id="campaign-dogs" v-model="form.hasDogs">
              Câini
            </UiCheckbox>
          </UiFormItem>
          <UiFormItem :grow="false" basis="auto">
            <UiCheckbox id="campaign-cats" v-model="form.hasCats">
              Pisici
            </UiCheckbox>
          </UiFormItem>
        </UiFormRow>
        <p v-if="submitted && errors.species" class="campaign-form__error" role="alert">
          {{ errors.species }}
        </p>

        <UiFormRow v-if="form.hasDogs || form.hasCats" :nowrap="!isMobile">
          <UiFormItem v-if="form.hasDogs" basis="160px">
            <UiInput
              id="campaign-slots-dogs"
              v-model="slotsDogsStr"
              label="Locuri pentru câini"
              type="number"
              :min="1"
              :max="500"
              placeholder="ex: 20"
              :required="true"
              :error="submitted ? errors.slotsDogs : undefined"
            />
          </UiFormItem>
          <UiFormItem v-if="form.hasCats" basis="160px">
            <UiInput
              id="campaign-slots-cats"
              v-model="slotsCatsStr"
              label="Locuri pentru pisici"
              type="number"
              :min="1"
              :max="500"
              placeholder="ex: 30"
              :required="true"
              :error="submitted ? errors.slotsCats : undefined"
            />
          </UiFormItem>
        </UiFormRow>
      </fieldset>

      <!-- Medic + telefon public -->
      <div class="form-section">
        <div class="form-section__header">
          <h3 class="form-section__title">Ce apare public?</h3>
        </div>
        <UiFormRow>
          <UiFormItem>
            <UiInput
              id="campaign-doctor"
              v-model="form.doctor"
              label="Medic veterinar (opțional)"
              placeholder="ex: Dr. Ionescu Maria"
            />
          </UiFormItem>
        </UiFormRow>
        <UiFormRow>
          <UiFormItem :grow="false" basis="auto">
            <UiCheckbox id="campaign-same-phone" v-model="form.samePublicPhone">
              Folosește telefonul de contact și ca telefon public
            </UiCheckbox>
          </UiFormItem>
        </UiFormRow>
        <UiFormRow v-if="!form.samePublicPhone">
          <UiFormItem basis="200px">
            <UiPhoneInput
              id="campaign-phone-public"
              v-model="form.phonePublic"
              label="Telefon public (afișat pe campanie)"
              :error="submitted ? errors.phonePublic : undefined"
            />
          </UiFormItem>
        </UiFormRow>
      </div>

      <!-- GDPR + Submit -->
      <div class="form-section form-section--footer">
        <UiFormRow>
          <UiFormItem>
            <UiCheckbox
              id="campaign-gdpr"
              v-model="form.gdprConsent"
              :required="true"
              :error="submitted ? errors.gdprConsent : undefined"
            >
              Sunt de acord cu
              <NuxtLink to="/politica-de-confidentialitate" target="_blank">politica de confidențialitate</NuxtLink>
              și prelucrarea datelor organizației.
            </UiCheckbox>
          </UiFormItem>
        </UiFormRow>

        <Transition name="error-banner">
          <UiFormRow v-if="submitted && errorCount > 0">
            <UiFormItem basis="100%">
              <div class="campaign-form__error-banner" role="alert">
                <AlertCircle :size="16" />
                <span>
                  {{ errorCount === 1 ? 'Un câmp necesită' : `${errorCount} câmpuri necesită` }} corectare.
                </span>
              </div>
            </UiFormItem>
          </UiFormRow>
        </Transition>

        <UiFormRow>
          <UiFormItem basis="100%">
            <div :class="{ 'campaign-form__btn--shake': shaking }">
              <UiButton type="submit" variant="primary" :block="true">
                Continuă spre previzualizare
              </UiButton>
            </div>
          </UiFormItem>
        </UiFormRow>
      </div>
    </template>

    <!-- ============================================================ -->
    <!-- STEP 2 — Preview                                               -->
    <!-- ============================================================ -->
    <template v-else>
      <CampaignCard :campaign="cardData" :show-call-cta="true" />

      <div v-if="hcaptchaSiteKey" class="campaign-form__captcha">
        <ClientOnly>
          <VueHcaptcha
            ref="hcaptchaRef"
            :sitekey="hcaptchaSiteKey"
            @verify="onCaptchaVerify"
            @expired="onCaptchaExpired"
            @error="onCaptchaError"
          />
        </ClientOnly>
        <p v-if="captchaError" class="campaign-form__error" role="alert">
          {{ captchaError }}
        </p>
      </div>

      <div class="campaign-form__preview-actions">
        <UiButton type="button" variant="ghost" :disabled="submitting" @click="goBackToEdit">
          <ArrowLeft :size="18" />
          Înapoi la editare
        </UiButton>
        <UiButton
          type="submit"
          variant="primary"
          :loading="submitting"
          :disabled="submitting || (!!hcaptchaSiteKey && !hcaptchaToken)"
        >
          Trimite spre aprobare
        </UiButton>
      </div>
    </template>
  </form>
</template>

<script setup lang="ts">
import VueHcaptcha from '@hcaptcha/vue3-hcaptcha'
import { Users, ArrowLeft, AlertCircle } from 'lucide-vue-next'

const emit = defineEmits<{ stepChange: [step: 1 | 2] }>()
import type {
  CampaignCardData,
  CampaignFormState,
  CampaignSubmission,
  CampaignSubmissionResponse,
} from '~/types'

const router = useRouter()
const runtimeConfig = useRuntimeConfig()
const hcaptchaSiteKey = runtimeConfig.public.hcaptchaSiteKey as string
const { counties, init: initLocations } = useLocationData()
const organizerSubmission = useOrganizerSubmission()
const toast = useToast()

const hcaptchaRef = ref<InstanceType<typeof VueHcaptcha> | null>(null)
const hcaptchaToken = ref('')
const captchaError = ref('')

function onCaptchaVerify(token: string) {
  hcaptchaToken.value = token
  captchaError.value = ''
}
function onCaptchaExpired() { hcaptchaToken.value = '' }
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

const todayISO = new Date().toISOString().slice(0, 10)

const timeOptions = Array.from({ length: 24 }, (_, h) => {
  const hh = h.toString().padStart(2, '0')
  return { value: `${hh}:00`, label: `${hh}:00` }
})

const form = reactive<CampaignFormState>({
  organizationName: '',
  contactEmail: '',
  contactPhone: '',
  samePublicPhone: true,
  phonePublic: '',
  county: '',
  locality: '',
  address: '',
  dateStart: '',
  isMultiDay: false,
  dateEnd: '',
  timeStart: '09:00',
  timeEnd: '20:00',
  hasDogs: false,
  hasCats: false,
  slotsDogs: undefined,
  slotsCats: undefined,
  doctor: '',
  gdprConsent: false,
})

// Must be after `form` — getter closes over the reactive object.
const { localities, loading: localityLoading, search: searchLocality } = useLocalities(() => form.county)

const slotsDogsStr = computed({
  get: () => form.slotsDogs?.toString() ?? '',
  set: (v: string) => { form.slotsDogs = v ? Number(v) : undefined },
})
const slotsCatsStr = computed({
  get: () => form.slotsCats?.toString() ?? '',
  set: (v: string) => { form.slotsCats = v ? Number(v) : undefined },
})

// Live "people waiting" stats — re-fetches via /api/stats/locality (GET /stats/locality on the backend)
// whenever county or locality change.
const { localityCount, countyCount, loading: waitingLoading } = useLocalityWaitingCount(
  () => form.county,
  () => form.locality,
)

interface Seg { t: string; b?: true }

const waitingParts = computed<Seg[]>(() => {
  if (!form.county || !form.locality) return []
  if (waitingLoading.value) return [{ t: 'Verificăm câți oameni așteaptă în zonă…' }]

  if (localityCount.value > 0) {
    const n = localityCount.value
    const word = n === 1 ? 'persoană' : 'persoane'
    return [
      { t: `${n} ${word}`, b: true },
      { t: ' din ' },
      { t: form.locality, b: true },
      { t: ' așteaptă o campanie.' },
    ]
  }
  if (countyCount.value > 0) {
    const n = countyCount.value
    const word = n === 1 ? 'persoană' : 'persoane'
    return [
      { t: `${n} ${word}`, b: true },
      { t: ' din județul ' },
      { t: countyName.value, b: true },
      { t: ' așteaptă o campanie.' },
    ]
  }
  return []
})

const step = ref<1 | 2>(1)
const submitted = ref(false)
const submitting = ref(false)
const shaking = ref(false)
const errors = ref<Record<string, string>>({})
const errorCount = computed(() => Object.keys(errors.value).length)

function validate(): boolean {
  const e: Record<string, string> = {}

  if (!form.organizationName.trim()) e.organizationName = 'Numele organizației este obligatoriu.'

  if (!form.contactEmail.trim()) e.contactEmail = 'Emailul este obligatoriu.'
  else if (!isValidEmail(form.contactEmail)) e.contactEmail = 'Adresă de email invalidă.'

  const contactPhoneClean = stripPhone(form.contactPhone)
  if (!contactPhoneClean) e.contactPhone = 'Telefonul de contact este obligatoriu.'
  else if (!isValidPhone(form.contactPhone)) e.contactPhone = 'Introdu un număr de telefon valid (ex: 0712 345 678).'

  if (!form.samePublicPhone) {
    const publicPhoneClean = stripPhone(form.phonePublic)
    if (!publicPhoneClean) e.phonePublic = 'Telefonul public este obligatoriu.'
    else if (!isValidPhone(form.phonePublic)) e.phonePublic = 'Introdu un număr de telefon valid (ex: 0712 345 678).'
  }

  if (!form.county) e.county = 'Alege județul.'
  if (!form.locality) e.locality = 'Alege localitatea.'
  if (!form.address.trim()) e.address = 'Adresa este obligatorie.'

  if (!form.dateStart) e.dateStart = 'Data este obligatorie.'
  else if (form.dateStart < todayISO) e.dateStart = 'Data trebuie să fie în viitor.'

  if (form.isMultiDay) {
    if (!form.dateEnd) e.dateEnd = 'Data de sfârșit este obligatorie.'
    else if (form.dateEnd < form.dateStart) e.dateEnd = 'Data de sfârșit nu poate fi înainte de început.'
  }

  if (!form.timeStart) e.timeStart = 'Ora de început este obligatorie.'
  if (!form.timeEnd) e.timeEnd = 'Ora de sfârșit este obligatorie.'
  // Only enforce end-after-start within a single day; multi-day campaigns can
  // legitimately end at an earlier clock time on a later date.
  if (!form.isMultiDay && form.timeStart && form.timeEnd && form.timeEnd <= form.timeStart) {
    e.timeEnd = 'Ora de sfârșit trebuie să fie după ora de început.'
  }

  if (!form.hasDogs && !form.hasCats) e.species = 'Alege cel puțin o specie.'
  if (form.hasDogs && (!form.slotsDogs || form.slotsDogs < 1)) e.slotsDogs = 'Introdu numărul de locuri.'
  if (form.hasCats && (!form.slotsCats || form.slotsCats < 1)) e.slotsCats = 'Introdu numărul de locuri.'

  if (!form.gdprConsent) e.gdprConsent = 'Trebuie să accepți politica de confidențialitate.'

  errors.value = e
  return Object.keys(e).length === 0
}

watch(() => ({ ...form }), () => {
  if (submitted.value) validate()
}, { deep: true })

function onCountyChange() {
  form.locality = ''
}

const countyName = computed(() =>
  counties.value.find(c => c.value === form.county)?.label ?? form.county,
)

const cardData = computed<CampaignCardData>(() => {
  const phonePublic = form.samePublicPhone
    ? stripPhone(form.contactPhone)
    : stripPhone(form.phonePublic)
  return {
    organizationName: form.organizationName.trim(),
    countyName: countyName.value,
    locality: form.locality,
    address: form.address.trim(),
    dateStart: form.dateStart,
    dateEnd: form.isMultiDay ? form.dateEnd : form.dateStart,
    timeStart: form.timeStart,
    timeEnd: form.timeEnd,
    species: [
      ...(form.hasDogs ? ['dog' as const] : []),
      ...(form.hasCats ? ['cat' as const] : []),
    ],
    slotsDogs: form.hasDogs ? form.slotsDogs : undefined,
    slotsCats: form.hasCats ? form.slotsCats : undefined,
    doctor: form.doctor.trim() || undefined,
    phonePublic,
  }
})

function goBackToEdit() {
  resetCaptcha()
  step.value = 1
  emit('stepChange', 1)
  if (import.meta.client) window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function handleSubmit() {
  // Step 1 — validate then advance to preview.
  if (step.value === 1) {
    submitted.value = true
    if (!validate()) {
      await nextTick()
      const firstError = document.querySelector<HTMLElement>('.ui-field--error')
      firstError?.scrollIntoView({ behavior: 'smooth', block: 'center' })
      shaking.value = true
      setTimeout(() => { shaking.value = false }, 500)
      return
    }
    step.value = 2
    emit('stepChange', 2)
    if (import.meta.client) window.scrollTo({ top: 0, behavior: 'smooth' })
    return
  }

  // Step 2 — POST to backend and persist session.
  if (hcaptchaSiteKey && !hcaptchaToken.value) {
    captchaError.value = 'Te rugăm să confirmi că nu ești robot.'
    return
  }
  submitting.value = true
  try {
    const payload: CampaignSubmission = {
      organizationName: form.organizationName.trim(),
      contactEmail: form.contactEmail.trim(),
      contactPhone: stripPhone(form.contactPhone),
      phonePublic: form.samePublicPhone ? stripPhone(form.contactPhone) : stripPhone(form.phonePublic),
      county: form.county,
      locality: form.locality,
      address: form.address.trim(),
      dateStart: form.dateStart,
      dateEnd: form.isMultiDay ? form.dateEnd : form.dateStart,
      timeStart: form.timeStart,
      timeEnd: form.timeEnd,
      species: [
        ...(form.hasDogs ? ['dog' as const] : []),
        ...(form.hasCats ? ['cat' as const] : []),
      ],
      slotsDogs: form.hasDogs ? form.slotsDogs : undefined,
      slotsCats: form.hasCats ? form.slotsCats : undefined,
      doctor: form.doctor.trim() || undefined,
      gdprConsent: form.gdprConsent,
    }

    const response = await $fetch<CampaignSubmissionResponse>('/api/campaigns/submit', {
      method: 'POST',
      body: { ...payload, hcaptchaToken: hcaptchaToken.value || undefined },
    })

    organizerSubmission.setSession({
      campaign: payload,
      countyName: countyName.value,
      submissionId: response.submissionId,
      status: response.status,
      stats: response.stats,
      submittedAt: new Date().toISOString(),
    })

    await router.push('/confirmare-campanie')
  } catch (err: unknown) {
    toast.error(extractApiError(err))
    resetCaptcha()
    // Stay on the preview so the user can retry without re-entering everything.
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.campaign-form {
  display: flex;
  flex-direction: column;
  gap: 0;
  text-align: left;
}

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

.campaign-form__error {
  font-size: var(--font-size-sm);
  color: var(--color-error);
}

.campaign-form__error-banner {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-error);
  background: rgba(220, 38, 38, 0.06);
  border: 1px solid rgba(220, 38, 38, 0.25);
  border-radius: var(--radius-md);
  padding: var(--space-sm) var(--space-md);
}

.error-banner-enter-active,
.error-banner-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}
.error-banner-enter-from,
.error-banner-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

@keyframes campaign-shake {
  0%, 100% { transform: translateX(0); }
  20%       { transform: translateX(-6px); }
  40%       { transform: translateX(6px); }
  60%       { transform: translateX(-4px); }
  80%       { transform: translateX(4px); }
}

.campaign-form__btn--shake {
  animation: campaign-shake 0.45s ease;
}

.campaign-form__waiting {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  background: var(--color-bg-muted, #f8fafc);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
  margin: 0;
}

.campaign-form__waiting :deep(strong) {
  color: var(--color-primary);
}

/* ---- Preview step ---- */
.campaign-form__preview-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-top: var(--space-lg);
  justify-content: space-between;
}

.campaign-form__preview-actions .ui-btn {
  flex: 1 1 200px;
}
</style>

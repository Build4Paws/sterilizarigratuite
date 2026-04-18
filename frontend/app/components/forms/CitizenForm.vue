<template>
  <form class="citizen-form" novalidate @submit.prevent="handleSubmit">
    <UiAlert v-if="submitError" variant="error">
      {{ submitError }}
    </UiAlert>

    <UiInput
      id="citizen-name"
      v-model="form.name"
      label="Nume"
      placeholder="Numele tău complet"
      :required="true"
      :error="touched.name ? errors.name : undefined"
      @blur="touch('name')"
    />

    <div class="citizen-form__row">
      <UiInput
        id="citizen-phone"
        v-model="form.phone"
        label="Telefon"
        type="tel"
        placeholder="07XX XXX XXX"
        :error="touched.phone ? errors.phone : undefined"
        @blur="touch('phone')"
      />
      <UiInput
        id="citizen-email"
        v-model="form.email"
        label="Email"
        type="email"
        placeholder="adresa@email.com"
        :error="touched.email ? errors.email : undefined"
        @blur="touch('email')"
      />
    </div>
    <p class="citizen-form__hint">Completează măcar unul: telefon sau email.</p>

    <div class="citizen-form__row">
      <UiSelect
        id="citizen-county"
        v-model="form.county"
        label="Județ"
        placeholder="Alege județul"
        :options="counties"
        :required="true"
        :error="touched.county ? errors.county : undefined"
        @blur="touch('county')"
        @update:model-value="onCountyChange"
      />
      <UiSelect
        id="citizen-locality"
        v-model="form.locality"
        label="Localitate"
        placeholder="Alege localitatea"
        :options="localities"
        :required="true"
        :disabled="!form.county"
        :error="touched.locality ? errors.locality : undefined"
        @blur="touch('locality')"
      />
    </div>

    <fieldset class="citizen-form__species">
      <legend class="citizen-form__species-legend">Specii</legend>
      <div class="citizen-form__species-checks">
        <UiCheckbox id="citizen-dogs" v-model="form.hasDogs">
          Câini
        </UiCheckbox>
        <UiCheckbox id="citizen-cats" v-model="form.hasCats">
          Pisici
        </UiCheckbox>
      </div>
      <p v-if="touched.species && errors.species" class="citizen-form__field-error" role="alert">
        {{ errors.species }}
      </p>

      <div v-if="form.hasDogs || form.hasCats" class="citizen-form__counts">
        <UiSelect
          v-if="form.hasDogs"
          id="citizen-dog-count"
          v-model="dogCountStr"
          label="Câți câini?"
          placeholder="Alege"
          :options="countOptions"
        />
        <UiSelect
          v-if="form.hasCats"
          id="citizen-cat-count"
          v-model="catCountStr"
          label="Câte pisici?"
          placeholder="Alege"
          :options="countOptions"
        />
      </div>
    </fieldset>

    <UiCheckbox
      id="citizen-gdpr"
      v-model="form.gdprConsent"
      :required="true"
      :error="touched.gdprConsent ? errors.gdprConsent : undefined"
    >
      Sunt de acord cu
      <NuxtLink to="/confidentialitate" target="_blank">politica de confidențialitate</NuxtLink>
      și prelucrarea datelor personale.
    </UiCheckbox>

    <UiButton type="submit" variant="primary" :loading="submitting" :disabled="submitting">
      Înscrie-mă
    </UiButton>
  </form>
</template>

<script setup lang="ts">
import type { CitizenRegistration } from '~/types'

const router = useRouter()
const { counties, localities, setCounty, init: initLocations } = useLocationData()

onMounted(() => {
  initLocations()
})

const form = reactive<CitizenRegistration>({
  name: '',
  phone: '',
  email: '',
  county: '',
  locality: '',
  hasDogs: false,
  hasCats: false,
  dogCount: undefined,
  catCount: undefined,
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
const submitError = ref('')

const errors = ref<Record<string, string>>({})
const touched = ref<Record<string, boolean>>({})

const countOptions = Array.from({ length: 10 }, (_, i) => ({
  value: String(i + 1),
  label: String(i + 1),
}))


function validate(): boolean {
  const e: Record<string, string> = {}

  if (!form.name.trim()) e.name = 'Numele este obligatoriu.'
  if (!form.phone?.trim() && !form.email?.trim()) {
    e.phone = 'Completează telefonul sau emailul.'
    e.email = 'Completează telefonul sau emailul.'
  }
  if (form.phone?.trim() && !/^(\+?40|0)[0-9]{9}$/.test(form.phone.replace(/\s/g, ''))) {
    e.phone = 'Număr de telefon invalid.'
  }
  if (form.email?.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    e.email = 'Adresă de email invalidă.'
  }
  if (!form.county) e.county = 'Alege județul.'
  if (!form.locality) e.locality = 'Alege localitatea.'
  if (!form.hasDogs && !form.hasCats) e.species = 'Alege cel puțin o specie.'
  if (!form.gdprConsent) e.gdprConsent = 'Trebuie să accepți politica de confidențialitate.'

  errors.value = e
  return Object.keys(e).length === 0
}

function touch(field: string) {
  touched.value[field] = true
  validate()
}

function onCountyChange(code: string) {
  form.locality = ''
  setCounty(code)
}

async function handleSubmit() {
  // Mark all fields as touched
  for (const key of ['name', 'phone', 'email', 'county', 'locality', 'species', 'gdprConsent']) {
    touched.value[key] = true
  }

  if (!validate()) return

  submitting.value = true
  submitError.value = ''

  try {
    const payload = {
      name: form.name.trim(),
      phone: form.phone?.trim() || undefined,
      email: form.email?.trim() || undefined,
      county: form.county,
      locality: form.locality,
      species: [
        ...(form.hasDogs ? ['dog' as const] : []),
        ...(form.hasCats ? ['cat' as const] : []),
      ],
      dogCount: form.hasDogs ? (form.dogCount ?? 1) : undefined,
      catCount: form.hasCats ? (form.catCount ?? 1) : undefined,
    }

    await $api('/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })

    const channel = form.phone && form.email ? 'both' : form.phone ? 'sms' : 'email'
    await router.push({
      path: '/confirmare',
      query: { channel, county: form.county },
    })
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'A apărut o eroare. Te rugăm să încerci din nou.'
    submitError.value = message
  } finally {
    submitting.value = false
  }
}

</script>

<style scoped>
.citizen-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
  text-align: left;
}

.citizen-form__row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-md);
}

.citizen-form__hint {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  margin-top: calc(-1 * var(--space-md));
}

.citizen-form__species {
  border: none;
  padding: 0;
}

.citizen-form__species-legend {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-text);
  margin-bottom: var(--space-sm);
}

.citizen-form__species-checks {
  display: flex;
  gap: var(--space-xl);
}

.citizen-form__counts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-md);
  margin-top: var(--space-md);
}

.citizen-form__field-error {
  font-size: var(--font-size-sm);
  color: var(--color-error);
  margin-top: var(--space-xs);
}

@media (max-width: 640px) {
  .citizen-form__row,
  .citizen-form__counts {
    grid-template-columns: 1fr;
  }
}
</style>

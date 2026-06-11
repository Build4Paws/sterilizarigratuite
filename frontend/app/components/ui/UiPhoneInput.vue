<template>
  <div :class="['ui-field', { 'ui-field--error': error }]">
    <label :for="id" class="ui-field__label">
      {{ label }}
      <span v-if="required" class="ui-field__required" aria-hidden="true">*</span>
    </label>
    <div class="ui-phone">
      <span class="ui-phone__prefix">
        <svg class="ui-phone__flag" viewBox="0 0 640 480" aria-hidden="true">
          <rect width="213.3" height="480" fill="#00319c"/>
          <rect x="213.3" width="213.4" height="480" fill="#ffde00"/>
          <rect x="426.7" width="213.3" height="480" fill="#de2110"/>
        </svg>
      </span>
      <input
        :id="id"
        ref="inputRef"
        type="tel"
        inputmode="numeric"
        :value="displayValue"
        placeholder="07XX XXX XXX"
        :required="required"
        :aria-invalid="!!error"
        :aria-describedby="error ? `${id}-error` : undefined"
        class="ui-phone__input"
        maxlength="12"
        @input="onInput"
        @blur="$emit('blur')"
        @keydown="onKeydown"
      />
    </div>
    <p v-if="error" :id="`${id}-error`" class="ui-field__error" role="alert">
      {{ error }}
    </p>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  modelValue?: string
  label: string
  id: string
  required?: boolean
  error?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  blur: []
}>()

const inputRef = ref<HTMLInputElement>()

function digitsOnly(str: string): string {
  return str.replace(/\D/g, '')
}

// Normalize any user/paste input to the national format: a single leading 0
// followed by up to 9 subscriber digits (e.g. "0740123456"). Romanians write
// their numbers starting with 0, so the leading 0 is preserved as typed and
// international prefixes (+40 / 0040 / 40) are folded back to it.
function toNational(raw: string): string {
  let cleaned = raw.replace(/\s/g, '')
  // Fold explicit country-code prefixes back to the national leading 0.
  // `+40` is also our canonical storage form, so handle it regardless of length.
  if (cleaned.startsWith('+40')) cleaned = `0${cleaned.slice(3)}`
  else if (cleaned.startsWith('0040')) cleaned = `0${cleaned.slice(4)}`
  else if (cleaned.startsWith('+')) cleaned = cleaned.slice(1)
  let digits = digitsOnly(cleaned)
  // Bare country code pasted without a + (e.g. "40740123456")
  if (digits.startsWith('40') && digits.length >= 11) digits = `0${digits.slice(2)}`
  else if (!digits.startsWith('0') && digits.length) digits = `0${digits}`
  // Collapse any run of leading zeros to a single 0
  digits = digits.replace(/^0+/, '0')
  return digits.slice(0, 10)
}

function formatNational(digits: string): string {
  // Format as: 07XX XXX XXX
  if (digits.length <= 4) return digits
  if (digits.length <= 7) return `${digits.slice(0, 4)} ${digits.slice(4)}`
  return `${digits.slice(0, 4)} ${digits.slice(4, 7)} ${digits.slice(7, 10)}`
}

// Subscriber digits (national minus the leading 0) used for +40 storage.
function toSubscriber(raw: string): string {
  return toNational(raw).replace(/^0/, '')
}

const displayValue = computed(() => {
  return formatNational(toNational(props.modelValue ?? ''))
})

function onInput(e: Event) {
  const input = e.target as HTMLInputElement
  const national = toNational(input.value)
  const subscriber = national.replace(/^0/, '')
  // Store the canonical +40 form regardless of how the user typed it
  if (subscriber.length > 0) {
    emit('update:modelValue', `+40${subscriber}`)
  } else {
    emit('update:modelValue', '')
  }
  // Re-apply the formatted national value after Vue re-renders. Use the value
  // captured above so a lone leading "0" stays visible as the user types it.
  nextTick(() => {
    input.value = formatNational(national)
  })
}

function onKeydown(e: KeyboardEvent) {
  // Allow: backspace, delete, tab, escape, enter, arrows
  const allowed = ['Backspace', 'Delete', 'Tab', 'Escape', 'Enter', 'ArrowLeft', 'ArrowRight', 'Home', 'End']
  if (allowed.includes(e.key)) return
  // Allow Ctrl/Cmd + A, C, V, X
  if ((e.ctrlKey || e.metaKey) && ['a', 'c', 'v', 'x'].includes(e.key.toLowerCase())) return
  // Block non-digit keys
  if (!/^\d$/.test(e.key)) {
    e.preventDefault()
  }
}
</script>

<style scoped>
.ui-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.ui-field__label {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-text);
}

.ui-field__required {
  color: var(--color-error);
}

.ui-phone {
  display: flex;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-input-bg);
  overflow: hidden;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.ui-phone:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(4, 26, 73, 0.1);
}

.ui-field--error .ui-phone {
  border-color: var(--color-error);
}

.ui-field--error .ui-phone:focus-within {
  box-shadow: 0 0 0 3px rgba(250, 45, 45, 0.1);
}

.ui-phone__prefix {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.625rem 0.75rem;
  background: var(--color-slate-50);
  border-right: 1px solid var(--color-border);
  flex-shrink: 0;
  user-select: none;
}

.ui-phone__flag {
  width: 20px;
  height: 15px;
  border-radius: 2px;
  flex-shrink: 0;
}

.ui-phone__input {
  flex: 1;
  min-width: 0;
  font-family: var(--font-body);
  font-size: var(--font-size-base);
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.04em;
  padding: 0.625rem 0.75rem;
  border: none;
  background: transparent;
  color: var(--color-text);
  outline: none;
}

.ui-phone__input::placeholder {
  color: var(--color-slate-300);
  letter-spacing: 0.04em;
}

.ui-field__error {
  font-size: var(--font-size-sm);
  color: var(--color-error);
}
</style>

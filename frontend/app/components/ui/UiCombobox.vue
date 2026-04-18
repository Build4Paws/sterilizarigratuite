<template>
  <div
    ref="wrapperRef"
    :class="['ui-field', { 'ui-field--error': error, 'ui-field--open': open }]"
  >
    <label :for="id" class="ui-field__label">
      {{ label }}
      <span v-if="required" class="ui-field__required" aria-hidden="true">*</span>
    </label>

    <div class="ui-combobox">
      <input
        :id="id"
        ref="inputRef"
        type="text"
        role="combobox"
        autocomplete="off"
        :value="displayValue"
        :placeholder="selectedLabel || placeholder"
        :required="required"
        :disabled="disabled"
        :aria-expanded="open"
        :aria-activedescendant="activeDescendant"
        :aria-invalid="!!error"
        :aria-describedby="error ? `${id}-error` : undefined"
        aria-autocomplete="list"
        :aria-controls="`${id}-listbox`"
        class="ui-combobox__input"
        :class="{ 'ui-combobox__input--has-value': modelValue && !open }"
        @focus="onFocus"
        @input="onInput"
        @keydown="onKeydown"
      />
      <button
        v-if="modelValue && !disabled"
        type="button"
        class="ui-combobox__clear"
        tabindex="-1"
        aria-label="Șterge selecția"
        @mousedown.prevent="clearSelection"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" width="14" height="14">
          <path d="M18 6 6 18M6 6l12 12" />
        </svg>
      </button>
      <span class="ui-combobox__chevron" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
          <path d="m6 9 6 6 6-6" />
        </svg>
      </span>

      <ul
        v-show="open"
        :id="`${id}-listbox`"
        ref="listboxRef"
        role="listbox"
        class="ui-combobox__list"
      >
        <li
          v-if="filtered.length === 0"
          class="ui-combobox__empty"
        >
          Niciun rezultat pentru „{{ query }}"
        </li>
        <li
          v-for="(opt, i) in filtered"
          :id="`${id}-opt-${i}`"
          :key="opt.value"
          role="option"
          :aria-selected="opt.value === modelValue"
          :class="['ui-combobox__option', {
            'ui-combobox__option--active': i === activeIndex,
            'ui-combobox__option--selected': opt.value === modelValue,
          }]"
          @mousedown.prevent="select(opt)"
          @mouseenter="activeIndex = i"
        >
          {{ opt.label }}
        </li>
      </ul>
    </div>

    <p v-if="error" :id="`${id}-error`" class="ui-field__error" role="alert">
      {{ error }}
    </p>
  </div>
</template>

<script setup lang="ts">
interface Option {
  value: string
  label: string
}

const props = defineProps<{
  modelValue: string
  label: string
  id: string
  placeholder?: string
  options: Option[]
  required?: boolean
  disabled?: boolean
  error?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  blur: []
}>()

const wrapperRef = ref<HTMLElement>()
const inputRef = ref<HTMLInputElement>()
const listboxRef = ref<HTMLUListElement>()
const open = ref(false)
const query = ref('')
const activeIndex = ref(-1)

function stripDiacritics(str: string): string {
  return str.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
}

const selectedLabel = computed(() => {
  if (!props.modelValue) return ''
  const opt = props.options.find(o => o.value === props.modelValue)
  return opt?.label ?? ''
})

const displayValue = computed(() => {
  if (open.value) return query.value
  return selectedLabel.value
})

function matchesAtWordBoundary(text: string, search: string): boolean {
  const normalized = stripDiacritics(text)
  if (normalized.startsWith(search)) return true
  // Match after space or hyphen (word boundaries)
  for (let i = 1; i < normalized.length; i++) {
    if ((normalized[i - 1] === ' ' || normalized[i - 1] === '-') && normalized.startsWith(search, i)) {
      return true
    }
  }
  return false
}

const filtered = computed(() => {
  if (!query.value) return props.options
  const q = stripDiacritics(query.value.trim())
  if (!q) return props.options
  return props.options.filter(opt => matchesAtWordBoundary(opt.label, q))
})

const activeDescendant = computed(() => {
  if (activeIndex.value < 0 || activeIndex.value >= filtered.value.length) return undefined
  return `${props.id}-opt-${activeIndex.value}`
})

function onFocus() {
  open.value = true
  query.value = ''
  activeIndex.value = -1
}

function onInput(e: Event) {
  query.value = (e.target as HTMLInputElement).value
  activeIndex.value = -1
  if (!open.value) open.value = true
}

function select(opt: Option) {
  emit('update:modelValue', opt.value)
  query.value = ''
  open.value = false
  inputRef.value?.blur()
}

function clearSelection() {
  emit('update:modelValue', '')
  query.value = ''
  activeIndex.value = -1
  inputRef.value?.focus()
}

function close() {
  open.value = false
  query.value = ''
  activeIndex.value = -1
  emit('blur')
}

function scrollActiveIntoView() {
  nextTick(() => {
    const el = listboxRef.value?.children[activeIndex.value] as HTMLElement | undefined
    el?.scrollIntoView({ block: 'nearest' })
  })
}

function onKeydown(e: KeyboardEvent) {
  if (!open.value && (e.key === 'ArrowDown' || e.key === 'Enter')) {
    open.value = true
    e.preventDefault()
    return
  }

  switch (e.key) {
    case 'ArrowDown':
      e.preventDefault()
      activeIndex.value = Math.min(activeIndex.value + 1, filtered.value.length - 1)
      scrollActiveIntoView()
      break
    case 'ArrowUp':
      e.preventDefault()
      activeIndex.value = Math.max(activeIndex.value - 1, 0)
      scrollActiveIntoView()
      break
    case 'Enter':
      e.preventDefault()
      if (activeIndex.value >= 0 && activeIndex.value < filtered.value.length) {
        select(filtered.value[activeIndex.value])
      }
      break
    case 'Escape':
      e.preventDefault()
      close()
      break
    case 'Tab':
      close()
      break
  }
}

// Close on outside click
function onClickOutside(e: MouseEvent) {
  if (wrapperRef.value && !wrapperRef.value.contains(e.target as Node)) {
    close()
  }
}

onMounted(() => {
  document.addEventListener('mousedown', onClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('mousedown', onClickOutside)
})
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

.ui-combobox {
  position: relative;
}

.ui-combobox__input {
  width: 100%;
  font-family: var(--font-body);
  font-size: var(--font-size-base);
  padding: 0.625rem 2.5rem 0.625rem 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-input-bg);
  color: var(--color-text);
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.ui-combobox__input::placeholder {
  color: var(--color-text);
  opacity: 1;
}

.ui-combobox__input--has-value::placeholder {
  color: var(--color-text);
  opacity: 1;
}

.ui-field--open .ui-combobox__input {
  cursor: text;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(4, 26, 73, 0.1);
}

.ui-field--open .ui-combobox__input::placeholder {
  color: var(--color-slate-300);
  opacity: 1;
}

.ui-combobox__input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ui-combobox__chevron {
  position: absolute;
  right: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-slate-600);
  pointer-events: none;
  display: flex;
}

.ui-combobox__clear {
  position: absolute;
  right: 2.25rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--color-slate-600);
  cursor: pointer;
  padding: 2px;
  display: flex;
  border-radius: var(--radius-sm);
}

.ui-combobox__clear:hover {
  color: var(--color-text);
  background: var(--color-slate-100);
}

.ui-combobox__list {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  max-height: 240px;
  overflow-y: auto;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  z-index: 200;
  list-style: none;
  padding: var(--space-xs) 0;
  margin: 0;
}

.ui-combobox__option {
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  font-size: var(--font-size-sm);
  transition: background-color 0.1s, color 0.1s;
}

.ui-combobox__option--active {
  background: var(--color-slate-100);
  color: var(--color-primary);
}

.ui-combobox__option--selected {
  color: var(--color-accent);
  font-weight: 600;
}

.ui-combobox__empty {
  padding: 0.75rem;
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  text-align: center;
}

.ui-field--error .ui-combobox__input {
  border-color: var(--color-error);
}

.ui-field--error .ui-combobox__input:focus {
  box-shadow: 0 0 0 3px rgba(250, 45, 45, 0.1);
}

.ui-field__error {
  font-size: var(--font-size-sm);
  color: var(--color-error);
}
</style>

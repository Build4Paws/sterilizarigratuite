<template>
  <div ref="rootRef" :class="['ui-date', { 'ui-date--error': error }]">
    <label :for="id" class="ui-date__label">
      {{ label }}
      <span v-if="required" class="ui-date__required" aria-hidden="true">*</span>
    </label>

    <!-- Trigger styled like a text input. Native <input type=date> renders its
         value + calendar in the browser locale (no way to force Romanian), so we
         render everything ourselves via Intl.DateTimeFormat('ro-RO'). The bound
         value stays canonical ISO (yyyy-mm-dd) for the backend. -->
    <button
      :id="id"
      ref="triggerRef"
      type="button"
      class="ui-date__trigger"
      :class="{ 'ui-date__trigger--placeholder': !modelValue }"
      :aria-invalid="!!error"
      :aria-describedby="describedBy"
      aria-haspopup="dialog"
      :aria-expanded="open"
      @click="toggle"
      @keydown.down.prevent="openCalendar()"
    >
      <span class="ui-date__value">{{ modelValue ? formatField(modelValue) : placeholder }}</span>
      <Calendar class="ui-date__icon" :size="18" aria-hidden="true" />
    </button>

    <Transition name="ui-date-pop">
      <div
        v-if="open"
        class="ui-date__pop"
        role="dialog"
        aria-label="Alege data"
        aria-modal="false"
        @keydown.esc.prevent.stop="close(true)"
      >
        <div class="ui-date__head">
          <button
            type="button"
            class="ui-date__nav"
            :disabled="!canPrev"
            aria-label="Luna anterioară"
            @click="changeMonth(-1)"
          >
            <ChevronLeft :size="18" />
          </button>
          <span class="ui-date__title" aria-live="polite">{{ monthTitle }}</span>
          <button
            type="button"
            class="ui-date__nav"
            :disabled="!canNext"
            aria-label="Luna următoare"
            @click="changeMonth(1)"
          >
            <ChevronRight :size="18" />
          </button>
        </div>

        <div class="ui-date__weekdays" aria-hidden="true">
          <span v-for="(w, i) in WEEKDAYS_ABBR" :key="i">{{ w }}</span>
        </div>

        <div class="ui-date__grid" @keydown="onGridKey">
          <button
            v-for="d in days"
            :key="toISO(d)"
            type="button"
            class="ui-date__day"
            :class="{
              'ui-date__day--other': !isSameMonth(d, view),
              'ui-date__day--selected': isSelected(d),
              'ui-date__day--today': isToday(d),
            }"
            :data-iso="toISO(d)"
            :tabindex="isActive(d) ? 0 : -1"
            :disabled="isDisabled(d)"
            :aria-label="fullLabel(d)"
            :aria-current="isToday(d) ? 'date' : undefined"
            :aria-pressed="isSelected(d)"
            @click="select(d)"
          >
            {{ d.getDate() }}
          </button>
        </div>

        <div v-if="todayInRange" class="ui-date__foot">
          <button type="button" class="ui-date__today" @click="select(today)">
            Astăzi
          </button>
        </div>
      </div>
    </Transition>

    <p v-if="error" :id="`${id}-error`" class="ui-date__error" role="alert">
      {{ error }}
    </p>
    <p v-else-if="hint" :id="`${id}-hint`" class="ui-date__hint">
      {{ hint }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { Calendar, ChevronLeft, ChevronRight } from 'lucide-vue-next'
import { onClickOutside } from '@vueuse/core'

const props = defineProps<{
  /** ISO date string `yyyy-mm-dd` (the canonical form stored/sent to the backend). */
  modelValue?: string
  label: string
  id: string
  required?: boolean
  error?: string
  hint?: string
  /** ISO `yyyy-mm-dd` lower/upper bounds (inclusive). */
  min?: string
  max?: string
  placeholder?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  blur: []
}>()

const placeholder = computed(() => props.placeholder ?? 'zz/ll/aaaa')

// --- Romanian formatters (single source of truth for the language) ----------
const WEEKDAYS_ABBR = ['Lu', 'Ma', 'Mi', 'Jo', 'Vi', 'Sâ', 'Du']
const monthYearFmt = new Intl.DateTimeFormat('ro-RO', { month: 'long', year: 'numeric' })
const fullDateFmt = new Intl.DateTimeFormat('ro-RO', { day: 'numeric', month: 'long', year: 'numeric' })
const capitalize = (s: string) => s.charAt(0).toUpperCase() + s.slice(1)

// --- Date helpers (all local-time to avoid UTC day-shift bugs) --------------
function toISO(d: Date): string {
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${m}-${day}`
}
function parseISO(s: string): Date {
  const [y, m, d] = s.split('-')
  return new Date(Number(y), Number(m) - 1, Number(d))
}
function startOfDay(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate())
}
function startOfMonth(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth(), 1)
}
function addDays(d: Date, n: number): Date {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate() + n)
}
function isSameMonth(a: Date, b: Date): boolean {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth()
}

// Field display: numeric day-first `dd/mm/yyyy` (compact, unambiguously Romanian).
function formatField(iso: string): string {
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}
// Per-day accessible label, e.g. "15 iulie 2026".
function fullLabel(d: Date): string {
  return fullDateFmt.format(d)
}

const today = startOfDay(new Date())
const minDate = computed(() => (props.min ? parseISO(props.min) : null))
const maxDate = computed(() => (props.max ? parseISO(props.max) : null))

// --- Popover + calendar state ----------------------------------------------
const rootRef = ref<HTMLElement>()
const triggerRef = ref<HTMLButtonElement>()
const open = ref(false)
const view = ref(startOfMonth(props.modelValue ? parseISO(props.modelValue) : today))
const active = ref(props.modelValue ? parseISO(props.modelValue) : clamp(today))

const describedBy = computed(() => {
  if (props.error) return `${props.id}-error`
  if (props.hint) return `${props.id}-hint`
  return undefined
})

const monthTitle = computed(() => capitalize(monthYearFmt.format(view.value)))

// Six-week (42-cell) grid, Monday-first (Romanian week starts Monday).
const days = computed(() => {
  const first = startOfMonth(view.value)
  const offset = (first.getDay() + 6) % 7
  const start = addDays(first, -offset)
  return Array.from({ length: 42 }, (_, i) => addDays(start, i))
})

function isDisabled(d: Date): boolean {
  if (minDate.value && d < minDate.value) return true
  if (maxDate.value && d > maxDate.value) return true
  return false
}
function isSelected(d: Date): boolean {
  return !!props.modelValue && toISO(d) === props.modelValue
}
function isToday(d: Date): boolean {
  return toISO(d) === toISO(today)
}
function isActive(d: Date): boolean {
  return toISO(d) === toISO(active.value)
}

const canPrev = computed(() => !minDate.value || startOfMonth(view.value) > startOfMonth(minDate.value))
const canNext = computed(() => !maxDate.value || startOfMonth(view.value) < startOfMonth(maxDate.value))
const todayInRange = computed(() => !isDisabled(today))

function clamp(d: Date): Date {
  if (minDate.value && d < minDate.value) return new Date(minDate.value)
  if (maxDate.value && d > maxDate.value) return new Date(maxDate.value)
  return d
}

function openCalendar() {
  active.value = clamp(props.modelValue ? parseISO(props.modelValue) : today)
  view.value = startOfMonth(active.value)
  open.value = true
  focusActive()
}
function toggle() {
  open.value ? close(false) : openCalendar()
}
function close(refocus: boolean) {
  if (!open.value) return
  open.value = false
  emit('blur')
  if (refocus) triggerRef.value?.focus()
}

function changeMonth(delta: number) {
  view.value = new Date(view.value.getFullYear(), view.value.getMonth() + delta, 1)
}

function select(d: Date) {
  if (isDisabled(d)) return
  emit('update:modelValue', toISO(d))
  close(true)
}

function focusActive() {
  nextTick(() => {
    rootRef.value?.querySelector<HTMLElement>(`[data-iso="${toISO(active.value)}"]`)?.focus()
  })
}

function moveActive(delta: number) {
  const next = clamp(addDays(active.value, delta))
  active.value = next
  if (!isSameMonth(next, view.value)) view.value = startOfMonth(next)
  focusActive()
}

function onGridKey(e: KeyboardEvent) {
  const steps: Record<string, number> = {
    ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7,
  }
  if (e.key in steps) {
    e.preventDefault()
    moveActive(steps[e.key]!)
  }
  else if (e.key === 'PageUp') {
    e.preventDefault()
    moveActive(-7 * Math.round(daysInMonth(view.value) / 7) || -28)
  }
  else if (e.key === 'PageDown') {
    e.preventDefault()
    moveActive(7 * Math.round(daysInMonth(view.value) / 7) || 28)
  }
}
function daysInMonth(d: Date): number {
  return new Date(d.getFullYear(), d.getMonth() + 1, 0).getDate()
}

onClickOutside(rootRef, () => close(false))

// Keep the displayed month in sync if the bound value changes externally.
watch(() => props.modelValue, (v) => {
  if (v) view.value = startOfMonth(parseISO(v))
})
</script>

<style scoped>
.ui-date {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.ui-date__label {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-text);
}

.ui-date__required {
  color: var(--color-error);
}

/* Trigger — mirrors .ui-field__input so it sits inline with other fields. */
.ui-date__trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-sm);
  width: 100%;
  min-height: 2.625rem;
  padding: 0.625rem 0.75rem;
  font-family: var(--font-body);
  font-size: var(--font-size-base);
  text-align: left;
  color: var(--color-text);
  background: var(--color-input-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.ui-date__trigger:hover {
  border-color: var(--color-slate-600);
}

.ui-date__trigger:focus-visible {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(4, 26, 73, 0.1);
}

.ui-date__trigger--placeholder .ui-date__value {
  color: var(--color-slate-300);
}

.ui-date__icon {
  flex-shrink: 0;
  color: var(--color-text-muted);
}

.ui-date--error .ui-date__trigger {
  border-color: var(--color-error);
}

.ui-date--error .ui-date__trigger:focus-visible {
  box-shadow: 0 0 0 3px rgba(250, 45, 45, 0.1);
}

/* Popover calendar */
.ui-date__pop {
  position: absolute;
  top: calc(100% + var(--space-xs));
  left: 0;
  z-index: 50;
  width: 18rem;
  max-width: calc(100vw - 2 * var(--space-md));
  padding: var(--space-sm);
  background: var(--color-bg);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  box-shadow:
    0 4px 6px rgba(4, 26, 73, 0.04),
    0 12px 28px rgba(4, 26, 73, 0.14);
}

.ui-date__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-sm);
}

.ui-date__title {
  font-family: var(--font-heading);
  font-size: var(--font-size-base);
  font-weight: 600;
  color: var(--color-primary);
}

.ui-date__nav {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  color: var(--color-text);
  background: none;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.ui-date__nav:hover:not(:disabled) {
  background: var(--color-bg-muted);
  color: var(--color-accent);
}

.ui-date__nav:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 1px;
}

.ui-date__nav:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.ui-date__weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  margin-bottom: var(--space-xs);
}

.ui-date__weekdays span {
  text-align: center;
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-muted);
}

.ui-date__grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
}

.ui-date__day {
  display: flex;
  align-items: center;
  justify-content: center;
  aspect-ratio: 1;
  font-family: var(--font-body);
  font-size: var(--font-size-sm);
  color: var(--color-text);
  background: none;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.ui-date__day:hover:not(:disabled) {
  background: var(--color-bg-muted);
}

.ui-date__day:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: -2px;
}

.ui-date__day--other {
  color: var(--color-slate-300);
}

.ui-date__day--today {
  font-weight: 700;
  color: var(--color-accent);
}

.ui-date__day--selected,
.ui-date__day--selected:hover {
  color: var(--color-text-light);
  background: var(--color-primary);
}

.ui-date__day:disabled {
  color: var(--color-slate-300);
  opacity: 0.45;
  cursor: not-allowed;
}

.ui-date__foot {
  display: flex;
  justify-content: center;
  margin-top: var(--space-sm);
  padding-top: var(--space-sm);
  border-top: 1px solid var(--color-border-light);
}

.ui-date__today {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-accent);
  background: none;
  border: none;
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-md);
  cursor: pointer;
}

.ui-date__today:hover {
  background: var(--color-bg-muted);
}

.ui-date__today:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 1px;
}

.ui-date__error {
  font-size: var(--font-size-sm);
  color: var(--color-error);
}

.ui-date__hint {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

/* Popover transition */
.ui-date-pop-enter-active,
.ui-date-pop-leave-active {
  transition: opacity 0.16s ease, transform 0.16s ease;
  transform-origin: top left;
}

.ui-date-pop-enter-from,
.ui-date-pop-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.98);
}

@media (prefers-reduced-motion: reduce) {
  .ui-date__trigger,
  .ui-date__nav,
  .ui-date__day,
  .ui-date-pop-enter-active,
  .ui-date-pop-leave-active {
    transition: none;
  }
  .ui-date-pop-enter-from,
  .ui-date-pop-leave-to {
    transform: none;
  }
}
</style>

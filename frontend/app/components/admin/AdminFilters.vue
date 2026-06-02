<template>
  <div class="afilters">
    <div class="afilters__search">
      <Search :size="16" class="afilters__icon" />
      <input
        v-model="search"
        type="search"
        :placeholder="searchPlaceholder ?? 'Caută…'"
        class="afilters__input"
        aria-label="Caută"
      />
    </div>

    <select
      v-if="showCounty"
      v-model="county"
      class="afilters__select"
      aria-label="Filtrează după județ"
    >
      <option value="">Toate județele</option>
      <option v-for="c in counties ?? []" :key="c.value" :value="c.value">{{ c.label }}</option>
    </select>

    <select
      v-if="showLocality"
      v-model="locality"
      class="afilters__select"
      :disabled="!county"
      aria-label="Filtrează după localitate"
    >
      <option value="">{{ county ? 'Toate localitățile' : 'Alege un județ' }}</option>
      <option v-for="l in localities ?? []" :key="l.value" :value="l.value">{{ l.label }}</option>
    </select>

    <button
      v-if="hasActive"
      type="button"
      class="afilters__reset"
      @click="$emit('reset')"
    >
      <X :size="14" /> Resetează
    </button>
  </div>
</template>

<script setup lang="ts">
import { Search, X } from 'lucide-vue-next'

const search = defineModel<string>('search', { default: '' })
const county = defineModel<string>('county', { default: '' })
const locality = defineModel<string>('locality', { default: '' })

defineProps<{
  searchPlaceholder?: string
  counties?: { value: string; label: string }[]
  localities?: { value: string; label: string }[]
  showCounty?: boolean
  showLocality?: boolean
  hasActive?: boolean
}>()

defineEmits<{ reset: [] }>()
</script>

<style scoped>
.afilters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-sm);
}

.afilters__search {
  position: relative;
  flex: 1 1 240px;
  min-width: 200px;
}
.afilters__icon {
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-muted);
  pointer-events: none;
}
.afilters__input {
  width: 100%;
  font-family: var(--font-body);
  font-size: var(--font-size-sm);
  padding: 0.5rem 0.75rem 0.5rem 2.25rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg);
  color: var(--color-text);
  transition: border-color 0.16s ease, box-shadow 0.16s ease;
}
.afilters__input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(4, 26, 73, 0.1);
}

.afilters__select {
  font-family: var(--font-body);
  font-size: var(--font-size-sm);
  padding: 0.5rem 2rem 0.5rem 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg);
  color: var(--color-text);
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23475569' stroke-width='2'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 0.6rem center;
  max-width: 220px;
}
.afilters__select:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(4, 26, 73, 0.1);
}
.afilters__select:disabled { opacity: 0.5; cursor: not-allowed; }

.afilters__reset {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  padding: 0.5rem 0.75rem;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  font-weight: 600;
  cursor: pointer;
  transition: color 0.16s ease, background-color 0.16s ease;
}
.afilters__reset:hover { color: var(--color-accent); background: var(--color-slate-50); }

@media (max-width: 600px) {
  .afilters__search { flex-basis: 100%; }
  .afilters__select { flex: 1; max-width: none; }
}
</style>

import { ref, computed } from 'vue'

interface ValidationRule {
  validate: (value: unknown) => boolean
  message: string
}

type Rules = Record<string, ValidationRule[]>

export function useFormValidation<T extends Record<string, unknown>>(formData: T, rules: Rules) {
  const errors = ref<Record<string, string>>({})
  const touched = ref<Record<string, boolean>>({})

  function validateField(field: string) {
    const fieldRules = rules[field]
    if (!fieldRules) return true

    for (const rule of fieldRules) {
      if (!rule.validate(formData[field])) {
        errors.value[field] = rule.message
        return false
      }
    }
    delete errors.value[field]
    return true
  }

  function validateAll(): boolean {
    let valid = true
    for (const field of Object.keys(rules)) {
      touched.value[field] = true
      if (!validateField(field)) {
        valid = false
      }
    }
    return valid
  }

  function touch(field: string) {
    touched.value[field] = true
    validateField(field)
  }

  const isValid = computed(() => Object.keys(errors.value).length === 0)

  return {
    errors,
    touched,
    validateField,
    validateAll,
    touch,
    isValid,
  }
}

// Common validation helpers
export const required = (message = 'Câmpul este obligatoriu'): ValidationRule => ({
  validate: (v) => v !== null && v !== undefined && String(v).trim().length > 0,
  message,
})

export const phoneFormat = (message = 'Număr de telefon invalid'): ValidationRule => ({
  validate: (v) => !v || /^(\+?40|0)[0-9]{9}$/.test(String(v).replace(/\s/g, '')),
  message,
})

export const emailFormat = (message = 'Adresă de email invalidă'): ValidationRule => ({
  validate: (v) => !v || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(v)),
  message,
})

export const phoneOrEmail = (phoneField: string, emailField: string, message = 'Completează măcar unul: telefon sau email.'): ValidationRule => ({
  validate: (_v, ) => false, // placeholder — cross-field validation handled in form component
  message,
})

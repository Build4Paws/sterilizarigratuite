<template>
  <span class="form-divider">
    <slot />
  </span>
</template>

<style scoped>
.form-divider {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  flex: 0 0 auto;
  padding-bottom: 0.75rem;
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  user-select: none;
}
</style>

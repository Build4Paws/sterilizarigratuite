<template>
  <Teleport to="body">
    <div class="ui-toaster" role="region" aria-label="Notificări" aria-live="polite">
      <TransitionGroup name="toast">
        <div
          v-for="t in toasts"
          :key="t.id"
          :class="['ui-toast', `ui-toast--${t.variant}`]"
          role="status"
        >
          <component :is="iconFor(t.variant)" class="ui-toast__icon" :size="20" />
          <p class="ui-toast__message">{{ t.message }}</p>
          <button
            type="button"
            class="ui-toast__close"
            aria-label="Închide notificarea"
            @click="dismiss(t.id)"
          >
            <X :size="16" />
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { CircleCheck, CircleAlert, Info, X } from 'lucide-vue-next'
import type { ToastVariant } from '~/composables/useToast'

const { toasts, dismiss } = useToast()

function iconFor(variant: ToastVariant) {
  switch (variant) {
    case 'success': return CircleCheck
    case 'error': return CircleAlert
    default: return Info
  }
}
</script>

<style scoped>
.ui-toaster {
  position: fixed;
  top: var(--space-md);
  right: var(--space-md);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  max-width: min(420px, calc(100vw - var(--space-md) * 2));
  pointer-events: none;
}

.ui-toast {
  pointer-events: auto;
  display: flex;
  align-items: flex-start;
  gap: var(--space-sm);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  background: #fff;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.05);
  border-left: 4px solid transparent;
  font-size: var(--font-size-sm);
}

.ui-toast__icon { flex-shrink: 0; margin-top: 1px; }
.ui-toast__message { margin: 0; flex: 1; line-height: 1.4; }

.ui-toast__close {
  flex-shrink: 0;
  background: transparent;
  border: 0;
  cursor: pointer;
  color: currentColor;
  opacity: 0.6;
  padding: 2px;
  border-radius: var(--radius-sm, 4px);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.ui-toast__close:hover { opacity: 1; }

.ui-toast--success { border-left-color: #10b981; color: #065f46; }
.ui-toast--success .ui-toast__icon { color: #10b981; }

.ui-toast--error { border-left-color: #ef4444; color: #991b1b; }
.ui-toast--error .ui-toast__icon { color: #ef4444; }

.ui-toast--info { border-left-color: var(--color-primary); color: var(--color-primary); }
.ui-toast--info .ui-toast__icon { color: var(--color-primary); }

.toast-enter-active, .toast-leave-active {
  transition: transform 0.25s ease, opacity 0.25s ease;
}
.toast-enter-from { transform: translateX(20px); opacity: 0; }
.toast-leave-to { transform: translateX(20px); opacity: 0; }
.toast-leave-active { position: absolute; right: 0; }
</style>

<template>
  <span :class="['badge', `badge--${tone}`]">{{ label }}</span>
</template>

<script setup lang="ts">
/** Colored pill for campaign + citizen statuses (DB lowercase values). */
const props = defineProps<{ status: string }>()

const MAP: Record<string, { label: string; tone: string }> = {
  // campaign_status
  pending: { label: 'În așteptare', tone: 'warn' },
  approved: { label: 'Aprobată', tone: 'ok' },
  rejected: { label: 'Respinsă', tone: 'danger' },
  cancelled: { label: 'Anulată', tone: 'muted' },
  finished: { label: 'Finalizată', tone: 'muted' },
  // citizen_status
  pending_confirm: { label: 'Neconfirmat', tone: 'warn' },
  active: { label: 'Activ', tone: 'ok' },
  unsubscribed: { label: 'Dezabonat', tone: 'muted' },
  deleted: { label: 'Șters (GDPR)', tone: 'danger' },
}

const label = computed(() => MAP[props.status]?.label ?? props.status)
const tone = computed(() => MAP[props.status]?.tone ?? 'muted')
</script>

<style scoped>
.badge {
  display: inline-block;
  padding: 0.125rem 0.5rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}
.badge--ok { background: #ecfdf5; color: #065f46; }
.badge--warn { background: #fffbeb; color: #92400e; }
.badge--danger { background: #fef2f2; color: #991b1b; }
.badge--muted { background: var(--color-slate-50); color: var(--color-slate-500, #64748b); }
</style>

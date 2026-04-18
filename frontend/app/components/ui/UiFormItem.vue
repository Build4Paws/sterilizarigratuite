<template>
  <div class="form-item" :style="itemStyle">
    <slot />
  </div>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  grow?: boolean
  basis?: string
  shrink?: boolean
  fixed?: boolean
}>(), {
  grow: true,
  shrink: true,
  fixed: false,
})

const itemStyle = computed(() => {
  if (props.fixed) {
    return { flex: '0 0 auto' }
  }
  const g = props.grow ? 1 : 0
  const s = props.shrink ? 1 : 0
  const b = props.basis ?? '0'
  return { flex: `${g} ${s} ${b}` }
})
</script>

<style scoped>
.form-item {
  min-width: 0;
}
</style>

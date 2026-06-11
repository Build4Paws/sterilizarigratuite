<template>
  <component
    :is="icon"
    :size="size"
    :stroke-width="2.25"
    :aria-hidden="true"
    class="species-icon"
    :class="`species-icon--${species}`"
    :style="colored ? { color: tint } : undefined"
  />
</template>

<script setup lang="ts">
import { Dog, Cat } from 'lucide-vue-next'
import type { Species } from '~/types'

/**
 * Single source of truth for the câine / pisică icons. Used everywhere a
 * species is shown (campaign card, map side panel, filters). Change the icon
 * or color mapping HERE and it propagates across the whole app.
 *
 * Color convention (matches the campaign card): dog = accent orange,
 * cat = primary navy. The distinct colors keep the two readable even at the
 * tiny sizes used in the map filters. Pass `:colored="false"` to inherit the
 * surrounding text color instead.
 */
const props = withDefaults(
  defineProps<{ species: Species; size?: number; colored?: boolean }>(),
  { size: 18, colored: true },
)

const icon = computed(() => (props.species === 'dog' ? Dog : Cat))
const tint = computed(() =>
  props.species === 'dog' ? 'var(--color-accent)' : 'var(--color-primary)',
)
</script>

<style scoped>
.species-icon {
  flex-shrink: 0;
}
</style>

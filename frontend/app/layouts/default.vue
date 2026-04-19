<template>
  <div class="app-layout">
    <LayoutTopNav />
    <main>
      <slot />
    </main>
    <LayoutFooter />
    <UiToaster />
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

main {
  flex: 1;
}
</style>

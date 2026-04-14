<template>
  <footer class="footer">
    <div class="container footer__inner">
      <p class="footer__brand">
        Sterilizări Gratuite &mdash; un proiect
        <a href="https://build4paws.ro" target="_blank" rel="noopener">Build4Paws</a>
      </p>
      <nav class="footer__links" aria-label="Linkuri footer">
        <NuxtLink to="/campanii">Campanii</NuxtLink>
        <NuxtLink to="/organizatori">Organizatori</NuxtLink>
        <NuxtLink to="/confidentialitate">Politica de confidențialitate</NuxtLink>
      </nav>
    </div>
  </footer>
</template>

<style scoped>
.footer {
  border-top: 1px solid var(--color-border);
  background: var(--color-bg-muted);
  padding: var(--space-xl) 0;
  margin-top: var(--space-2xl);
}

.footer__inner {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-md);
}

.footer__brand {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.footer__links {
  display: flex;
  gap: var(--space-lg);
}

.footer__links a {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.footer__links a:hover {
  color: var(--color-primary);
}

@media (max-width: 768px) {
  .footer__inner {
    flex-direction: column;
    text-align: center;
  }
}
</style>

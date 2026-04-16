<template>
  <footer class="footer">
    <div class="container footer__inner">
      <div class="footer__brand">
        <p class="footer__name">
          sterilizări<strong>gratuite</strong>
        </p>
        <p class="footer__tagline">
          Un proiect <a href="https://build4paws.ro" target="_blank" rel="noopener">Build4Paws</a>
        </p>
      </div>
      <nav class="footer__links" aria-label="Linkuri footer">
        <NuxtLink to="/campanii">Campanii</NuxtLink>
        <NuxtLink to="/organizatori">Organizatori</NuxtLink>
        <NuxtLink to="/despre">Despre noi</NuxtLink>
        <NuxtLink to="/confidentialitate">Confidențialitate</NuxtLink>
      </nav>
    </div>
  </footer>
</template>

<style scoped>
.footer {
  background: var(--color-primary);
  color: var(--color-text-light);
  padding: var(--space-2xl) 0;
}

.footer__inner {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-lg);
}

.footer__name {
  font-family: var(--font-heading);
  font-size: 1.125rem;
  letter-spacing: -0.01em;
}

.footer__name strong {
  color: var(--color-accent);
}

.footer__tagline {
  font-size: var(--font-size-sm);
  color: var(--color-slate-300);
  margin-top: var(--space-xs);
}

.footer__tagline a {
  color: var(--color-accent);
}

.footer__links {
  display: flex;
  gap: var(--space-lg);
}

.footer__links a {
  color: var(--color-slate-300);
  font-size: var(--font-size-sm);
  text-decoration: none;
  transition: color 0.2s;
}

.footer__links a:hover {
  color: var(--color-text-light);
  text-decoration: none;
}

@media (max-width: 768px) {
  .footer__inner {
    flex-direction: column;
    text-align: center;
  }

  .footer__links {
    flex-wrap: wrap;
    justify-content: center;
  }
}
</style>

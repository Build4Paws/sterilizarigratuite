<template>
  <footer class="footer">
    <div class="container footer__body">

      <div class="footer__brand">
        <a :href="siteUrl" class="footer__logo-link" aria-label="Sterilizări Gratuite, acasă">
          <img
            src="~/assets/images/logo-horizontal.svg"
            alt="Sterilizări Gratuite"
            class="footer__logo"
            width="200"
            height="28"
          />
        </a>
        <p class="footer__tagline">
          Platformă digitală pentru campanii de sterilizare gratuită a animalelor de companie din România.
          <br />Un proiect <a href="https://build4paws.ro" target="_blank" rel="noopener">Build4Paws</a>.
        </p>
        <p class="footer__donate">
          Dacă vrei să ne susții inițiativele,
          <NuxtLink to="/sustine" class="footer__donate-link block">donează aici</NuxtLink>.
        </p>
      </div>

      <div class="footer__cols">
        <div class="footer__col">
          <p class="footer__col-title">Navigare</p>
          <nav class="footer__col-links" aria-label="Navigare site">
            <NuxtLink to="/campanii">Campanii</NuxtLink>
            <NuxtLink to="/ghid-sterilizare">Ghid sterilizare</NuxtLink>
            <NuxtLink to="/organizatori">Organizatori</NuxtLink>
            <NuxtLink to="/harta">Harta</NuxtLink>
            <NuxtLink to="/sustine">Susține-ne</NuxtLink>
          </nav>
        </div>

        <div class="footer__col">
          <p class="footer__col-title">Contact</p>
          <div class="footer__col-links">
            <a href="mailto:contact@build4paws.ro">contact@build4paws.ro</a>
            <a href="https://build4paws.ro" target="_blank" rel="noopener">build4paws.ro</a>
          </div>
        </div>
      </div>

    </div>

    <div class="footer__bottom">
      <div class="container footer__bottom-inner">
        <p>© {{ currentYear }} Asociația Build 4 Paws<br/>OG 26/2000 · Încheiere nr. 217/2026 · Judecătoria Alba Iulia</p>
        <nav aria-label="Linkuri legale">
          <NuxtLink to="/politica-de-confidentialitate">Politică de confidențialitate</NuxtLink>
        </nav>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
// Site URL is environment-driven (nuxt.config `site.url` ← NUXT_PUBLIC_SITE_URL),
// so the footer logo links to prod/dev domain automatically — never hardcoded.
const siteUrl = useSiteConfig().url
const currentYear = new Date().getFullYear()
</script>

<style scoped>
.footer {
  background: var(--color-primary);
  color: var(--color-text-light);
}

/* ── Main body ── */
.footer__body {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: var(--space-2xl);
  padding-top: var(--space-2xl);
  padding-bottom: var(--space-2xl);
}

/* ── Brand ── */
.footer__brand {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  max-width: 340px;
}

.footer__logo-link {
  display: inline-flex;
}

.footer__logo {
  height: 28px;
  width: auto;
  filter: brightness(0) invert(1);
}

.footer__tagline {
  font-size: var(--font-size-sm);
  color: var(--color-slate-300);
  line-height: 1.6;
}

.footer__tagline a {
  color: var(--color-accent);
  text-decoration: none;
}

.footer__tagline a:hover {
  text-decoration: underline;
}

/* ── Donation note ── */
.footer__donate {
  font-size: var(--font-size-sm);
  color: var(--color-slate-300);
  line-height: 1.6;
}

.footer__donate-link {
  color: var(--color-accent);
  font-weight: 700;
  text-decoration: none;
  transition: color 0.2s;
}

.footer__donate-link:hover {
  color: var(--color-accent-hover);
  text-decoration: underline;
}

/* ── Columns ── */
.footer__cols {
  display: flex;
  gap: var(--space-2xl);
}

.footer__col {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.footer__col-title {
  font-family: var(--font-heading);
  font-size: var(--font-size-sm);
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--color-text-light);
}

.footer__col-links {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.footer__col-links a {
  font-size: var(--font-size-sm);
  color: var(--color-slate-300);
  text-decoration: none;
  transition: color 0.2s;
}

.footer__col-links a:hover {
  color: var(--color-text-light);
  text-decoration: none;
}

/* ── Legal bottom strip ── */
.footer__bottom {
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.footer__bottom-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
  padding-top: var(--space-lg);
  padding-bottom: var(--space-lg);
}

.footer__bottom p,
.footer__bottom a {
  font-size: var(--font-size-sm);
  color: var(--color-slate-300);
  text-decoration: none;
}

.footer__bottom a:hover {
  color: var(--color-text-light);
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .footer__body {
    flex-direction: column;
    gap: var(--space-xl);
  }

  .footer__brand {
    max-width: 100%;
  }

  .footer__bottom-inner {
    flex-direction: column;
    text-align: center;
    gap: var(--space-sm);
  }
}

@media (max-width: 480px) {
  .footer__cols {
    flex-direction: column;
    gap: var(--space-xl);
  }
}
</style>

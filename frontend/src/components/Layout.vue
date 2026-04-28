<template>
  <div class="page-shell">
    <header class="site-header container">
      <router-link to="/" class="logo-inline">
        <img src="/brand/svg/icon-mark.svg" alt="ESS Icon" class="logo-crosshair" />
        <div class="logo-wordmark">
          <span class="logo-wordmark__ess">ESS</span>
          <span class="logo-wordmark__sub">TARGET FINDER</span>
        </div>
      </router-link>

      <nav class="site-header__nav">
        <span class="badge badge--live"><span class="badge__dot"></span>ESI LIVE</span>
        <router-link class="site-header__nav-link" to="/">Global</router-link>
        <router-link class="site-header__nav-link" to="/nearby">Nearby</router-link>
        <router-link class="site-header__nav-link" to="/saved">Saved</router-link>
      </nav>
    </header>

    <main class="container">
      <slot />
    </main>
  </div>
</template>

<script setup>
</script>

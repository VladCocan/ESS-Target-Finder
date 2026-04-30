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
        <router-link v-if="authStore.character" class="site-header__nav-link" to="/nearby">Nearby</router-link>
        <router-link v-if="authStore.character" class="site-header__nav-link" to="/saved">Saved</router-link>
      </nav>

      <div class="site-header__actions">
        <span v-if="authStore.character" class="site-header__user">{{ displayName }}</span>
        <router-link
          v-if="authStore.character"
          :to="{ name: 'CharacterProfile' }"
          class="btn btn--outline"
        >
          My Character
        </router-link>
        <button
          v-if="authStore.character"
          class="btn btn--outline"
          type="button"
          @click="logout"
          :disabled="authStore.loading"
        >
          Logout
        </button>
        <button
          v-else
          class="btn btn--primary"
          type="button"
          @click="login"
          :disabled="authStore.loading"
        >
          Login
        </button>
      </div>
    </header>

    <main class="container">
      <slot />
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/authStore.js'

const router = useRouter()
const authStore = useAuthStore()

const displayName = computed(() => {
  if (!authStore.character) return ''
  return (
    authStore.character.character_name ||
    authStore.character.name ||
    authStore.character.CharacterName ||
    String(authStore.character.character_id || authStore.character.CharacterID || 'Authenticated')
  )
})

const login = () => {
  const returnPath = window.location.pathname + window.location.search
  window.location.href = '/api/auth/login?next=' + encodeURIComponent(returnPath)
}

const logout = async () => {
  await authStore.logout()
}

onMounted(() => {
  authStore.fetchMe()
})
</script>

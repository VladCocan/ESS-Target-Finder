<template>
  <section class="auth-panel">
    <div class="auth-panel__status">
      <span v-if="authStore.character">Logged in as {{ authStore.character.name }}</span>
      <a v-else class="btn btn--outline" href="/api/auth/login">Login with EVE</a>
    </div>

    <div class="auth-panel__actions">
      <button
        v-if="authStore.character"
        type="button"
        class="btn btn--outline"
        :disabled="authStore.loading"
        @click="handleUseLocation"
      >
        Use current location
      </button>
      <button
        v-if="authStore.character"
        type="button"
        class="btn btn--primary"
        :disabled="authStore.loading"
        @click="handleLogout"
      >
        Logout
      </button>
    </div>
  </section>
</template>

<script setup>
import { useAuthStore } from '../stores/authStore.js'

const emit = defineEmits(['use-current-location'])
const authStore = useAuthStore()

const handleUseLocation = async () => {
  const location = await authStore.fetchLocation()
  if (location?.system_name) {
    emit('use-current-location', location.system_name)
  }
}

const handleLogout = async () => {
  await authStore.logout()
}
</script>

<template>
  <section class="auth-panel">
    <div class="auth-panel__status">
      <span v-if="authStore.character">Logged in as {{ displayName }}</span>
      <span v-else>Login in the header to use current location.</span>
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
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { useAuthStore } from '../stores/authStore.js'

const emit = defineEmits(['use-current-location'])
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

const handleUseLocation = async () => {
  const location = await authStore.fetchLocation()
  const systemName =
    location?.system_name || location?.name || location?.solar_system_name || location?.systemName
  if (systemName) {
    emit('use-current-location', systemName)
  }
}

</script>

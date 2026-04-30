<template>
  <section>
    <div class="page-header page-header--stacked">
      <div>
        <p class="hero__eyebrow">NEARBY TARGETS</p>
        <h1 class="hero__title">Scan from your current system or a manual entry</h1>
      </div>
      <AuthPanel @use-current-location="handleLocationUpdate" />
    </div>

    <TargetFilters
      :fromSystem="fromSystem"
      :maxDistance="maxDistance"
      :loading="store.loading"
      @update:fromSystem="(value) => fromSystem = value"
      @update:maxDistance="(value) => maxDistance = value"
      @search="fetchNearby"
    />

    <div class="results-panel">
      <div class="results-header">
        <div class="results-count">SHOWING <strong>{{ store.nearbyTargets.length }}</strong> TARGETS</div>
        <span class="badge badge--live"><span class="badge__dot"></span>LIVE</span>
      </div>

      <section class="status">{{ statusMessage }}</section>

      <TargetTable
        :targets="store.nearbyTargets"
        showDistance
        @select-target="openTarget"
      />

      <TargetModal :target="selectedTarget" :open="!!selectedTarget" @close="selectedTarget = null" />
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/authStore.js'
import { useTargetsStore } from '../stores/targetsStore.js'
import AuthPanel from '../components/AuthPanel.vue'
import TargetFilters from '../components/TargetFilters.vue'
import TargetTable from '../components/TargetTable.vue'
import TargetModal from '../components/TargetModal.vue'

const router = useRouter()
const authStore = useAuthStore()
const store = useTargetsStore()
const fromSystem = ref('')
const maxDistance = ref(300)
const selectedTarget = ref(null)
const refreshTimer = ref(null)
const hasSearched = ref(false)

const fetchNearby = async () => {
  if (!fromSystem.value.trim()) {
    store.error = 'Please enter a origin system.'
    return
  }

  await store.fetchNearbyTargets({
    fromSystem: fromSystem.value.trim(),
    maxDistance: maxDistance.value,
  })
  hasSearched.value = true

  if (!refreshTimer.value) {
    refreshTimer.value = setInterval(fetchNearby, 30000)
  }
}

const handleLocationUpdate = (systemName) => {
  fromSystem.value = systemName
  fetchNearby()
}

const openTarget = (target) => {
  selectedTarget.value = target
}

const statusMessage = computed(() => {
  if (store.loading) return 'Loading nearby targets…'
  if (store.error) return `Failed to load targets: ${store.error}`
  if (!hasSearched.value) return authStore.character ? 'Use current location or enter a system to begin.' : 'Login to use current location and scan nearby systems.'
  if (!store.nearbyTargets.length) return 'No nearby targets matched your search.'
  return `Updated ${new Date(store.lastUpdated).toLocaleTimeString()}`
})

onMounted(async () => {
  await authStore.fetchMe()
  if (authStore.character) {
    const location = await authStore.fetchLocation()
    if (location?.system_name && !fromSystem.value) {
      fromSystem.value = location.system_name
      await fetchNearby()
    }
  }
})

onBeforeUnmount(() => {
  clearInterval(refreshTimer.value)
})
</script>

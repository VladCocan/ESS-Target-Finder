<template>
  <section>
    <div class="page-header">
      <div>
        <p class="hero__eyebrow">GLOBAL TARGETS</p>
        <h1 class="hero__title">Top systems across null-sec</h1>
      </div>
      <button class="btn btn--outline" type="button" @click="toggleSort">
        Sort by score {{ store.sortDescending ? '▲' : '▼' }}
      </button>
    </div>

    <div class="results-panel">
      <div class="results-header">
        <div class="results-count">SHOWING <strong>{{ store.globalTargets.length }}</strong> TARGETS</div>
        <span class="badge badge--live"><span class="badge__dot"></span>LIVE</span>
      </div>

      <section class="status">{{ statusMessage }}</section>

      <TargetTable
        :targets="store.globalTargets"
        showDistance
        @select-target="openTarget"
      />

      <TargetModal :target="selectedTarget" :open="!!selectedTarget" @close="selectedTarget = null" />
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useTargetsStore } from '../stores/targetsStore.js'
import TargetTable from '../components/TargetTable.vue'
import TargetModal from '../components/TargetModal.vue'

const store = useTargetsStore()
const selectedTarget = ref(null)
const refreshTimer = ref(null)

const loadTargets = async () => {
  await store.fetchGlobalTargets()
}

const toggleSort = () => {
  store.toggleSort()
}

const openTarget = (target) => {
  selectedTarget.value = target
}

const statusMessage = computed(() => {
  if (store.loading) return 'Loading targets…'
  if (store.error) return `Failed to load targets: ${store.error}`
  if (!store.globalTargets.length) return 'No targets available.'
  return `Updated ${new Date(store.lastUpdated).toLocaleTimeString()}`
})

onMounted(() => {
  loadTargets()
  refreshTimer.value = setInterval(loadTargets, 30000)
})

onBeforeUnmount(() => {
  clearInterval(refreshTimer.value)
})
</script>

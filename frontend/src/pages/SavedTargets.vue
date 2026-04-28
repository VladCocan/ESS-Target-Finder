<template>
  <section>
    <div class="page-header">
      <div>
        <p class="hero__eyebrow">SAVED TARGETS</p>
        <h1 class="hero__title">Your bookmarked systems</h1>
      </div>
      <button class="btn btn--outline" type="button" @click="clearAll" :disabled="!store.savedTargets.length">
        Clear all
      </button>
    </div>

    <div class="results-panel">
      <div class="results-header">
        <div class="results-count">SAVED <strong>{{ store.savedTargets.length }}</strong> TARGETS</div>
        <span class="badge badge--live"><span class="badge__dot"></span>LOCAL</span>
      </div>

      <section class="status">{{ statusMessage }}</section>

      <TargetTable
        :targets="store.savedTargets"
        showDistance
        allowRemove
        @select-target="openTarget"
        @remove-target="removeTarget"
      />

      <TargetModal :target="selectedTarget" :open="!!selectedTarget" @close="selectedTarget = null" />
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useSavedTargetsStore } from '../stores/savedTargetsStore.js'
import TargetTable from '../components/TargetTable.vue'
import TargetModal from '../components/TargetModal.vue'

const store = useSavedTargetsStore()
const selectedTarget = ref(null)

const openTarget = (target) => {
  selectedTarget.value = target
}

const removeTarget = (systemId) => {
  store.removeTarget(systemId)
  if (selectedTarget.value?.system_id === systemId) {
    selectedTarget.value = null
  }
}

const clearAll = () => {
  store.clearAll()
  selectedTarget.value = null
}

const statusMessage = computed(() => {
  if (!store.savedTargets.length) return 'No saved targets yet. Use the Global or Nearby views to bookmark systems.'
  return 'Review your saved systems below.'
})

onMounted(() => {
  store.load()
})
</script>

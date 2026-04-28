<template>
  <section class="hero hero--compact">
    <div class="hero__search hero__search--wide">
      <input
        class="input"
        type="text"
        placeholder="FROM SYSTEM"
        v-model="localFromSystem"
      />
      <input
        class="input"
        type="number"
        min="0"
        placeholder="MAX DISTANCE"
        v-model="localMaxDistance"
      />
      <button class="btn btn--primary" type="button" @click="onSearch" :disabled="loading">
        ▶ SCAN
      </button>
    </div>
  </section>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  fromSystem: String,
  maxDistance: [String, Number],
  loading: Boolean,
})
const emit = defineEmits(['update:fromSystem', 'update:maxDistance', 'search'])

const localFromSystem = ref(props.fromSystem || '')
const localMaxDistance = ref(props.maxDistance ?? '')

watch(
  () => props.fromSystem,
  (value) => {
    localFromSystem.value = value || ''
  }
)

watch(
  () => props.maxDistance,
  (value) => {
    localMaxDistance.value = value ?? ''
  }
)

const onSearch = () => {
  emit('update:fromSystem', localFromSystem.value)
  emit('update:maxDistance', localMaxDistance.value)
  emit('search')
}
</script>

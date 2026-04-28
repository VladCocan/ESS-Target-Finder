<template>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>system_name</th>
          <th>region_name</th>
          <th>constellation_name</th>
          <th v-if="showDistance">distance</th>
          <th>score</th>
          <th>npc_kills</th>
          <th>ship_kills</th>
          <th>pod_kills</th>
          <th>system_jumps</th>
          <th v-if="allowSave || allowRemove">actions</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(target, index) in targets"
          :key="target.system_id || index"
          :class="['table-row', { 'top-target': index < 5 }]"
          @click="selectTarget(target)"
        >
          <td>{{ target.system_name || 'N/A' }}</td>
          <td>{{ target.region_name || 'N/A' }}</td>
          <td>{{ target.constellation_name || 'N/A' }}</td>
          <td v-if="showDistance">{{ target.distance ?? 'N/A' }}</td>
          <td>{{ formatScore(target.score) }}</td>
          <td>{{ target.npc_kills ?? 'N/A' }}</td>
          <td>{{ target.ship_kills ?? 'N/A' }}</td>
          <td>{{ target.pod_kills ?? 'N/A' }}</td>
          <td>{{ target.jumps ?? 'N/A' }}</td>
          <td v-if="allowSave || allowRemove">
            <button
              v-if="allowSave"
              type="button"
              class="btn btn--outline btn--sm"
              @click.stop="saveTarget(target)"
            >
              Save
            </button>
            <button
              v-if="allowRemove"
              type="button"
              class="btn btn--outline btn--sm"
              @click.stop="removeTarget(target.system_id)"
            >
              Remove
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
const props = defineProps({
  targets: {
    type: Array,
    default: () => [],
  },
  showDistance: {
    type: Boolean,
    default: false,
  },
  allowSave: {
    type: Boolean,
    default: false,
  },
  allowRemove: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['select-target', 'save-target', 'remove-target'])

const selectTarget = (target) => {
  emit('select-target', target)
}

const saveTarget = (target) => {
  emit('save-target', target)
}

const removeTarget = (systemId) => {
  emit('remove-target', systemId)
}

const formatScore = (score) => {
  return score != null ? Number(score).toFixed(1) : 'N/A'
}
</script>

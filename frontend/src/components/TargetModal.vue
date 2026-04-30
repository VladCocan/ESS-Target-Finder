<template>
  <div class="modal" v-if="open">
    <div class="modal-backdrop" @click="$emit('close')"></div>
    <div class="modal-panel">
      <button type="button" class="modal-close" @click="$emit('close')">×</button>
      <h2 class="modal-title">Target details</h2>
      <div class="modal-grid">
        <div class="modal-detail">
          <span class="modal-label">system_name</span>
          <span class="modal-value">{{ target.system_name || '—' }}</span>
        </div>
        <div class="modal-detail">
          <span class="modal-label">system_id</span>
          <span class="modal-value">{{ target.system_id ?? '—' }}</span>
        </div>
        <div class="modal-detail">
          <span class="modal-label">region_name</span>
          <span class="modal-value">{{ target.region_name || '—' }}</span>
        </div>
        <div class="modal-detail">
          <span class="modal-label">constellation_name</span>
          <span class="modal-value">{{ target.constellation_name || '—' }}</span>
        </div>
        <div class="modal-detail">
          <span class="modal-label">npc_kills</span>
          <span class="modal-value">{{ target.npc_kills ?? '—' }}</span>
        </div>
        <div class="modal-detail">
          <span class="modal-label">ship_kills</span>
          <span class="modal-value">{{ target.ship_kills ?? '—' }}</span>
        </div>
        <div class="modal-detail">
          <span class="modal-label">pod_kills</span>
          <span class="modal-value">{{ target.pod_kills ?? '—' }}</span>
        </div>
        <div class="modal-detail">
          <span class="modal-label">jumps</span>
          <span class="modal-value">{{ target.jumps ?? '—' }}</span>
        </div>
        <div class="modal-detail">
          <span class="modal-label">distance</span>
          <span class="modal-value">{{ formattedDistance }}</span>
        </div>
        <div class="modal-detail">
          <span class="modal-label">score</span>
          <span class="modal-value">{{ formattedScore }}</span>
        </div>
      </div>
      <div class="modal-breakdown">
        <h3>Score explanation</h3>
        <ul class="breakdown-list">
          <li>NPC activity contribution: {{ breakdown.npcContribution.toFixed(1) }}</li>
          <li>Efficiency contribution: {{ breakdown.efficiencyContribution.toFixed(1) }}</li>
          <li>Traffic penalty: {{ breakdown.trafficPenalty.toFixed(1) }}</li>
          <li>PvP danger penalty: {{ breakdown.pvpPenalty.toFixed(1) }}</li>
          <li>{{ distancePenaltyLabel }}</li>
        </ul>
      </div>
      <div class="modal-actions">
        <span class="modal-note">Character profile navigation is not available here.</span>
      </div>
      <div class="modal-status">
        <span class="badge" :class="riskInfo.className"><span class="badge__dot"></span>{{ riskInfo.label }}</span>
        <span class="modal-score">{{ formattedScore }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { getRiskInfo, getScoreBreakdown } from '../lib/scoring.js'

const props = defineProps({
  target: {
    type: Object,
    default: () => ({}),
  },
  open: {
    type: Boolean,
    default: false,
  },
})

const formattedScore = computed(() => {
  return props.target.score != null ? Number(props.target.score).toFixed(1) : '—'
})

const formattedDistance = computed(() => {
  return props.target.distance != null ? props.target.distance : '—'
})

const breakdown = computed(() => getScoreBreakdown(props.target))
const riskInfo = computed(() => getRiskInfo(props.target))
const distancePenaltyLabel = computed(() => {
  return breakdown.value.distance != null
    ? `Distance penalty: ${breakdown.value.distancePenalty.toFixed(1)}`
    : 'Distance penalty: N/A'
})

</script>

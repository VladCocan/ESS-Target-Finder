<template>
  <section>
    <div class="page-header">
      <div>
        <p class="hero__eyebrow">MY CHARACTER</p>
        <h1 class="hero__title">{{ profile?.name || 'Character Profile' }}</h1>
        <p class="hero__subtitle" v-if="profile">
          {{ profile.corporation_name || 'Unknown corporation' }}
          <span v-if="profile.alliance_name">• {{ profile.alliance_name }}</span>
        </p>
      </div>
      <router-link class="btn btn--outline" to="/">Back to targets</router-link>
    </div>

    <section v-if="store.loading" class="status">Loading character profile…</section>
    <section v-else-if="store.error" class="status">Failed to load profile: {{ store.error }}</section>
    <section v-else-if="!profile" class="status">Character profile unavailable.</section>

    <div v-else class="profile-grid">
      <div class="profile-card profile-card--identity">
        <div class="profile-avatar">
          <img v-if="profile.portrait_url" :src="profile.portrait_url" alt="Portrait" />
        </div>
        <h2>Identity</h2>
        <dl>
          <dt>Name</dt>
          <dd>{{ profile.name }}</dd>
          <dt>Character ID</dt>
          <dd>{{ profile.character_id }}</dd>
          <dt>Corporation</dt>
          <dd>{{ profile.corporation_name || 'Unknown' }}</dd>
          <dt>Alliance</dt>
          <dd>{{ profile.alliance_name || 'Unknown' }}</dd>
          <dt>Birthday</dt>
          <dd>{{ profile.birthday || 'Unknown' }}</dd>
          <dt>Security status</dt>
          <dd>{{ formatSecurity(profile.security_status) }}</dd>
        </dl>
      </div>

      <div class="profile-card profile-card--wallet">
        <h2>Wallet / Economy</h2>
        <dl>
          <dt>ISK balance</dt>
          <dd>{{ formatCurrency(profile.isk_balance) }}</dd>
          <dt>PLEX balance</dt>
          <dd>
            <template v-if="profile.plex_error">
              <div>{{ profile.plex_error }}</div>
              <button type="button" class="btn btn--outline btn--sm" @click="relogin">
                Re-authorize character
              </button>
            </template>
            <template v-else-if="assetScopeMissing">
              <div>Missing ESI scope: esi-assets.read_assets.v1 — re-login required</div>
              <button type="button" class="btn btn--outline btn--sm" @click="relogin">
                Re-authorize character
              </button>
            </template>
            <template v-else-if="profile.plex_balance != null">
              {{ profile.plex_balance }} PLEX
              <span v-if="profile.plex_source" class="status">({{ profile.plex_source }})</span>
            </template>
            <template v-else>
              Unavailable
            </template>
          </dd>
        </dl>
        <div v-if="profile.wallet_journal?.length">
          <h3>Recent wallet journal</h3>
          <ul class="small-list">
            <li v-for="entry in profile.wallet_journal.slice(0, 5)" :key="entry.date + entry.ref_type">
              {{ entry.date }} — {{ formatCurrency(entry.amount) }} — {{ entry.reason || entry.ref_type || 'N/A' }}
            </li>
          </ul>
        </div>
        <div v-if="profile.wallet_transactions?.length">
          <h3>Recent wallet transactions</h3>
          <ul class="small-list">
            <li v-for="tx in profile.wallet_transactions.slice(0, 5)" :key="tx.journal_ref_id || tx.date">
              {{ tx.date }} — {{ formatCurrency(tx.amount) }} — {{ tx.type_name || tx.type_id || 'Unknown' }}
            </li>
          </ul>
        </div>
      </div>

      <div class="profile-card profile-card--skills" v-if="profile.skills || profile.skill_queue">
        <div class="profile-card__actions">
          <button type="button" class="btn btn--outline" @click="skillModalOpen = true">
            View all skills
          </button>
        </div>
        <h2>Skills</h2>
        <dl>
          <dt>Total skill points</dt>
          <dd>{{ profile.total_skill_points != null ? profile.total_skill_points : 'Unavailable' }}</dd>
          <dt>Unallocated skill points</dt>
          <dd>{{ profile.unallocated_skill_points != null ? profile.unallocated_skill_points : 'Unavailable' }}</dd>
        </dl>
        <div v-if="profile.skills?.length">
          <h3>Top skills</h3>
          <ul class="small-list">
            <li v-for="skill in profile.skills.slice(0, 6)" :key="skill.type_id">
              {{ skill.type_name || skill.type_id }} — level {{ skill.level }} — {{ skill.skillpoints }} SP
            </li>
          </ul>
        </div>
        <div v-if="profile.skill_queue?.length">
          <h3>Skill queue</h3>
          <ul class="small-list">
            <li v-for="item in profile.skill_queue.slice(0, 5)" :key="item.type_id + item.queue_position">
              {{ item.type_name || ("Unknown Skill (ID: " + item.type_id + ")") }}
              <template v-if="item.finished_level != null"> — level {{ item.finished_level }}</template>
              — finishes {{ item.finish_date || 'Unavailable' }}
            </li>
          </ul>
        </div>
        <p v-if="!profile.skills && !profile.skill_queue" class="status">Skills data unavailable or missing scope.</p>
      </div>

      <div class="modal" v-if="skillModalOpen">
        <div class="modal-backdrop" @click="skillModalOpen = false"></div>
        <div class="modal-panel">
          <button type="button" class="modal-close" @click="skillModalOpen = false">×</button>
          <h2 class="modal-title">Character Skills</h2>
          <div class="modal-actions">
            <button type="button" class="btn btn--outline" @click="copySkills" :disabled="copying">
              {{ copying ? 'Copying...' : 'Copy to clipboard' }}
            </button>
            <span class="status" v-if="copyStatus">{{ copyStatus }}</span>
          </div>
          <div class="modal-breakdown">
            <div class="modal-detail" v-for="section in categorizedSkills" :key="section.category">
              <h3>{{ section.category }}</h3>
              <ul class="small-list">
                <li v-for="skill in section.skills" :key="skill.type_id || skill.skill_id || skill.skill_name">
                  {{ skill.skill_name || skill.type_name || skill.type_id || 'Unknown Skill' }} — level {{ skill.level ?? skill.trained_skill_level ?? 0 }} — {{ skill.skillpoints ?? 0 }} SP
                </li>
              </ul>
            </div>
            <p v-if="categorizedSkills.length === 0" class="status">No skill data available.</p>
          </div>
        </div>
      </div>

      <div class="profile-card profile-card--location">
        <h2>Location / Ship</h2>
        <dl>
          <dt>Current location</dt>
          <dd>
            <template v-if="locationDetail">{{ locationDetail }}</template>
            <template v-else-if="locationScopeMissing">Missing ESI scope — re-login required</template>
            <template v-else>Unavailable</template>
          </dd>
          <dt>Current ship</dt>
          <dd>
            <template v-if="shipDetail">
              <button type="button" class="btn btn--outline btn--sm" @click="openShipFitModal">
                {{ shipDetail }}
              </button>
            </template>
            <template v-else-if="shipScopeMissing">Missing ESI scope — re-login required</template>
            <template v-else>Unavailable</template>
          </dd>
          <dt>Online status</dt>
          <dd>
            <template v-if="onlineStatusText">{{ onlineStatusText }}</template>
            <template v-else-if="onlineScopeMissing">Missing ESI scope — re-login required</template>
            <template v-else>Unknown</template>
          </dd>
          <template v-if="profile.online_last_login">
            <dt>Last login</dt>
            <dd>{{ profile.online_last_login }}</dd>
          </template>
          <template v-if="profile.online_last_logout">
            <dt>Last logout</dt>
            <dd>{{ profile.online_last_logout }}</dd>
          </template>
          <template v-if="profile.online_logins != null">
            <dt>Logins</dt>
            <dd>{{ profile.online_logins }}</dd>
          </template>
        </dl>
      </div>

      <div class="modal" v-if="shipFitOpen">
        <div class="modal-backdrop" @click="closeShipFitModal"></div>
        <div class="modal-panel">
          <button type="button" class="modal-close" @click="closeShipFitModal">×</button>
          <h2 class="modal-title">Current Ship Fit & Cargo</h2>
          <div class="modal-actions">
            <button type="button" class="btn btn--outline" @click="copyShipFit" :disabled="copying || store.shipFitLoading">
              {{ copying ? 'Copying...' : 'Copy to clipboard' }}
            </button>
          </div>
          <div class="modal-breakdown">
            <div v-if="store.shipFitLoading" class="status">Loading current ship fit…</div>
            <div v-else-if="store.shipFitError" class="status">{{ store.shipFitError }}</div>
            <div v-else-if="store.shipFit">
              <div class="modal-detail modal-detail--ship-image">
                <img
                  v-if="shipImageUrl"
                  :src="shipImageUrl"
                  :alt="store.shipFit.ship.type_name || 'Ship portrait'"
                  class="ship-portrait"
                />
                <div>
                  <div class="modal-label">Ship name</div>
                  <div class="modal-value">{{ store.shipFit.ship.name || 'Unknown' }}</div>
                  <div class="modal-label">Ship type</div>
                  <div class="modal-value">{{ store.shipFit.ship.type_name || store.shipFit.ship.type_id || 'Unknown' }}</div>
                </div>
              </div>
              <div class="modal-detail">
                <h3>High slots</h3>
                <ul class="small-list">
                  <li v-for="item in store.shipFit.fit.high_slots" :key="item.type_id + item.location_flag">
                    {{ item.type_name || item.type_id }} — x{{ item.quantity || 0 }} — {{ item.location_flag || 'Unknown' }}
                  </li>
                  <li v-if="store.shipFit.fit.high_slots.length === 0">None</li>
                </ul>
              </div>
              <div class="modal-detail">
                <h3>Mid slots</h3>
                <ul class="small-list">
                  <li v-for="item in store.shipFit.fit.mid_slots" :key="item.type_id + item.location_flag">
                    {{ item.type_name || item.type_id }} — x{{ item.quantity || 0 }} — {{ item.location_flag || 'Unknown' }}
                  </li>
                  <li v-if="store.shipFit.fit.mid_slots.length === 0">None</li>
                </ul>
              </div>
              <div class="modal-detail">
                <h3>Low slots</h3>
                <ul class="small-list">
                  <li v-for="item in store.shipFit.fit.low_slots" :key="item.type_id + item.location_flag">
                    {{ item.type_name || item.type_id }} — x{{ item.quantity || 0 }} — {{ item.location_flag || 'Unknown' }}
                  </li>
                  <li v-if="store.shipFit.fit.low_slots.length === 0">None</li>
                </ul>
              </div>
              <div class="modal-detail">
                <h3>Rig slots</h3>
                <ul class="small-list">
                  <li v-for="item in store.shipFit.fit.rig_slots" :key="item.type_id + item.location_flag">
                    {{ item.type_name || item.type_id }} — x{{ item.quantity || 0 }} — {{ item.location_flag || 'Unknown' }}
                  </li>
                  <li v-if="store.shipFit.fit.rig_slots.length === 0">None</li>
                </ul>
              </div>
              <div class="modal-detail">
                <h3>Subsystem slots</h3>
                <ul class="small-list">
                  <li v-for="item in store.shipFit.fit.subsystem_slots" :key="item.type_id + item.location_flag">
                    {{ item.type_name || item.type_id }} — x{{ item.quantity || 0 }} — {{ item.location_flag || 'Unknown' }}
                  </li>
                  <li v-if="store.shipFit.fit.subsystem_slots.length === 0">None</li>
                </ul>
              </div>
              <div class="modal-detail">
                <h3>Drones</h3>
                <ul class="small-list">
                  <li v-for="item in store.shipFit.fit.drones" :key="item.type_id + item.location_flag">
                    {{ item.type_name || item.type_id }} — x{{ item.quantity || 0 }} — {{ item.location_flag || 'Unknown' }}
                  </li>
                  <li v-if="store.shipFit.fit.drones.length === 0">None</li>
                </ul>
              </div>
              <div class="modal-detail">
                <h3>Cargo</h3>
                <ul class="small-list">
                  <li v-for="item in store.shipFit.fit.cargo" :key="item.type_id + item.location_flag">
                    {{ item.type_name || item.type_id }} — x{{ item.quantity || 0 }} — {{ item.location_flag || 'Unknown' }}
                  </li>
                  <li v-if="store.shipFit.fit.cargo.length === 0">None</li>
                </ul>
              </div>
              <div class="modal-detail">
                <h3>Other</h3>
                <ul class="small-list">
                  <li v-for="item in store.shipFit.fit.other" :key="item.type_id + item.location_flag">
                    {{ item.type_name || item.type_id }} — x{{ item.quantity || 0 }} — {{ item.location_flag || 'Unknown' }}
                  </li>
                  <li v-if="store.shipFit.fit.other.length === 0">None</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="profile-card profile-card--assets" v-if="profile.assets?.length">
        <h2>Assets</h2>
        <p>{{ profile.assets.length }} asset items loaded.</p>
        <ul class="small-list">
          <li v-for="asset in profile.assets.slice(0, 6)" :key="asset.type_id + asset.location_id">
            {{ asset.type_name || asset.type_id }} — x{{ asset.quantity || 0 }} @ {{ asset.location_name || asset.location_id || 'Unknown' }}
          </li>
        </ul>
      </div>
    </div>

    <section v-if="missingScopeDetected" class="status status--warning">
      <p v-if="profile?.missing_scopes?.length">
        Missing scopes: {{ profile.missing_scopes.join(', ') }}.
      </p>
      <p v-else>
        Missing ESI asset access scope: esi-assets.read_assets.v1.
      </p>
      <p>Please log in again to grant expanded permissions.</p>
      <button type="button" class="btn btn--outline" @click="relogin">
        Re-authorize character
      </button>
    </section>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/authStore.js'
import { useCharacterStore } from '../stores/characterStore.js'

const router = useRouter()
const authStore = useAuthStore()
const store = useCharacterStore()

const profile = computed(() => store.profile)

const locationScopeMissing = computed(() =>
  profile.value?.missing_scopes?.includes('esi-location.read_location.v1') ?? false
)
const shipScopeMissing = computed(() =>
  profile.value?.missing_scopes?.includes('esi-location.read_ship_type.v1') ?? false
)
const onlineScopeMissing = computed(() =>
  profile.value?.missing_scopes?.includes('esi-location.read_online.v1') ?? false
)
const assetScopeMissing = computed(() =>
  profile.value?.missing_scopes?.includes('esi-assets.read_assets.v1') ?? false
)
const missingScopeDetected = computed(() => {
  if (!profile.value) return false
  return (
    assetScopeMissing.value ||
    profile.value?.plex_error?.includes('Missing scope: esi-assets.read_assets.v1')
  )
})

const locationDetail = computed(() => {
  if (!profile.value) return ''
  const parts = []
  if (profile.value.location_name) parts.push(profile.value.location_name)
  if (profile.value.location_station_name) parts.push(profile.value.location_station_name)
  else if (profile.value.location_structure_name) parts.push(profile.value.location_structure_name)
  return parts.join(' • ')
})

const shipDetail = computed(() => {
  if (!profile.value) return ''
  const parts = []
  if (profile.value.ship_type_name) parts.push(profile.value.ship_type_name)
  else if (profile.value.ship_type_id) parts.push(`Type ${profile.value.ship_type_id}`)
  if (profile.value.ship_name) parts.push(profile.value.ship_name)
  return parts.join(' • ')
})

const shipImageUrl = computed(() => {
  const typeId = store.shipFit?.ship?.type_id || profile.value?.ship_type_id
  return typeId ? `https://images.evetech.net/types/${typeId}/portrait?size=256` : ''
})

const onlineStatusText = computed(() => {
  if (!profile.value) return ''
  if (profile.value.online_status === true) return 'Online'
  if (profile.value.online_status === false) return 'Offline'
  return ''
})

const shipFitOpen = ref(false)
const openShipFitModal = async () => {
  shipFitOpen.value = true
  if (!store.shipFit && !store.shipFitLoading) {
    await store.fetchCurrentShipFit()
  }
}
const closeShipFitModal = () => {
  shipFitOpen.value = false
}

const skillModalOpen = ref(false)
const categorizedSkills = computed(() => {
  if (!profile.value?.skills?.length) return []

  const grouped = {}
  for (const skill of profile.value.skills) {
    const category = skill.group_name || (skill.group_id ? `Group ${skill.group_id}` : 'Unknown Category')
    if (!grouped[category]) grouped[category] = []
    grouped[category].push(skill)
  }

  return Object.entries(grouped)
    .map(([category, skills]) => ({
      category,
      skills: skills.slice().sort((a, b) => {
        const nameA = (a.skill_name || a.type_name || '').toString().toLowerCase()
        const nameB = (b.skill_name || b.type_name || '').toString().toLowerCase()
        return nameA.localeCompare(nameB)
      }),
    }))
    .sort((a, b) => a.category.localeCompare(b.category))
})

onMounted(async () => {
  await authStore.fetchMe()
  if (!authStore.character) {
    router.replace('/')
    return
  }

  await store.fetchProfile()
})

const formatSecurity = (value) => {
  return value != null ? Number(value).toFixed(2) : 'Unknown'
}

const formatCurrency = (value) => {
  if (value == null) return 'Unavailable'
  return Number(value).toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
}

const copyStatus = ref('')
const copying = ref(false)

const copySkills = async () => {
  if (!navigator.clipboard) {
    copyStatus.value = 'Clipboard API unavailable.'
    return
  }

  copying.value = true
  copyStatus.value = ''

  try {
    const exportText = await store.copySkillExport()
    if (!exportText) {
      copyStatus.value = 'No skill data available to copy.'
      return
    }
    await navigator.clipboard.writeText(exportText)
    copyStatus.value = 'Copied to clipboard'
  } catch (error) {
    copyStatus.value = error?.message || 'Failed to copy skills'
  } finally {
    copying.value = false
  }
}

const copyShipFit = async () => {
  if (!navigator.clipboard) {
    copyStatus.value = 'Clipboard API unavailable.'
    return
  }

  if (!store.shipFit) {
    copyStatus.value = 'Ship fit is unavailable.'
    return
  }

  copying.value = true
  copyStatus.value = ''

  try {
    await navigator.clipboard.writeText(JSON.stringify(store.shipFit, null, 2))
    copyStatus.value = 'Copied to clipboard'
  } catch (error) {
    copyStatus.value = error?.message || 'Failed to copy ship fit'
  } finally {
    copying.value = false
  }
}

const relogin = () => {
  const returnPath = window.location.pathname + window.location.search
  window.location.href = '/api/auth/login?next=' + encodeURIComponent(returnPath) + '&prompt=consent'
}
</script>

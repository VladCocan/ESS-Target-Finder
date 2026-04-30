import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/authStore.js'
import GlobalTargets from '../pages/GlobalTargets.vue'
import NearbyTargets from '../pages/NearbyTargets.vue'
import SavedTargets from '../pages/SavedTargets.vue'
import CharacterDetail from '../pages/CharacterDetail.vue'

const routes = [
  { path: '/', name: 'GlobalTargets', component: GlobalTargets },
  { path: '/nearby', name: 'NearbyTargets', component: NearbyTargets, meta: { requiresAuth: true } },
  { path: '/saved', name: 'SavedTargets', component: SavedTargets, meta: { requiresAuth: true } },
  { path: '/character', name: 'CharacterProfile', component: CharacterDetail, meta: { requiresAuth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  if (!to.meta.requiresAuth) {
    return true
  }

  const authStore = useAuthStore()
  await authStore.fetchMe()
  if (!authStore.character) {
    return { path: '/' }
  }

  return true
})

export default router

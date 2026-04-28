import { createRouter, createWebHistory } from 'vue-router'
import GlobalTargets from '../pages/GlobalTargets.vue'
import NearbyTargets from '../pages/NearbyTargets.vue'
import SavedTargets from '../pages/SavedTargets.vue'

const routes = [
  { path: '/', name: 'GlobalTargets', component: GlobalTargets },
  { path: '/nearby', name: 'NearbyTargets', component: NearbyTargets },
  { path: '/saved', name: 'SavedTargets', component: SavedTargets },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router

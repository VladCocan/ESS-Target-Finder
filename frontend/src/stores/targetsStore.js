import { defineStore } from 'pinia'
import { getTargets } from '../lib/api.js'

export const useTargetsStore = defineStore('targets', {
  state: () => ({
    globalTargets: [],
    nearbyTargets: [],
    loading: false,
    error: null,
    lastUpdated: null,
    sortDescending: true,
  }),
  actions: {
    async fetchGlobalTargets(params = {}) {
      this.loading = true
      this.error = null
      try {
        const targets = await getTargets(params)
        this.globalTargets = this.sortTargets(targets)
        this.lastUpdated = new Date().toISOString()
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    },
    async fetchNearbyTargets({ fromSystem, maxDistance }) {
      this.loading = true
      this.error = null
      try {
        const targets = await getTargets({
          from_system: fromSystem,
          max_distance: maxDistance,
        })
        this.nearbyTargets = this.sortTargets(targets)
        this.lastUpdated = new Date().toISOString()
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    },
    toggleSort() {
      this.sortDescending = !this.sortDescending
      this.globalTargets = this.sortTargets(this.globalTargets)
      this.nearbyTargets = this.sortTargets(this.nearbyTargets)
    },
    sortTargets(list) {
      return [...list].sort((a, b) => {
        const aScore = Number(a.score ?? 0)
        const bScore = Number(b.score ?? 0)
        return this.sortDescending ? bScore - aScore : aScore - bScore
      })
    },
  },
})

import { defineStore } from 'pinia'

const STORAGE_KEY = 'savedTargets'

export const useSavedTargetsStore = defineStore('savedTargets', {
  state: () => ({
    savedTargets: [],
  }),
  actions: {
    load() {
      const stored = localStorage.getItem(STORAGE_KEY)
      this.savedTargets = stored ? JSON.parse(stored) : []
    },
    persist() {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.savedTargets))
    },
    saveTarget(target) {
      if (!this.savedTargets.some((item) => item.system_id === target.system_id)) {
        this.savedTargets.push(target)
        this.persist()
      }
    },
    removeTarget(systemId) {
      this.savedTargets = this.savedTargets.filter((item) => item.system_id !== systemId)
      this.persist()
    },
    clearAll() {
      this.savedTargets = []
      this.persist()
    },
  },
})

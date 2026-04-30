import { defineStore } from 'pinia'
import { getCharacterProfile, getCurrentShipFit, getSkillExport } from '../lib/api.js'

export const useCharacterStore = defineStore('character', {
  state: () => ({
    profile: null,
    loading: false,
    error: null,
    shipFit: null,
    shipFitLoading: false,
    shipFitError: null,
  }),
  actions: {
    async fetchProfile() {
      this.loading = true
      this.error = null
      this.profile = null
      try {
        this.profile = await getCharacterProfile()
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    },
    async fetchCurrentShipFit() {
      this.shipFitLoading = true
      this.shipFitError = null
      this.shipFit = null
      try {
        this.shipFit = await getCurrentShipFit()
      } catch (error) {
        this.shipFitError = error.message
      } finally {
        this.shipFitLoading = false
      }
    },
    async copySkillExport() {
      try {
        return await getSkillExport()
      } catch (error) {
        throw error
      }
    },
  },
})

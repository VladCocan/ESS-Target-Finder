import { defineStore } from 'pinia'
import { getMe, getLocation, postLogout } from '../lib/api.js'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    character: null,
    loading: false,
    error: null,
    initialized: false,
  }),
  actions: {
    async fetchMe() {
      if (this.initialized) return
      this.loading = true
      this.error = null
      try {
        const result = await getMe()
        this.character = {
          ...result,
          character_name:
            result.character_name || result.name || result.CharacterName || result.characterName || null,
        }
      } catch (error) {
        if (error.message.includes('401')) {
          this.character = null
        } else {
          this.error = error.message
        }
      } finally {
        this.loading = false
        this.initialized = true
      }
    },
    async fetchLocation() {
      this.loading = true
      this.error = null
      try {
        const result = await getLocation()
        return result
      } catch (error) {
        this.error = error.message
        return null
      } finally {
        this.loading = false
      }
    },
    async logout() {
      this.loading = true
      this.error = null
      try {
        await postLogout()
        this.character = null
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    },
  },
})

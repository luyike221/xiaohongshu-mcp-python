import { defineStore } from 'pinia'

export const useAppStore = defineStore('app', {
  state: () => ({
    count: 0,
    theme: 'light'
  }),
  
  actions: {
    increment() {
      this.count++
    },
    
    setTheme(theme: string) {
      this.theme = theme
    }
  }
})

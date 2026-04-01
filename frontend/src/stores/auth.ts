import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const API_BASE = '/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref<{ user_id: string; username: string } | null>(null)

  const isLoggedIn = computed(() => !!token.value)

  async function login(username: string, password: string) {
    const response = await axios.post(`${API_BASE}/auth/login`, { username, password })
    if (response.data.code === 0) {
      token.value = response.data.data.token
      localStorage.setItem('token', token.value)
      axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
      await fetchUser()
      return true
    }
    return false
  }

  async function register(username: string, password: string) {
    const response = await axios.post(`${API_BASE}/auth/register`, { username, password })
    return response.data.code === 0
  }

  async function fetchUser() {
    try {
      const response = await axios.get(`${API_BASE}/auth/me`)
      if (response.data.code === 0) {
        user.value = response.data.data
      }
    } catch (e) {
      logout()
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    delete axios.defaults.headers.common['Authorization']
  }

  // Initialize axios headers
  if (token.value) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
  }

  return { token, user, isLoggedIn, login, register, logout, fetchUser }
})

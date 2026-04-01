<template>
  <div class="login-card card">
    <h2>{{ isRegister ? '注册' : '登录' }}</h2>
    <form @submit.prevent="handleSubmit" class="login-form">
      <div class="form-group">
        <label>用户名</label>
        <input v-model="username" type="text" class="input" required />
      </div>
      <div class="form-group">
        <label>密码</label>
        <input v-model="password" type="password" class="input" required />
      </div>
      <div v-if="error" class="error">{{ error }}</div>
      <button type="submit" class="btn btn-primary w-full" :disabled="loading">
        {{ loading ? '处理中...' : (isRegister ? '注册' : '登录') }}
      </button>
      <div class="toggle-mode">
        <a href="#" @click.prevent="isRegister = !isRegister">
          {{ isRegister ? '已有账号？登录' : '没有账号？注册' }}
        </a>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const router = useRouter()

const username = ref('')
const password = ref('')
const isRegister = ref(false)
const loading = ref(false)
const error = ref('')

async function handleSubmit() {
  loading.value = true
  error.value = ''

  try {
    if (isRegister.value) {
      const success = await authStore.register(username.value, password.value)
      if (success) {
        // Auto login after register
        await authStore.login(username.value, password.value)
        router.push('/chat')
      } else {
        error.value = '注册失败'
      }
    } else {
      const success = await authStore.login(username.value, password.value)
      if (success) {
        router.push('/chat')
      } else {
        error.value = '登录失败，请检查用户名和密码'
      }
    }
  } catch (e: any) {
    error.value = e.message || '请求失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-card {
  width: 100%;
  max-width: 400px;
  padding: 2rem;
}

.login-card h2 {
  text-align: center;
  margin-bottom: 1.5rem;
  color: var(--primary-color);
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 500;
  color: var(--text-secondary);
}

.error {
  color: var(--error-color);
  font-size: 0.875rem;
  text-align: center;
}

.toggle-mode {
  text-align: center;
  margin-top: 1rem;
}

.toggle-mode a {
  color: var(--primary-color);
  text-decoration: none;
}
</style>

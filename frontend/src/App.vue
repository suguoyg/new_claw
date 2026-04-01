<template>
  <div id="app" class="app-container">
    <div v-if="authStore.isLoggedIn" class="main-layout">
      <aside class="sidebar">
        <div class="sidebar-header">
          <h2>NewClaw</h2>
        </div>
        <nav class="sidebar-nav">
          <router-link to="/chat" class="nav-item">
            <span class="nav-icon">💬</span>
            <span>对话</span>
          </router-link>
          <router-link to="/agents" class="nav-item">
            <span class="nav-icon">🤖</span>
            <span>Agent</span>
          </router-link>
          <router-link to="/tools" class="nav-item">
            <span class="nav-icon">🔧</span>
            <span>工具</span>
          </router-link>
          <router-link to="/skills" class="nav-item">
            <span class="nav-icon">✨</span>
            <span>技能</span>
          </router-link>
          <router-link to="/models" class="nav-item">
            <span class="nav-icon">⚙️</span>
            <span>模型</span>
          </router-link>
          <router-link to="/memory" class="nav-item">
            <span class="nav-icon">🧠</span>
            <span>记忆</span>
          </router-link>
        </nav>
        <div class="sidebar-footer">
          <button @click="authStore.logout" class="btn btn-secondary w-full">
            退出登录
          </button>
        </div>
      </aside>
      <main class="main-content">
        <router-view />
      </main>
    </div>
    <div v-else class="auth-container">
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from './stores/auth'

const authStore = useAuthStore()
</script>

<style scoped>
.app-container {
  height: 100vh;
  overflow: hidden;
}

.main-layout {
  display: flex;
  height: 100%;
}

.sidebar {
  width: 220px;
  background-color: var(--surface-color);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 1.5rem 1rem;
  border-bottom: 1px solid var(--border-color);
}

.sidebar-header h2 {
  font-size: 1.5rem;
  color: var(--primary-color);
}

.sidebar-nav {
  flex: 1;
  padding: 1rem 0;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  color: var(--text-primary);
  text-decoration: none;
  transition: background-color 0.2s;
}

.nav-item:hover {
  background-color: var(--background-color);
}

.nav-item.router-link-active {
  background-color: #e8f4fc;
  color: var(--primary-color);
}

.nav-icon {
  margin-right: 0.75rem;
  font-size: 1.25rem;
}

.sidebar-footer {
  padding: 1rem;
  border-top: 1px solid var(--border-color);
}

.main-content {
  flex: 1;
  overflow: hidden;
}

.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
</style>

<template>
  <div class="model-view">
    <div class="page-header">
      <h2>模型配置</h2>
      <button @click="showAddModal = true" class="btn btn-primary">添加模型</button>
    </div>

    <div class="models-section">
      <h3>对话模型</h3>
      <div class="models-grid">
        <div v-for="(config, provider) in models.dialog?.providers" :key="provider" class="model-card card">
          <div class="model-header">
            <h4>{{ provider }}</h4>
            <span class="model-status" :class="config.status">{{ config.status }}</span>
          </div>
          <div class="model-info">
            <p><strong>模型:</strong> {{ config.model }}</p>
            <p><strong>API:</strong> {{ config.api_url }}</p>
          </div>
          <div class="model-actions">
            <button @click="testModel(provider, 'dialog')" class="btn btn-secondary">测试</button>
            <button @click="deleteModel(provider, 'dialog')" class="btn btn-danger">删除</button>
          </div>
        </div>
      </div>
    </div>

    <div class="models-section">
      <h3>Embedding 模型</h3>
      <div class="models-grid">
        <div v-for="(config, provider) in models.embedding?.providers" :key="provider" class="model-card card">
          <div class="model-header">
            <h4>{{ provider }}</h4>
            <span class="model-status" :class="config.status">{{ config.status }}</span>
          </div>
          <div class="model-info">
            <p><strong>模型:</strong> {{ config.model }}</p>
            <p><strong>API:</strong> {{ config.api_url }}</p>
          </div>
          <div class="model-actions">
            <button @click="testModel(provider, 'embedding')" class="btn btn-secondary">测试</button>
            <button @click="deleteModel(provider, 'embedding')" class="btn btn-danger">删除</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
      <div class="modal card">
        <h3>添加模型</h3>
        <form @submit.prevent="addModel">
          <div class="form-group">
            <label>模型类型</label>
            <select v-model="modelForm.type" class="input">
              <option value="dialog">对话模型</option>
              <option value="embedding">Embedding 模型</option>
            </select>
          </div>
          <div class="form-group">
            <label>提供商</label>
            <select v-model="modelForm.provider" class="input">
              <option value="ollama">Ollama</option>
              <option value="openai">OpenAI</option>
              <option value="vllm">vLLM</option>
            </select>
          </div>
          <div class="form-group">
            <label>API 地址</label>
            <input v-model="modelForm.api_url" class="input" placeholder="http://localhost:11434" required />
          </div>
          <div class="form-group">
            <label>模型名称</label>
            <input v-model="modelForm.model" class="input" placeholder="llama2" required />
          </div>
          <div class="form-group">
            <label>API Key (可选)</label>
            <input v-model="modelForm.api_key" class="input" type="password" />
          </div>
          <div class="form-group">
            <label>
              <input v-model="modelForm.set_default" type="checkbox" />
              设为默认模型
            </label>
          </div>
          <div class="form-actions">
            <button type="button" @click="showAddModal = false" class="btn btn-secondary">取消</button>
            <button type="submit" class="btn btn-primary">添加</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const models = ref<any>({
  dialog: { default: 'ollama', providers: {} },
  embedding: { default: 'ollama', providers: {} }
})

const showAddModal = ref(false)

const modelForm = ref({
  type: 'dialog',
  provider: 'ollama',
  api_url: 'http://localhost:11434',
  model: 'llama2',
  api_key: '',
  set_default: true
})

onMounted(async () => {
  await fetchModels()
})

async function fetchModels() {
  const response = await axios.get('/api/models')
  if (response.data.code === 0) {
    models.value = response.data.data
  }
}

async function addModel() {
  const endpoint = modelForm.value.type === 'dialog' ? '/dialog' : '/embedding'

  await axios.post(`/api/models${endpoint}`, {
    provider: modelForm.value.provider,
    api_url: modelForm.value.api_url,
    model: modelForm.value.model,
    api_key: modelForm.value.api_key,
    set_default: modelForm.value.set_default
  })

  showAddModal.value = false
  await fetchModels()
}

async function testModel(provider: string, type: string) {
  const config = type === 'dialog'
    ? models.value.dialog?.providers?.[provider]
    : models.value.embedding?.providers?.[provider]

  if (!config) return

  const response = await axios.post('/api/models/test', {
    provider,
    api_url: config.api_url,
    model: config.model
  })

  if (response.data.code === 0) {
    alert(`状态: ${response.data.data.status}, 延迟: ${response.data.data.latency_ms}ms`)
  }
}

async function deleteModel(provider: string, type: string) {
  if (!confirm(`确定删除 ${type} 模型 "${provider}" 吗？`)) return

  const endpoint = type === 'dialog' ? '/dialog' : '/embedding'
  await axios.delete(`/api/models${endpoint}/${provider}`)
  await fetchModels()
}
</script>

<style scoped>
.model-view {
  padding: 1.5rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.models-section {
  margin-bottom: 2rem;
}

.models-section h3 {
  margin-bottom: 1rem;
  color: var(--text-secondary);
}

.models-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}

.model-card {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.model-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.model-status {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.model-status.connected {
  background: #d4edda;
  color: #155724;
}

.model-status.error {
  background: #f8d7da;
  color: #721c24;
}

.model-info {
  flex: 1;
  font-size: 0.875rem;
}

.model-info p {
  margin-bottom: 0.25rem;
}

.model-actions {
  display: flex;
  gap: 0.5rem;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal {
  width: 100%;
  max-width: 400px;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.25rem;
  font-weight: 500;
}

.form-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}
</style>

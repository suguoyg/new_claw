<template>
  <div class="tool-view">
    <div class="page-header">
      <h2>工具管理</h2>
      <button @click="showCreateModal = true" class="btn btn-primary">添加工具</button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="tools-grid">
      <div v-for="tool in tools" :key="tool.name" class="tool-card card">
        <div class="tool-header">
          <h3>{{ tool.name }}</h3>
          <span class="tool-type" :class="tool.type">{{ tool.type }}</span>
        </div>
        <p class="tool-description">{{ tool.description }}</p>
        <div class="tool-modules" v-if="tool.has_references || tool.has_scripts || tool.has_templates">
          <span v-if="tool.has_references" class="module-tag">references</span>
          <span v-if="tool.has_scripts" class="module-tag">scripts</span>
          <span v-if="tool.has_templates" class="module-tag">templates</span>
        </div>
        <div class="tool-actions">
          <button @click="editTool(tool)" class="btn btn-secondary">编辑</button>
          <button v-if="tool.type === 'custom'" @click="deleteTool(tool.name)" class="btn btn-danger">删除</button>
        </div>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showCreateModal || editingTool" class="modal-overlay" @click.self="closeModal">
      <div class="modal card">
        <h3>{{ editingTool ? '编辑工具' : '添加工具' }}</h3>
        <form @submit.prevent="saveTool">
          <div class="form-group">
            <label>名称</label>
            <input v-model="toolForm.name" :disabled="!!editingTool" type="text" required />
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="toolForm.description" rows="3"></textarea>
          </div>
          <div class="form-group">
            <label>类型</label>
            <select v-model="toolForm.type" :disabled="!!editingTool">
              <option value="custom">自定义</option>
              <option value="api">API</option>
              <option value="script">脚本</option>
            </select>
          </div>
          <div class="form-actions">
            <button type="button" @click="closeModal" class="btn btn-secondary">取消</button>
            <button type="submit" class="btn btn-primary">保存</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const tools = ref<any[]>([])
const loading = ref(false)
const error = ref('')
const showCreateModal = ref(false)
const editingTool = ref<any>(null)

const toolForm = ref({
  name: '',
  description: '',
  type: 'custom'
})

const loadTools = async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await axios.get('/api/tools')
    tools.value = res.data.data || []
  } catch (e: any) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

const editTool = (tool: any) => {
  editingTool.value = tool
  toolForm.value = {
    name: tool.name,
    description: tool.description,
    type: tool.type
  }
}

const closeModal = () => {
  showCreateModal.value = false
  editingTool.value = null
  toolForm.value = { name: '', description: '', type: 'custom' }
}

const saveTool = async () => {
  try {
    if (editingTool.value) {
      await axios.put(`/api/tools/${editingTool.value.name}`, {
        description: toolForm.value.description
      })
    } else {
      await axios.post('/api/tools', toolForm.value)
    }
    closeModal()
    loadTools()
  } catch (e: any) {
    error.value = e.message || '保存失败'
  }
}

const deleteTool = async (name: string) => {
  if (!confirm(`确定删除工具 ${name}？`)) return
  try {
    await axios.delete(`/api/tools/${name}`)
    loadTools()
  } catch (e: any) {
    error.value = e.message || '删除失败'
  }
}

onMounted(loadTools)
</script>

<style scoped>
.tool-view {
  padding: 1.5rem;
  height: 100%;
  overflow-y: auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.tool-card {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.tool-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tool-type {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.tool-type.builtin {
  background: #e3f2fd;
  color: #1976d2;
}

.tool-type.custom {
  background: #e8f5e9;
  color: #388e3c;
}

.tool-type.api {
  background: #fff3e0;
  color: #f57c00;
}

.tool-type.script {
  background: #f3e5f5;
  color: #7b1fa2;
}

.tool-description {
  color: var(--text-secondary);
  font-size: 0.875rem;
  flex: 1;
}

.tool-modules {
  display: flex;
  gap: 0.5rem;
}

.module-tag {
  font-size: 11px;
  padding: 2px 6px;
  background: #f5f5f5;
  border-radius: 3px;
  color: #666;
}

.tool-actions {
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
  align-items: flex-start;
  justify-content: center;
  z-index: 1000;
  overflow-y: auto;
  padding: 2rem 0;
}

.modal {
  width: 100%;
  max-width: 500px;
  max-height: none;
  overflow-y: visible;
  margin: auto;
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

.loading, .error {
  text-align: center;
  padding: 2rem;
  color: var(--text-secondary);
}

.error {
  color: #d32f2f;
}
</style>
<template>
  <div class="tools-editor">
    <div class="section-header">
      <h3>工具管理</h3>
      <button @click="showCreateModal = true" class="btn-primary">添加工具</button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="tools-list">
      <div v-for="tool in tools" :key="tool.name" class="tool-item">
        <div class="tool-info">
          <div class="tool-header">
            <span class="tool-name">{{ tool.name }}</span>
            <span class="tool-type" :class="tool.type">{{ tool.type }}</span>
          </div>
          <div class="tool-description">{{ tool.description }}</div>
          <div class="tool-modules" v-if="tool.has_references || tool.has_scripts || tool.has_templates">
            <span v-if="tool.has_references" class="module-tag">references</span>
            <span v-if="tool.has_scripts" class="module-tag">scripts</span>
            <span v-if="tool.has_templates" class="module-tag">templates</span>
          </div>
        </div>
        <div class="tool-actions">
          <button @click="editTool(tool)" class="btn-small">编辑</button>
          <button v-if="tool.type === 'custom'" @click="deleteTool(tool.name)" class="btn-danger btn-small">删除</button>
        </div>
      </div>
      <div v-if="tools.length === 0" class="empty">暂无自定义工具</div>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showCreateModal || editingTool" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
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
            <button type="button" @click="closeModal" class="btn-secondary">取消</button>
            <button type="submit" class="btn-primary">保存</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { toolApi } from '@/api/tool'

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
    const res = await toolApi.list()
    tools.value = res.data || []
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
      await toolApi.update(editingTool.value.name, {
        description: toolForm.value.description
      })
    } else {
      await toolApi.create(toolForm.value)
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
    await toolApi.delete(name)
    loadTools()
  } catch (e: any) {
    error.value = e.message || '删除失败'
  }
}

onMounted(loadTools)
</script>

<style scoped>
.tools-editor {
  padding: 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  margin: 0;
}

.tools-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tool-item {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 12px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.tool-info {
  flex: 1;
}

.tool-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.tool-name {
  font-weight: 600;
}

.tool-type {
  font-size: 12px;
  padding: 2px 6px;
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
  color: #666;
  font-size: 14px;
  margin-bottom: 8px;
}

.tool-modules {
  display: flex;
  gap: 6px;
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
  gap: 8px;
}

.btn-primary {
  background: #1976d2;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.btn-secondary {
  background: #f5f5f5;
  color: #333;
  border: 1px solid #ddd;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.btn-danger {
  background: #d32f2f;
  color: white;
}

.btn-small {
  padding: 4px 12px;
  font-size: 12px;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  padding: 24px;
  border-radius: 8px;
  width: 400px;
  max-width: 90vw;
}

.modal h3 {
  margin-top: 0;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 4px;
  font-weight: 500;
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-sizing: border-box;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}

.loading, .error, .empty {
  text-align: center;
  padding: 20px;
  color: #666;
}

.error {
  color: #d32f2f;
}
</style>

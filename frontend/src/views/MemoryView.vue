<template>
  <div class="memory-view">
    <div class="page-header">
      <h2>记忆管理</h2>
      <button @click="showCreateModal = true" class="btn btn-primary">新建记忆</button>
    </div>

    <div class="filters">
      <select v-model="filterType" @change="fetchMemories" class="input">
        <option value="">全部类型</option>
        <option value="private">私有记忆</option>
        <option value="shared">共享记忆</option>
      </select>
      <input
        v-model="searchQuery"
        @input="searchMemories"
        class="input search-input"
        placeholder="搜索记忆..."
      />
    </div>

    <div class="memories-list">
      <div v-for="memory in memories" :key="memory.memory_id" class="memory-card card">
        <div class="memory-header">
          <h3>{{ memory.title }}</h3>
          <span class="memory-type" :class="memory.type">{{ memory.type }}</span>
        </div>
        <p class="memory-content">{{ memory.content }}</p>
        <div class="memory-footer">
          <span class="memory-time">{{ formatTime(memory.created_at) }}</span>
          <div class="memory-actions">
            <button @click="editMemory(memory)" class="btn btn-secondary">编辑</button>
            <button @click="deleteMemory(memory)" class="btn btn-danger">删除</button>
          </div>
        </div>
      </div>

      <div v-if="memories.length === 0" class="empty-state">
        <p>暂无记忆</p>
      </div>
    </div>

    <div v-if="showCreateModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal card">
        <h3>{{ editingMemory ? '编辑' : '新建' }}记忆</h3>
        <form @submit.prevent="saveMemory">
          <div class="form-group">
            <label>标题</label>
            <input v-model="memoryForm.title" class="input" required />
          </div>
          <div class="form-group">
            <label>内容</label>
            <textarea v-model="memoryForm.content" class="input" rows="8" required></textarea>
          </div>
          <div class="form-group">
            <label>类型</label>
            <select v-model="memoryForm.type" class="input">
              <option value="private">私有记忆</option>
              <option value="shared">共享记忆</option>
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

const memories = ref<any[]>([])
const filterType = ref('')
const searchQuery = ref('')
const showCreateModal = ref(false)
const editingMemory = ref<any>(null)

const memoryForm = ref({
  title: '',
  content: '',
  type: 'private'
})

onMounted(async () => {
  await fetchMemories()
})

async function fetchMemories() {
  let url = '/api/memory'
  const params = new URLSearchParams()

  if (filterType.value) {
    params.append('type', filterType.value)
  }

  if (params.toString()) {
    url += '?' + params.toString()
  }

  const response = await axios.get(url)
  if (response.data.code === 0) {
    memories.value = response.data.data
  }
}

async function searchMemories() {
  if (!searchQuery.value.trim()) {
    await fetchMemories()
    return
  }

  const response = await axios.get('/api/memory/search', {
    params: { q: searchQuery.value }
  })

  if (response.data.code === 0) {
    memories.value = response.data.data
  }
}

function editMemory(memory: any) {
  editingMemory.value = memory
  memoryForm.value = {
    title: memory.title,
    content: memory.content,
    type: memory.type
  }
  showCreateModal.value = true
}

async function saveMemory() {
  if (editingMemory.value) {
    await axios.put(`/api/memory/${editingMemory.value.memory_id}`, {
      title: memoryForm.value.title,
      content: memoryForm.value.content
    })
  } else {
    await axios.post('/api/memory', {
      title: memoryForm.value.title,
      content: memoryForm.value.content,
      type: memoryForm.value.type
    })
  }
  closeModal()
  await fetchMemories()
}

async function deleteMemory(memory: any) {
  if (!confirm(`确定删除记忆 "${memory.title}" 吗？`)) return

  await axios.delete(`/api/memory/${memory.memory_id}`)
  await fetchMemories()
}

function closeModal() {
  showCreateModal.value = false
  editingMemory.value = null
  memoryForm.value = { title: '', content: '', type: 'private' }
}

function formatTime(time: string): string {
  if (!time) return ''
  return new Date(time).toLocaleString()
}
</script>

<style scoped>
.memory-view {
  padding: 1.5rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.filters {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.search-input {
  flex: 1;
  max-width: 300px;
}

.memories-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.memory-card {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.memory-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.memory-type {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.memory-type.private {
  background: #e8f4fc;
  color: var(--primary-color);
}

.memory-type.shared {
  background: #d4edda;
  color: #155724;
}

.memory-content {
  color: var(--text-secondary);
  font-size: 0.875rem;
  max-height: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.memory-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.memory-time {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.memory-actions {
  display: flex;
  gap: 0.5rem;
}

.empty-state {
  text-align: center;
  color: var(--text-secondary);
  padding: 2rem;
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
  max-width: 500px;
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

<template>
  <div class="agent-view">
    <div class="page-header">
      <h2>Agent 管理</h2>
      <button @click="showCreateModal = true" class="btn btn-primary">新建 Agent</button>
    </div>

    <div class="agents-grid">
      <div v-for="agent in agents" :key="agent.agent_id" class="agent-card card">
        <div class="agent-header">
          <h3>{{ agent.name }}</h3>
          <span class="agent-status" :class="agent.status">{{ agent.status }}</span>
        </div>
        <p class="agent-description">{{ agent.description }}</p>
        <div class="agent-meta">
          <span class="meta-item">工具: {{ agent.enabled_tools?.length || 0 }}</span>
          <span class="meta-item">技能: {{ agent.enabled_skills?.length || 0 }}</span>
        </div>
        <div class="agent-actions">
          <button @click="editAgent(agent)" class="btn btn-secondary">编辑</button>
          <button @click="configAgent(agent)" class="btn btn-primary">配置</button>
          <button @click="deleteAgent(agent)" class="btn btn-danger">删除</button>
        </div>
      </div>
    </div>

    <!-- Create/Edit Agent Modal -->
    <div v-if="showCreateModal || editingAgent" class="modal-overlay" @click.self="closeModal">
      <div class="modal card">
        <h3>{{ editingAgent ? '编辑' : '新建' }} Agent</h3>
        <form @submit.prevent="saveAgent">
          <div class="form-group">
            <label>名称</label>
            <input v-model="agentForm.name" class="input" required />
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="agentForm.description" class="input" rows="3"></textarea>
          </div>
          <div class="form-group">
            <label>对话模型</label>
            <select v-model="agentForm.dialogModel" class="input">
              <option v-for="model in dialogModels" :key="model" :value="model">{{ model }}</option>
            </select>
          </div>
          <div class="form-actions">
            <button type="button" @click="closeModal" class="btn btn-secondary">取消</button>
            <button type="submit" class="btn btn-primary">保存</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Agent Config Modal: Tools & Skills Selection -->
    <div v-if="showConfigModal" class="modal-overlay" @click.self="showConfigModal = false">
      <div class="config-modal card">
        <div class="config-header">
          <h3>配置 {{ currentAgent?.name }}</h3>
          <button @click="showConfigModal = false" class="btn btn-secondary">关闭</button>
        </div>

        <div class="config-tabs">
          <button
            v-for="tab in configTabs"
            :key="tab.id"
            @click="currentTab = tab.id"
            :class="{ active: currentTab === tab.id }"
          >
            {{ tab.name }}
          </button>
        </div>

        <div class="config-content">
          <!-- Tools Selection Tab -->
          <div v-if="currentTab === 'tools'" class="tab-content">
            <h4>选择启用的工具</h4>
            <div class="checkbox-list">
              <label v-for="tool in allTools" :key="tool.name" class="checkbox-item">
                <input type="checkbox" v-model="selectedTools" :value="tool.name" />
                <span class="tool-name">{{ tool.name }}</span>
                <span class="tool-desc">{{ tool.description }}</span>
              </label>
            </div>
            <div class="tab-actions">
              <button @click="saveToolsConfig" class="btn btn-primary">保存工具配置</button>
            </div>
          </div>

          <!-- Skills Selection Tab -->
          <div v-if="currentTab === 'skills'" class="tab-content">
            <h4>选择启用的技能</h4>
            <div class="checkbox-list">
              <label v-for="skill in allSkills" :key="skill.name" class="checkbox-item">
                <input type="checkbox" v-model="selectedSkills" :value="skill.name" />
                <span class="skill-name">{{ skill.name }}</span>
                <span class="skill-desc">{{ skill.description }}</span>
              </label>
            </div>
            <div class="tab-actions">
              <button @click="saveSkillsConfig" class="btn btn-primary">保存技能配置</button>
            </div>
          </div>

          <!-- Files Tab -->
          <div v-if="currentTab === 'files'" class="tab-content">
            <h4>配置文件</h4>
            <div v-for="file in agentFiles" :key="file.name" class="file-item">
              <label>{{ file.name }}.md</label>
              <textarea v-model="file.content" class="input code-input" rows="10"></textarea>
              <button @click="saveFile(file)" class="btn btn-primary">保存</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const agents = ref<any[]>([])
const showCreateModal = ref(false)
const showConfigModal = ref(false)
const editingAgent = ref<any>(null)
const currentAgent = ref<any>(null)
const currentTab = ref('tools')

const agentFiles = ref<{ name: string; content: string }[]>([])
const allTools = ref<any[]>([])
const allSkills = ref<any[]>([])
const selectedTools = ref<string[]>([])
const selectedSkills = ref<string[]>([])

const dialogModels = ref(['ollama/llama2', 'openai/gpt-4', 'vllm/llama2'])

const configTabs = [
  { id: 'tools', name: '工具' },
  { id: 'skills', name: '技能' },
  { id: 'files', name: '文件' }
]

const agentForm = ref({
  name: '',
  description: '',
  dialogModel: ''
})

onMounted(async () => {
  await fetchAgents()
  await loadToolsAndSkills()
})

async function fetchAgents() {
  const response = await axios.get('/api/agents')
  if (response.data.code === 0) {
    agents.value = response.data.data
  }
}

async function loadToolsAndSkills() {
  // Load all tools
  try {
    const toolsRes = await axios.get('/api/tools')
    allTools.value = toolsRes.data.data || []
  } catch (e) {
    console.error('Failed to load tools:', e)
  }

  // Load all skills
  try {
    const skillsRes = await axios.get('/api/skills')
    allSkills.value = skillsRes.data.data || []
  } catch (e) {
    console.error('Failed to load skills:', e)
  }
}

function editAgent(agent: any) {
  editingAgent.value = agent
  agentForm.value = {
    name: agent.name,
    description: agent.description,
    dialogModel: ''
  }
  showCreateModal.value = true
}

async function configAgent(agent: any) {
  currentAgent.value = agent
  currentTab.value = 'tools'

  // Load current config
  const response = await axios.get(`/api/agents/${agent.agent_id}`)
  if (response.data.code === 0) {
    const data = response.data.data
    selectedTools.value = data.enabled_tools || []
    selectedSkills.value = data.enabled_skills || []
    agentFiles.value = [
      { name: 'AGENTS', content: data.files['AGENTS.md'] || '' },
      { name: 'SOUL', content: data.files['SOUL.md'] || '' },
      { name: 'USER', content: data.files['USER.md'] || '' },
      { name: 'MEMORY', content: data.files['MEMORY.md'] || '' },
      { name: 'HEARTBEAT', content: data.files['HEARTBEAT.md'] || '' }
    ]
  }

  showConfigModal.value = true
}

async function saveToolsConfig() {
  if (!currentAgent.value) return
  try {
    await axios.put(`/api/agents/${currentAgent.value.agent_id}/tools`, selectedTools.value)
    alert('工具配置已保存')
    await fetchAgents()
  } catch (e: any) {
    alert('保存失败: ' + (e.message || '未知错误'))
  }
}

async function saveSkillsConfig() {
  if (!currentAgent.value) return
  try {
    await axios.put(`/api/agents/${currentAgent.value.agent_id}/skills`, selectedSkills.value)
    alert('技能配置已保存')
    await fetchAgents()
  } catch (e: any) {
    alert('保存失败: ' + (e.message || '未知错误'))
  }
}

async function saveAgent() {
  if (editingAgent.value) {
    await axios.put(`/api/agents/${editingAgent.value.agent_id}`, {
      name: agentForm.value.name,
      description: agentForm.value.description
    })
  } else {
    await axios.post('/api/agents', {
      name: agentForm.value.name,
      description: agentForm.value.description,
      dialog_model: { provider: 'ollama', model_name: 'llama2' }
    })
  }
  showCreateModal.value = false
  editingAgent.value = null
  await fetchAgents()
}

async function deleteAgent(agent: any) {
  if (confirm(`确定删除 Agent "${agent.name}" 吗？`)) {
    await axios.delete(`/api/agents/${agent.agent_id}`)
    await fetchAgents()
  }
}

async function saveFile(file: any) {
  if (!currentAgent.value) return
  await axios.put(
    `/api/agents/${currentAgent.value.agent_id}/file/${file.name}.md`,
    file.content,
    { headers: { 'Content-Type': 'text/plain' } }
  )
  alert('保存成功')
}

function closeModal() {
  showCreateModal.value = false
  editingAgent.value = null
  agentForm.value = { name: '', description: '', dialogModel: '' }
}
</script>

<style scoped>
.agent-view {
  padding: 1.5rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.agents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.agent-card {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.agent-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.agent-status {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.agent-status.active {
  background: #d4edda;
  color: #155724;
}

.agent-description {
  color: var(--text-secondary);
  font-size: 0.875rem;
  flex: 1;
}

.agent-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.meta-item {
  background: var(--background-color);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.agent-actions {
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
  max-width: 500px;
}

.config-modal {
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
}

.config-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-color);
}

.config-tabs button {
  padding: 0.75rem 1.5rem;
  background: none;
  border: none;
  cursor: pointer;
  border-bottom: 2px solid transparent;
}

.config-tabs button.active {
  border-bottom-color: var(--primary-color);
  color: var(--primary-color);
}

.config-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.tab-content h4 {
  margin-bottom: 1rem;
}

.checkbox-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background: var(--background-color);
  border-radius: 8px;
  cursor: pointer;
}

.checkbox-item:hover {
  background: var(--surface-color);
}

.checkbox-item input[type="checkbox"] {
  width: 18px;
  height: 18px;
}

.tool-name, .skill-name {
  font-weight: 600;
  min-width: 150px;
}

.tool-desc, .skill-desc {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.tab-actions {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border-color);
}

.file-item {
  margin-bottom: 1rem;
}

.file-item label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.code-input {
  font-family: monospace;
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
<template>
  <div class="skills-editor">
    <!-- Agent Skills Selection Mode -->
    <div v-if="agentId" class="agent-skills-config">
      <div class="section-header">
        <h3>为 Agent {{ agentName }} 配置技能</h3>
        <button @click="saveAgentSkills" class="btn-primary" :disabled="saving">
          {{ saving ? '保存中...' : '保存配置' }}
        </button>
      </div>

      <div v-if="loading" class="loading">加载技能列表...</div>
      <div v-else class="skills-list">
        <div v-for="skill in allSkills" :key="skill.name" class="skill-item selectable">
          <div class="skill-checkbox">
            <input
              type="checkbox"
              :id="'skill-' + skill.name"
              v-model="selectedSkills"
              :value="skill.name"
            />
          </div>
          <div class="skill-info">
            <div class="skill-header">
              <span class="skill-name">{{ skill.name }}</span>
              <span v-if="skill.trigger" class="skill-trigger">{{ skill.trigger }}</span>
            </div>
            <div class="skill-description">{{ skill.description }}</div>
          </div>
        </div>
        <div v-if="allSkills.length === 0" class="empty">暂无可用技能</div>
      </div>

      <div class="selected-info">
        已选择 {{ selectedSkills.length }} 个技能
      </div>
    </div>

    <!-- Standalone Skills Management Mode -->
    <div v-else class="skills-management">
      <div class="section-header">
        <h3>技能管理</h3>
        <button @click="showCreateModal = true" class="btn-primary">创建技能</button>
      </div>

      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else class="skills-list">
        <div v-for="skill in skills" :key="skill.name" class="skill-item">
          <div class="skill-info">
            <div class="skill-header">
              <span class="skill-name">{{ skill.name }}</span>
              <span v-if="skill.trigger" class="skill-trigger">{{ skill.trigger }}</span>
            </div>
            <div class="skill-description">{{ skill.description }}</div>
            <div class="skill-modules" v-if="skill.has_references || skill.has_scripts || skill.has_templates || skill.has_examples">
              <span v-if="skill.has_references" class="module-tag">references</span>
              <span v-if="skill.has_scripts" class="module-tag">scripts</span>
              <span v-if="skill.has_templates" class="module-tag">templates</span>
              <span v-if="skill.has_examples" class="module-tag">examples</span>
            </div>
          </div>
          <div class="skill-actions">
            <button @click="editSkill(skill)" class="btn-small">编辑</button>
            <button @click="deleteSkill(skill.name)" class="btn-danger btn-small">删除</button>
          </div>
        </div>
        <div v-if="skills.length === 0" class="empty">暂无技能</div>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showCreateModal || editingSkill" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <h3>{{ editingSkill ? '编辑技能' : '创建技能' }}</h3>
        <form @submit.prevent="saveSkill">
          <div class="form-group">
            <label>名称</label>
            <input v-model="skillForm.name" :disabled="!!editingSkill" type="text" required />
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="skillForm.description" rows="3"></textarea>
          </div>
          <div class="form-group">
            <label>触发词</label>
            <input v-model="skillForm.trigger" type="text" placeholder="如: .pdf, write-doc" />
          </div>
          <div class="form-group" v-if="editingSkill">
            <label>指令内容</label>
            <textarea v-model="skillForm.content" rows="10"></textarea>
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
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'
import { skillApi } from '@/api/skill'

const props = defineProps<{
  agentId?: string
  agentName?: string
}>()

const skills = ref<any[]>([])
const allSkills = ref<any[]>([])
const selectedSkills = ref<string[]>([])
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const showCreateModal = ref(false)
const editingSkill = ref<any>(null)

const skillForm = ref({
  name: '',
  description: '',
  trigger: '',
  content: ''
})

const loadSkills = async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await skillApi.list()
    skills.value = res.data || []
    allSkills.value = res.data || []
  } catch (e: any) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

const loadAgentSkills = async () => {
  if (!props.agentId) return
  loading.value = true
  error.value = ''
  try {
    // Load all available skills
    const skillsRes = await skillApi.list()
    allSkills.value = skillsRes.data || []

    // Load agent's enabled skills
    const agentRes = await axios.get(`/api/agents/${props.agentId}/skills`)
    selectedSkills.value = agentRes.data.data?.enabled || []
  } catch (e: any) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

const saveAgentSkills = async () => {
  if (!props.agentId) return
  saving.value = true
  error.value = ''
  try {
    await axios.put(`/api/agents/${props.agentId}/skills`, selectedSkills.value)
    alert('保存成功！')
  } catch (e: any) {
    error.value = e.message || '保存失败'
  } finally {
    saving.value = false
  }
}

const editSkill = async (skill: any) => {
  try {
    const res = await skillApi.get(skill.name)
    editingSkill.value = skill
    skillForm.value = {
      name: skill.name,
      description: skill.description || '',
      trigger: skill.trigger || '',
      content: res.data.content || ''
    }
  } catch (e: any) {
    error.value = e.message || '加载失败'
  }
}

const closeModal = () => {
  showCreateModal.value = false
  editingSkill.value = null
  skillForm.value = { name: '', description: '', trigger: '', content: '' }
}

const saveSkill = async () => {
  try {
    if (editingSkill.value) {
      await skillApi.update(editingSkill.value.name, {
        description: skillForm.value.description,
        content: skillForm.value.content
      })
    } else {
      await skillApi.create(skillForm.value)
    }
    closeModal()
    loadSkills()
  } catch (e: any) {
    error.value = e.message || '保存失败'
  }
}

const deleteSkill = async (name: string) => {
  if (!confirm(`确定删除技能 ${name}？`)) return
  try {
    await skillApi.delete(name)
    loadSkills()
  } catch (e: any) {
    error.value = e.message || '删除失败'
  }
}

onMounted(() => {
  if (props.agentId) {
    loadAgentSkills()
  } else {
    loadSkills()
  }
})

watch(() => props.agentId, (newId) => {
  if (newId) {
    loadAgentSkills()
  }
})
</script>

<style scoped>
.skills-editor {
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

.skills-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.skill-item {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 12px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.skill-item.selectable {
  cursor: pointer;
}

.skill-item.selectable:hover {
  border-color: #1976d2;
  background: #f8f9fa;
}

.skill-checkbox {
  margin-right: 12px;
  padding-top: 2px;
}

.skill-checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.selected-info {
  margin-top: 16px;
  padding: 12px;
  background: #e3f2fd;
  border-radius: 8px;
  color: #1976d2;
  font-weight: 500;
}

.skill-info {
  flex: 1;
}

.skill-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.skill-name {
  font-weight: 600;
}

.skill-trigger {
  font-size: 12px;
  padding: 2px 8px;
  background: #e3f2fd;
  color: #1976d2;
  border-radius: 4px;
}

.skill-description {
  color: #666;
  font-size: 14px;
  margin-bottom: 8px;
}

.skill-modules {
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

.skill-actions {
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
  width: 500px;
  max-width: 90vw;
  max-height: 90vh;
  overflow-y: auto;
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

<template>
  <div class="skill-view">
    <div class="page-header">
      <h2>技能管理</h2>
      <button @click="showCreateModal = true" class="btn btn-primary">创建技能</button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="skills-grid">
      <div v-for="skill in skills" :key="skill.name" class="skill-card card">
        <div class="skill-header">
          <h3>{{ skill.name }}</h3>
          <span v-if="skill.trigger" class="skill-trigger">{{ skill.trigger }}</span>
        </div>
        <p class="skill-description">{{ skill.description }}</p>
        <div class="skill-modules" v-if="skill.has_references || skill.has_scripts || skill.has_templates || skill.has_examples">
          <span v-if="skill.has_references" class="module-tag">references</span>
          <span v-if="skill.has_scripts" class="module-tag">scripts</span>
          <span v-if="skill.has_templates" class="module-tag">templates</span>
          <span v-if="skill.has_examples" class="module-tag">examples</span>
        </div>
        <div class="skill-actions">
          <button @click="editSkill(skill)" class="btn btn-secondary">编辑</button>
          <button @click="deleteSkill(skill.name)" class="btn btn-danger">删除</button>
        </div>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showCreateModal || editingSkill" class="modal-overlay" @click.self="closeModal">
      <div class="modal card">
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
import { skillApi } from '@/api/skill'

const skills = ref<any[]>([])
const loading = ref(false)
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
  } catch (e: any) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
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

onMounted(loadSkills)
</script>

<style scoped>
.skill-view {
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

.skills-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.skill-card {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.skill-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.skill-trigger {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  background: #e3f2fd;
  color: #1976d2;
  border-radius: 4px;
}

.skill-description {
  color: var(--text-secondary);
  font-size: 0.875rem;
  flex: 1;
}

.skill-modules {
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

.skill-actions {
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
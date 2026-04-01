<template>
  <div class="chat-container">
    <div class="chat-header">
      <div class="agent-selector">
        <label>选择Agent:</label>
        <select v-model="selectedAgentId" class="input">
          <option v-for="agent in agents" :key="agent.agent_id" :value="agent.agent_id">
            {{ agent.name }}
          </option>
        </select>
      </div>
      <div class="session-selector">
        <button @click="showSessionList = !showSessionList" class="btn btn-secondary">
          会话列表
        </button>
      </div>
    </div>

    <div class="chat-main">
      <div v-if="showSessionList" class="session-panel">
        <div class="session-header">
          <h3>会话列表</h3>
          <button @click="createNewSession" class="btn btn-primary">新建会话</button>
        </div>
        <div class="session-list">
          <div
            v-for="session in chatStore.sessions"
            :key="session.session_id"
            class="session-item"
            :class="{ active: session.session_id === chatStore.currentSessionId }"
            @click="selectSession(session.session_id)"
          >
            <span class="session-title">{{ session.title || '新会话' }}</span>
            <span class="session-time">{{ formatTime(session.updated_at) }}</span>
          </div>
        </div>
      </div>

      <div class="messages-area">
        <div class="messages-list" ref="messagesListRef">
          <div v-if="chatStore.messages.length === 0" class="empty-state">
            <p>开始对话吧！上传文件并输入消息。</p>
          </div>

          <div
            v-for="msg in chatStore.messages"
            :key="msg.id"
            class="message"
            :class="msg.role"
          >
            <div class="message-content">
              <div class="message-text" v-html="renderMarkdown(msg.content)"></div>

              <div v-if="msg.tool_results && msg.tool_results.length > 0" class="tool-results">
                <div class="tool-results-header">执行记录:</div>
                <div
                  v-for="(result, idx) in msg.tool_results"
                  :key="idx"
                  class="tool-result-item"
                >
                  <div class="tool-name">{{ result.type }}: {{ result.name }}</div>
                  <div class="tool-input">输入: {{ result.input }}</div>
                  <div class="tool-output">输出: {{ result.output }}</div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="chatStore.isLoading" class="message assistant loading">
            <div class="message-content">
              <div class="executing-tasks">
                <div v-for="[taskId, task] in chatStore.executingTasks" :key="taskId" class="task-item">
                  <span class="task-icon">🔧</span>
                  <span class="task-name">{{ task.name }}</span>
                  <span class="task-status">{{ task.status }} {{ task.progress }}</span>
                </div>
              </div>
              <div class="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>

        <div class="input-area">
          <div class="uploaded-files" v-if="uploadedFiles.length > 0">
            <div v-for="(file, idx) in uploadedFiles" :key="idx" class="uploaded-file">
              <span>{{ file.name }}</span>
              <button @click="removeFile(idx)" class="remove-file">×</button>
            </div>
          </div>

          <div class="input-row">
            <button @click="triggerFileUpload" class="btn btn-secondary upload-btn">
              📎
            </button>
            <input
              type="file"
              ref="fileInputRef"
              @change="handleFileUpload"
              multiple
              hidden
            />
            <textarea
              v-model="inputMessage"
              @keydown.enter.exact.prevent="sendMessage"
              placeholder="输入消息... (Enter 发送)"
              class="input message-input"
              rows="1"
            ></textarea>
            <button
              @click="sendMessage"
              class="btn btn-primary send-btn"
              :disabled="!inputMessage.trim() || !chatStore.isConnected"
            >
              发送
            </button>
          </div>
        </div>
      </div>
    </div>

    <ConfirmDialog
      v-if="showConfirm"
      :tool="confirmData.tool"
      :action="confirmData.action"
      :target="confirmData.target"
      :warning="confirmData.warning"
      @confirm="handleConfirm(true)"
      @cancel="handleConfirm(false)"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import axios from 'axios'
import { marked } from 'marked'
import ConfirmDialog from '@/components/Chat/ConfirmDialog.vue'

const authStore = useAuthStore()
const chatStore = useChatStore()

const agents = ref<any[]>([])
const selectedAgentId = ref('')
const inputMessage = ref('')
const uploadedFiles = ref<{ name: string; id: string }[]>([])
const fileInputRef = ref<HTMLInputElement | null>(null)
const messagesListRef = ref<HTMLElement | null>(null)
const showSessionList = ref(false)

const showConfirm = ref(false)
const confirmData = ref({
  tool: '',
  action: '',
  target: '',
  warning: ''
})

onMounted(async () => {
  // Connect WebSocket
  chatStore.connectWebSocket(authStore.token)

  // Fetch agents
  const response = await axios.get('/api/agents')
  if (response.data.code === 0) {
    agents.value = response.data.data
    if (agents.value.length > 0) {
      selectedAgentId.value = agents.value[0].agent_id
    }
  }

  // Fetch sessions
  await chatStore.fetchSessions()
})

onUnmounted(() => {
  chatStore.disconnect()
})

watch(() => chatStore.messages, () => {
  nextTick(() => {
    if (messagesListRef.value) {
      messagesListRef.value.scrollTop = messagesListRef.value.scrollHeight
    }
  })
}, { deep: true })

function renderMarkdown(text: string): string {
  return marked(text) as string
}

function formatTime(time: string): string {
  if (!time) return ''
  const date = new Date(time)
  return date.toLocaleDateString()
}

async function sendMessage() {
  if (!inputMessage.value.trim()) return

  const fileIds = uploadedFiles.value.map(f => f.id)
  await chatStore.sendMessage(selectedAgentId.value, inputMessage.value, fileIds)

  inputMessage.value = ''
  uploadedFiles.value = []
}

function triggerFileUpload() {
  fileInputRef.value?.click()
}

async function handleFileUpload(event: Event) {
  const target = event.target as HTMLInputElement
  const files = target.files

  if (!files) return

  for (const file of files) {
    const formData = new FormData()
    formData.append('file', file)

    const response = await axios.post('/api/files/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    if (response.data.code === 0) {
      uploadedFiles.value.push({
        name: file.name,
        id: response.data.data.file_id
      })
    }
  }

  target.value = ''
}

function removeFile(index: number) {
  uploadedFiles.value.splice(index, 1)
}

async function createNewSession() {
  if (!selectedAgentId.value) return

  const response = await axios.post(`/api/sessions?agent_id=${selectedAgentId.value}`)
  if (response.data.code === 0) {
    chatStore.currentSessionId = response.data.data.session_id
    chatStore.clearMessages()
    await chatStore.fetchSessions()
    showSessionList.value = false
  }
}

async function selectSession(sessionId: string) {
  chatStore.currentSessionId = sessionId
  chatStore.clearMessages()

  const response = await axios.get(`/api/sessions/${sessionId}`)
  if (response.data.code === 0) {
    chatStore.messages = response.data.data.messages || []
  }

  showSessionList.value = false
}

function handleConfirm(approved: boolean) {
  showConfirm.value = false
  // Send confirmation response via WebSocket
  // Implementation depends on WebSocket protocol
}
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-header {
  padding: 1rem;
  background: var(--surface-color);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.agent-selector {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.agent-selector select {
  width: 200px;
}

.chat-main {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.session-panel {
  width: 280px;
  background: var(--surface-color);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
}

.session-header {
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.session-list {
  flex: 1;
  overflow-y: auto;
}

.session-item {
  padding: 0.75rem 1rem;
  cursor: pointer;
  border-bottom: 1px solid var(--border-color);
}

.session-item:hover {
  background: var(--background-color);
}

.session-item.active {
  background: #e8f4fc;
}

.session-title {
  display: block;
  font-weight: 500;
}

.session-time {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.messages-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.messages-list {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.empty-state {
  text-align: center;
  color: var(--text-secondary);
  padding: 2rem;
}

.message {
  margin-bottom: 1rem;
  display: flex;
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.message-content {
  max-width: 70%;
  padding: 0.75rem 1rem;
  border-radius: 8px;
}

.message.user .message-content {
  background: var(--primary-color);
  color: white;
}

.message.assistant .message-content {
  background: var(--surface-color);
  border: 1px solid var(--border-color);
}

.message-text {
  white-space: pre-wrap;
  word-break: break-word;
}

.tool-results {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border-color);
}

.tool-results-header {
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: var(--text-secondary);
}

.tool-result-item {
  background: var(--background-color);
  padding: 0.5rem;
  border-radius: 4px;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.tool-name {
  font-weight: 600;
  color: var(--primary-color);
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 0.5rem;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: var(--text-secondary);
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-4px); }
}

.input-area {
  padding: 1rem;
  background: var(--surface-color);
  border-top: 1px solid var(--border-color);
}

.uploaded-files {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.uploaded-file {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  background: var(--background-color);
  border-radius: 4px;
  font-size: 0.875rem;
}

.remove-file {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 1rem;
}

.input-row {
  display: flex;
  gap: 0.5rem;
  align-items: flex-end;
}

.upload-btn {
  padding: 0.5rem 0.75rem;
}

.message-input {
  flex: 1;
  resize: none;
  min-height: 40px;
  max-height: 120px;
}

.send-btn {
  padding: 0.5rem 1.5rem;
}

.executing-tasks {
  margin-bottom: 0.5rem;
}

.task-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0;
  font-size: 0.875rem;
  color: var(--primary-color);
}
</style>

import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

const API_BASE = '/api'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  files?: string[]
  tool_results?: ToolResult[]
  timestamp: string
}

export interface ToolResult {
  type: 'tool' | 'skill'
  name: string
  input: string
  output: string
}

export const useChatStore = defineStore('chat', () => {
  const sessions = ref<any[]>([])
  const currentSessionId = ref<string | null>(null)
  const messages = ref<Message[]>([])
  const isConnected = ref(false)
  const isLoading = ref(false)
  const executingTasks = ref<Map<string, any>>(new Map())

  let ws: WebSocket | null = null

  async function fetchSessions() {
    const response = await axios.get(`${API_BASE}/sessions`)
    if (response.data.code === 0) {
      sessions.value = response.data.data.sessions
    }
  }

  function connectWebSocket(token: string) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    ws = new WebSocket(`${protocol}//${window.location.host}/ws/chat?token=${token}`)

    ws.onopen = () => {
      isConnected.value = true
      console.log('WebSocket connected')
    }

    ws.onclose = () => {
      isConnected.value = false
      console.log('WebSocket disconnected')
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      handleMessage(data)
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
  }

  function handleMessage(data: any) {
    switch (data.type) {
      case 'ack':
        // Session acknowledged - update current session ID
        if (data.session_id) {
          currentSessionId.value = data.session_id
        }
        break

      case 'executing':
        executingTasks.value.set(data.task_id, {
          name: data.name,
          status: data.status,
          progress: data.progress,
          message: data.message
        })
        break

      case 'tool_complete':
      case 'skill_complete':
        if (data.task_id && executingTasks.value.has(data.task_id)) {
          const task = executingTasks.value.get(data.task_id)
          task.result = data.result
          task.status = 'complete'
        }
        break

      case 'final':
        // Add assistant message with tool results
        messages.value.push({
          id: `msg_${Date.now()}`,
          role: 'assistant',
          content: data.message,
          tool_results: data.results,
          timestamp: data.timestamp || new Date().toISOString()
        })
        isLoading.value = false
        // Clear executing tasks
        executingTasks.value.clear()
        break

      case 'confirm_request':
        // Handle confirmation request
        // This would show a dialog to user
        break

      case 'error':
        console.error('Chat error:', data.message)
        isLoading.value = false
        break
    }
  }

  async function sendMessage(agentId: string, content: string, files: string[] = []) {
    if (!ws || !isConnected.value) return

    isLoading.value = true

    // Add user message
    messages.value.push({
      id: `msg_${Date.now()}`,
      role: 'user',
      content,
      files,
      timestamp: new Date().toISOString()
    })

    // Send to WebSocket
    ws.send(JSON.stringify({
      type: 'chat',
      session_id: currentSessionId.value,
      agent_id: agentId,
      message: content,
      files
    }))
  }

  function disconnect() {
    if (ws) {
      ws.close()
      ws = null
    }
    isConnected.value = false
  }

  function clearMessages() {
    messages.value = []
    executingTasks.value.clear()
  }

  return {
    sessions,
    currentSessionId,
    messages,
    isConnected,
    isLoading,
    executingTasks,
    fetchSessions,
    connectWebSocket,
    sendMessage,
    disconnect,
    clearMessages
  }
})

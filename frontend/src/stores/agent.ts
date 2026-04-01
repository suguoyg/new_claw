// Type definitions placeholder
export interface Agent {
  agent_id: string
  name: string
  description: string
  status: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  files?: string[]
  timestamp: string
}

export interface Skill {
  name: string
  description: string
  trigger: string
}

export interface Memory {
  memory_id: string
  title: string
  content: string
  type: 'private' | 'shared'
  agent_id?: string
}

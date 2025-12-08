// 类型定义

export type PublishStatus = 'idle' | 'success' | 'error'

export interface ChatRequest {
  apiBaseUrl: string
  message: string
  thread_id: string | null
  reset: boolean
}

export interface ChatResponse {
  response: string
  thread_id?: string
  [key: string]: any
}

export interface ChromeMessage {
  action: string
  data?: any
}

export interface SidebarState {
  isVisible: boolean
  isCollapsed: boolean
}

export interface PublishState {
  isPublishing: boolean
  status: PublishStatus
  message: string
}

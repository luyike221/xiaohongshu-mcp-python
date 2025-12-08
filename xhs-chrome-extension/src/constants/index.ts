// 常量配置

export const DEFAULT_API_BASE_URL = 'http://localhost:8012'
export const MAX_CONTENT_LENGTH = 1000
export const AUTO_CLEAR_DELAY = 3000

export const MESSAGE_ACTIONS = {
  TOGGLE_SIDEBAR: 'toggleSidebar',
  CHAT_REQUEST: 'chatRequest',
} as const

export const SUCCESS_KEYWORDS = ['成功', '已发布', '完成']
export const ERROR_KEYWORDS = ['失败', '错误']

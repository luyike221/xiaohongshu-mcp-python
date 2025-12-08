// API 服务

import type { ChatRequest, ChatResponse } from '../types'

/**
 * 通过 background script 发送聊天请求（绕过 CORS）
 */
export async function sendChatRequest(requestData: ChatRequest): Promise<ChatResponse> {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(
      {
        action: 'chatRequest',
        data: requestData,
      },
      (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message))
          return
        }

        if (!response.success) {
          reject(new Error(response.error || '请求失败'))
          return
        }

        resolve(response.data)
      }
    )
  })
}

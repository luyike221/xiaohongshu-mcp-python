// 发布功能逻辑

import { ref } from 'vue'
import type { PublishStatus } from '../types'
import { sendChatRequest } from '../services/api'
import { StorageService } from '../services/storage'
import { SUCCESS_KEYWORDS, ERROR_KEYWORDS, AUTO_CLEAR_DELAY } from '../constants'

export function usePublish() {
  const contentText = ref('')
  const isPublishing = ref(false)
  const publishStatus = ref<PublishStatus>('idle')
  const publishMessage = ref('')
  const apiBaseUrl = ref('')

  // 初始化 API URL
  const initApiUrl = async () => {
    apiBaseUrl.value = await StorageService.getApiBaseUrl()
  }

  const clearContent = () => {
    contentText.value = ''
    publishStatus.value = 'idle'
    publishMessage.value = ''
  }

  const publishContent = async () => {
    if (!contentText.value.trim()) {
      alert('请输入要发布的内容')
      return
    }

    isPublishing.value = true
    publishStatus.value = 'idle'
    publishMessage.value = ''

    try {
      console.log('发布请求:', contentText.value)

      const result = await sendChatRequest({
        apiBaseUrl: apiBaseUrl.value,
        message: contentText.value,
        thread_id: null,
        reset: true,
      })

      const responseText = result.response || ''
      const isSuccess = checkPublishSuccess(responseText)

      if (isSuccess) {
        publishStatus.value = 'success'
        publishMessage.value = responseText || '发布成功！'
        // 3秒后清空内容
        setTimeout(() => {
          if (publishStatus.value === 'success') {
            clearContent()
          }
        }, AUTO_CLEAR_DELAY)
      } else {
        publishStatus.value = 'error'
        publishMessage.value = responseText || '发布可能失败，请查看 AI 回复'
      }

      console.log('发布结果:', result)
    } catch (error: any) {
      publishStatus.value = 'error'
      publishMessage.value = error.message || '发布失败，请检查网络连接和 API 配置'
      console.error('发布失败:', error)
      alert(`发布失败: ${error.message || '未知错误'}`)
    } finally {
      isPublishing.value = false
    }
  }

  const checkPublishSuccess = (responseText: string): boolean => {
    const hasSuccessKeyword = SUCCESS_KEYWORDS.some((keyword) =>
      responseText.includes(keyword)
    )
    const hasErrorKeyword = ERROR_KEYWORDS.some((keyword) =>
      responseText.includes(keyword)
    )

    return hasSuccessKeyword || (!hasErrorKeyword && responseText.trim().length > 0)
  }

  return {
    contentText,
    isPublishing,
    publishStatus,
    publishMessage,
    apiBaseUrl,
    initApiUrl,
    clearContent,
    publishContent,
  }
}

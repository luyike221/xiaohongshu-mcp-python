// Storage 服务

import { DEFAULT_API_BASE_URL } from '../constants'

export const StorageService = {
  /**
   * 获取 API 基础 URL
   */
  async getApiBaseUrl(): Promise<string> {
    try {
      const result = await chrome.storage.sync.get(['apiBaseUrl'])
      return result.apiBaseUrl || DEFAULT_API_BASE_URL
    } catch (error) {
      console.warn('读取 API 配置失败，使用默认值:', error)
      return DEFAULT_API_BASE_URL
    }
  },

  /**
   * 设置 API 基础 URL
   */
  async setApiBaseUrl(url: string): Promise<void> {
    try {
      await chrome.storage.sync.set({ apiBaseUrl: url })
    } catch (error) {
      console.error('保存 API 配置失败:', error)
      throw error
    }
  },
}

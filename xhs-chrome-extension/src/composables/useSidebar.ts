// Sidebar 状态管理

import { ref, onMounted } from 'vue'
import { MESSAGE_ACTIONS } from '../constants'

export function useSidebar() {
  const isVisible = ref(true)
  const isCollapsed = ref(false)

  const closeSidebar = () => {
    isVisible.value = false
    document.body.classList.remove('xhs-sidebar-open', 'collapsed')
  }

  const toggleCollapse = () => {
    isCollapsed.value = !isCollapsed.value
  }

  // 监听来自 background 的消息
  onMounted(() => {
    document.body.classList.add('xhs-sidebar-open')

    chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
      if (message.action === MESSAGE_ACTIONS.TOGGLE_SIDEBAR) {
        isVisible.value = !isVisible.value
        if (isVisible.value) {
          isCollapsed.value = false
          document.body.classList.add('xhs-sidebar-open')
          document.body.classList.remove('collapsed')
        } else {
          document.body.classList.remove('xhs-sidebar-open', 'collapsed')
        }
        sendResponse({ success: true, visible: isVisible.value })
      }
      return true
    })

    console.log('✅ 侧边栏已初始化并显示')
  })

  return {
    isVisible,
    isCollapsed,
    closeSidebar,
    toggleCollapse,
  }
}

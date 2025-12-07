import { createApp } from 'vue'
import Sidebar from '../components/Sidebar.vue'

console.log('🔧 小红书发布助手 Content Script 已加载')
console.log('📍 当前页面 URL:', window.location.href)
console.log('📄 Document ready state:', document.readyState)

let sidebarApp: ReturnType<typeof createApp> | null = null

// 创建侧边栏容器和样式
const setupSidebarStyles = () => {
  // 检查样式是否已添加
  if (document.getElementById('xhs-sidebar-styles')) {
    return
  }

  const style = document.createElement('style')
  style.id = 'xhs-sidebar-styles'
  style.textContent = `
    #xhs-sidebar-container {
      position: fixed !important;
      top: 0 !important;
      right: 0 !important;
      width: 360px !important;
      height: 100vh !important;
      z-index: 2147483647 !important;
      pointer-events: auto !important;
    }
    
    /* 防止页面内容被侧边栏遮挡时的交互问题 */
    body.xhs-sidebar-open {
      margin-right: 360px;
      transition: margin-right 0.3s ease;
    }
    
    body.xhs-sidebar-open.collapsed {
      margin-right: 60px;
    }
  `
  document.head.appendChild(style)
}

// 创建侧边栏容器
const createSidebarContainer = () => {
  // 检查是否已经存在侧边栏容器
  let container = document.getElementById('xhs-sidebar-container')
  if (container) {
    return container
  }

  container = document.createElement('div')
  container.id = 'xhs-sidebar-container'
  container.style.display = 'block' // 确保默认显示
  document.body.appendChild(container)
  
  return container
}

// 初始化侧边栏
const initSidebar = () => {
  // 设置样式
  setupSidebarStyles()
  
  // 获取或创建容器
  const container = createSidebarContainer()
  
  // 如果 Vue 应用已存在，直接显示
  if (sidebarApp) {
    container.style.display = 'block'
    document.body.classList.add('xhs-sidebar-open')
    return
  }
  
  // 创建 Vue 应用
  sidebarApp = createApp(Sidebar)
  sidebarApp.mount(container)
  
  // 确保容器可见
  container.style.display = 'block'
  
  // 添加 body 类名，用于调整页面布局
  document.body.classList.add('xhs-sidebar-open')
  
  console.log('✅ 侧边栏已初始化并显示')
  console.log('📦 容器元素:', container)
  console.log('👁️ 容器是否可见:', container.style.display)
}

// 初始化函数，确保在合适的时机执行
const startInit = () => {
  try {
    // 确保 body 存在
    if (!document.body) {
      console.log('等待 body 元素...')
      setTimeout(startInit, 100)
      return
    }
    
    console.log('开始初始化侧边栏...')
    initSidebar()
  } catch (error) {
    console.error('初始化侧边栏失败:', error)
  }
}

// 等待 DOM 加载完成
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', startInit)
} else {
  // 如果 DOM 已经加载，直接初始化
  startInit()
}

// 监听来自 background 或 popup 的消息，切换侧边栏显示/隐藏
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'toggleSidebar') {
    const container = document.getElementById('xhs-sidebar-container')
    
    if (container) {
      const isVisible = container.style.display !== 'none'
      
      if (isVisible) {
        // 隐藏侧边栏
        container.style.display = 'none'
        document.body.classList.remove('xhs-sidebar-open', 'collapsed')
        sendResponse({ success: true, visible: false })
      } else {
        // 显示侧边栏
        container.style.display = 'block'
        document.body.classList.add('xhs-sidebar-open')
        sendResponse({ success: true, visible: true })
      }
    } else {
      // 如果容器不存在，初始化
      initSidebar()
      sendResponse({ success: true, visible: true })
    }
  }
  return true
})

// 与 background 通信，通知 content script 已加载
try {
  chrome.runtime.sendMessage({ action: 'contentScriptReady' }, (response) => {
    if (chrome.runtime.lastError) {
      console.warn('发送消息到 background 失败:', chrome.runtime.lastError.message)
    } else {
      console.log('Content script 就绪:', response)
    }
  })
} catch (error) {
  console.warn('Content script 通信错误:', error)
}

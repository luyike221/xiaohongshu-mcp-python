<script setup lang="ts">
import { ref, onMounted } from 'vue'

const isVisible = ref(true)
const isCollapsed = ref(false)

const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
  // 更新 body 类名
  if (isCollapsed.value) {
    document.body.classList.add('collapsed')
  } else {
    document.body.classList.remove('collapsed')
  }
}

const closeSidebar = () => {
  isVisible.value = false
  document.body.classList.remove('xhs-sidebar-open', 'collapsed')
}

// 监听来自 content script 的消息，控制侧边栏显示/隐藏
onMounted(() => {
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'toggleSidebar') {
      isVisible.value = !isVisible.value
      if (isVisible.value) {
        isCollapsed.value = false
      }
      // 更新 body 类名
      if (isVisible.value) {
        document.body.classList.add('xhs-sidebar-open')
      } else {
        document.body.classList.remove('xhs-sidebar-open', 'collapsed')
      }
    }
    return true
  })
})
</script>

<template>
  <div v-if="isVisible" class="xhs-sidebar" :class="{ collapsed: isCollapsed }">
    <!-- 侧边栏头部 -->
    <div class="sidebar-header">
      <div class="sidebar-title">
        <h3>小红书发布助手</h3>
      </div>
      <div class="sidebar-controls">
        <button class="btn-icon" @click="toggleSidebar" :title="isCollapsed ? '展开' : '收起'">
          <svg v-if="!isCollapsed" width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M10 12L6 8L10 4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <svg v-else width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M6 12L10 8L6 4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
        <button class="btn-icon" @click="closeSidebar" title="关闭">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M12 4L4 12M4 4L12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- 侧边栏内容 -->
    <div v-if="!isCollapsed" class="sidebar-content">
      <div class="content-section">
        <h4>快速操作</h4>
        <button class="btn-primary">发布新内容</button>
        <button class="btn-secondary">内容管理</button>
      </div>

      <div class="content-section">
        <h4>功能</h4>
        <ul class="feature-list">
          <li>内容编辑</li>
          <li>图片上传</li>
          <li>标签建议</li>
          <li>发布历史</li>
        </ul>
      </div>

      <div class="content-section">
        <h4>状态</h4>
        <div class="status-info">
          <span class="status-dot"></span>
          <span>已就绪</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.xhs-sidebar {
  position: fixed;
  top: 0;
  right: 0;
  width: 360px;
  height: 100vh;
  background: #ffffff;
  box-shadow: -2px 0 12px rgba(0, 0, 0, 0.1);
  z-index: 2147483647;
  display: flex;
  flex-direction: column;
  transition: transform 0.3s ease;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.xhs-sidebar.collapsed {
  width: 60px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid #e8e8e8;
  background: #fff;
  min-height: 56px;
}

.sidebar-title h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.xhs-sidebar.collapsed .sidebar-title {
  display: none;
}

.sidebar-controls {
  display: flex;
  gap: 8px;
}

.btn-icon {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  transition: all 0.2s;
}

.btn-icon:hover {
  background: #f5f5f5;
  color: #333;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.content-section {
  margin-bottom: 24px;
}

.content-section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.btn-primary {
  width: 100%;
  padding: 10px 16px;
  background: #ff2442;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  margin-bottom: 8px;
  transition: background 0.2s;
}

.btn-primary:hover {
  background: #e01e3a;
}

.btn-secondary {
  width: 100%;
  padding: 10px 16px;
  background: #f5f5f5;
  color: #333;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-secondary:hover {
  background: #e8e8e8;
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.feature-list li {
  padding: 8px 0;
  color: #666;
  font-size: 14px;
  border-bottom: 1px solid #f5f5f5;
}

.feature-list li:last-child {
  border-bottom: none;
}

.status-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #666;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #52c41a;
  display: inline-block;
}

/* 滚动条样式 */
.sidebar-content::-webkit-scrollbar {
  width: 6px;
}

.sidebar-content::-webkit-scrollbar-track {
  background: #f5f5f5;
}

.sidebar-content::-webkit-scrollbar-thumb {
  background: #d9d9d9;
  border-radius: 3px;
}

.sidebar-content::-webkit-scrollbar-thumb:hover {
  background: #bfbfbf;
}
</style>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useSidebar } from './composables/useSidebar'
import { usePublish } from './composables/usePublish'
import SidebarHeader from './components/SidebarHeader.vue'
import CollapsibleCard from './components/CollapsibleCard.vue'
import PublishSection from './components/PublishSection.vue'
import AISection from './components/AISection.vue'
import TipsSection from './components/TipsSection.vue'

const { isVisible, isCollapsed, closeSidebar } = useSidebar()
const {
  contentText,
  isPublishing,
  publishStatus,
  publishMessage,
  initApiUrl,
  clearContent,
  publishContent,
} = usePublish()

// 初始化 API URL
onMounted(async () => {
  await initApiUrl()
})
</script>

<template>
  <div v-if="isVisible" class="xhs-sidebar" :class="{ collapsed: isCollapsed }">
    <!-- 红色头部 -->
    <SidebarHeader @close="closeSidebar" />

    <!-- 侧边栏内容 -->
    <div v-if="!isCollapsed" class="sidebar-content">
      <!-- 发布内容区块 -->
      <CollapsibleCard title="发布内容">
        <template #icon>
          <svg class="card-icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path
              d="M8 0L10.163 5.527L16 6.292L12 10.146L12.944 16L8 13.236L3.056 16L4 10.146L0 6.292L5.837 5.527L8 0Z"
              fill="#ff2442"
            />
          </svg>
        </template>
        <PublishSection
          :content-text="contentText"
          :is-publishing="isPublishing"
          :publish-status="publishStatus"
          :publish-message="publishMessage"
          @update:content-text="contentText = $event"
          @publish="publishContent"
          @clear="clearContent"
        />
      </CollapsibleCard>

      <!-- AI仿写内容区块 -->
      <CollapsibleCard title="AI 仿写内容" badge="AI">
        <template #icon>
          <svg class="card-icon ai-icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="6" fill="#8B5CF6" />
            <circle cx="6" cy="6" r="1.5" fill="white" />
            <circle cx="10" cy="6" r="1.5" fill="white" />
            <path
              d="M6 10C6 10 7 11 8 11C9 11 10 10 10 10"
              stroke="white"
              stroke-width="1.5"
              stroke-linecap="round"
            />
          </svg>
        </template>
        <AISection />
      </CollapsibleCard>

      <!-- 使用小贴士区块 -->
      <CollapsibleCard title="使用小贴士">
        <template #icon>
          <svg class="card-icon tips-icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path
              d="M8 1V3M8 13V15M15 8H13M3 8H1M13.364 2.636L11.95 4.05M4.05 11.95L2.636 13.364M13.364 13.364L11.95 11.95M4.05 4.05L2.636 2.636"
              stroke="#FFC107"
              stroke-width="1.5"
              stroke-linecap="round"
            />
            <circle cx="8" cy="8" r="3" stroke="#FFC107" stroke-width="1.5" />
          </svg>
        </template>
        <TipsSection />
      </CollapsibleCard>
    </div>
  </div>
</template>

<style scoped>
.xhs-sidebar {
  position: fixed;
  top: 0;
  right: 0;
  width: 400px;
  height: 100vh;
  background: #fff5f5;
  box-shadow: -2px 0 12px rgba(0, 0, 0, 0.1);
  z-index: 2147483647;
  display: flex;
  flex-direction: column;
  transition: transform 0.3s ease;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    sans-serif;
}

.xhs-sidebar.collapsed {
  width: 60px;
}

/* 内容区域 */
.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #fff5f5;
}

/* 图标样式 */
.card-icon {
  flex-shrink: 0;
}

.ai-icon {
  color: #8b5cf6;
}

.tips-icon {
  color: #ffc107;
}

/* 滚动条样式 */
.sidebar-content::-webkit-scrollbar {
  width: 6px;
}

.sidebar-content::-webkit-scrollbar-track {
  background: #fff5f5;
}

.sidebar-content::-webkit-scrollbar-thumb {
  background: #ffd6d6;
  border-radius: 3px;
}

.sidebar-content::-webkit-scrollbar-thumb:hover {
  background: #ffb3b3;
}
</style>

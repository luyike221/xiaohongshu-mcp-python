<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  title: string
  badge?: string
  defaultCollapsed?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  defaultCollapsed: false,
})

const isCollapsed = ref(props.defaultCollapsed)

const toggle = () => {
  isCollapsed.value = !isCollapsed.value
}
</script>

<template>
  <div class="content-card">
    <div class="card-header" @click="toggle">
      <div class="card-title">
        <slot name="icon" />
        <span>{{ title }}</span>
        <span v-if="badge" class="ai-badge">{{ badge }}</span>
      </div>
      <svg
        class="collapse-icon"
        :class="{ rotated: isCollapsed }"
        width="12"
        height="12"
        viewBox="0 0 12 12"
        fill="none"
      >
        <path d="M6 9L2 5H10L6 9Z" fill="#666" />
      </svg>
    </div>
    <div v-if="!isCollapsed" class="card-body">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.content-card {
  background: #fff;
  border-radius: 12px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  cursor: pointer;
  transition: background 0.2s;
  border-bottom: 1px solid #f5f5f5;
}

.card-header:hover {
  background: #fafafa;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

.card-icon {
  flex-shrink: 0;
}

.ai-badge {
  background: #8b5cf6;
  color: white;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 10px;
  font-weight: 500;
  margin-left: 4px;
}

.collapse-icon {
  transition: transform 0.3s ease;
  flex-shrink: 0;
}

.collapse-icon.rotated {
  transform: rotate(180deg);
}

.card-body {
  padding: 16px;
}
</style>

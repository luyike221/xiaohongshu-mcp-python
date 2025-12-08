<script setup lang="ts">
defineEmits<{
  close: []
}>()
</script>

<template>
  <div class="sidebar-header-red">
    <div class="header-content">
      <div class="header-icon">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <rect x="4" y="4" width="16" height="20" rx="2" fill="white" />
          <path
            d="M8 8h8M8 12h8M8 16h5"
            stroke="#ff2442"
            stroke-width="1.5"
            stroke-linecap="round"
          />
          <path
            d="M16 8l2-2M18 8l-2-2"
            stroke="#ff2442"
            stroke-width="1.5"
            stroke-linecap="round"
          />
        </svg>
      </div>
      <div class="header-text">
        <h1>小红书发布助手</h1>
        <p>让内容创作更简单、更高效</p>
      </div>
    </div>
    <button class="btn-close" @click="$emit('close')" title="关闭">
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path
          d="M15 5L5 15M5 5L15 15"
          stroke="white"
          stroke-width="2"
          stroke-linecap="round"
        />
      </svg>
    </button>
  </div>
</template>

<style scoped>
.sidebar-header-red {
  background: #ff2442;
  padding: 20px 16px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  position: relative;
}

.header-content {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex: 1;
}

.header-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.header-text {
  flex: 1;
}

.header-text h1 {
  margin: 0 0 6px 0;
  font-size: 20px;
  font-weight: 600;
  color: white;
  line-height: 1.3;
}

.header-text p {
  margin: 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.4;
}

.btn-close {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  transition: background 0.2s;
  flex-shrink: 0;
}

.btn-close:hover {
  background: rgba(255, 255, 255, 0.2);
}
</style>

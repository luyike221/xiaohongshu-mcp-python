<script setup lang="ts">
import { computed } from 'vue'
import type { PublishStatus } from '../types'
import { MAX_CONTENT_LENGTH } from '../constants'

interface Props {
  contentText: string
  isPublishing: boolean
  publishStatus: PublishStatus
  publishMessage: string
}

interface Emits {
  (e: 'update:contentText', value: string): void
  (e: 'publish'): void
  (e: 'clear'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const charCount = computed(() => props.contentText.length)

const handleInput = (event: Event) => {
  const target = event.target as HTMLTextAreaElement
  emit('update:contentText', target.value)
}
</script>

<template>
  <div>
    <label class="input-label">内容输入框</label>
    <textarea
      :value="contentText"
      @input="handleInput"
      class="content-input"
      placeholder="在这里输入你想发布的内容..."
      :maxlength="MAX_CONTENT_LENGTH"
      rows="8"
    ></textarea>
    <div class="support-features">
      <span class="support-label">支持:</span>
      <span class="feature-item">· 文字描述</span>
      <span class="feature-item">· 话题标签 #</span>
      <span class="feature-item">· 表情符号 😊</span>
    </div>
    <div class="char-counter">{{ charCount }}/{{ MAX_CONTENT_LENGTH }}字</div>

    <!-- 发布状态提示 -->
    <div v-if="publishStatus !== 'idle'" class="publish-status" :class="publishStatus">
      <span v-if="publishStatus === 'success'">✅</span>
      <span v-else-if="publishStatus === 'error'">❌</span>
      <span>{{ publishMessage }}</span>
    </div>

    <div class="action-buttons">
      <button class="btn-clear" @click="$emit('clear')" :disabled="isPublishing">清空</button>
      <button class="btn-publish" @click="$emit('publish')" :disabled="isPublishing">
        <span v-if="isPublishing">发布中...</span>
        <span v-else>发布</span>
        <svg v-if="!isPublishing" width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path
            d="M2 8L14 8M10 4L14 8L10 12"
            stroke="white"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
        <svg v-else class="spinner" width="16" height="16" viewBox="0 0 16 16" fill="none">
          <circle
            cx="8"
            cy="8"
            r="7"
            stroke="white"
            stroke-width="2"
            stroke-opacity="0.3"
            fill="none"
          />
          <path
            d="M8 1 A7 7 0 0 1 15 8"
            stroke="white"
            stroke-width="2"
            fill="none"
            stroke-linecap="round"
          />
        </svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.input-label {
  display: block;
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
  font-weight: 500;
}

.content-input {
  width: 100%;
  min-height: 120px;
  padding: 12px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  background: #fff;
  color: #333;
  line-height: 1.6;
  box-sizing: border-box;
}

.content-input:focus {
  outline: none;
  border-color: #ff2442;
  box-shadow: 0 0 0 2px rgba(255, 36, 66, 0.1);
}

.content-input::placeholder {
  color: #999;
}

.support-features {
  margin-top: 10px;
  font-size: 12px;
  color: #666;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.support-label {
  font-weight: 500;
}

.feature-item {
  color: #888;
}

.char-counter {
  text-align: right;
  font-size: 12px;
  color: #999;
  margin-top: 8px;
  margin-bottom: 12px;
}

.publish-status {
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 13px;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.publish-status.success {
  background: #f0f9ff;
  color: #059669;
  border: 1px solid #a7f3d0;
}

.publish-status.error {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.btn-clear {
  flex: 1;
  padding: 10px 16px;
  background: white;
  color: #ff2442;
  border: 1px solid #ff2442;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-clear:hover {
  background: #fff5f5;
}

.btn-publish {
  flex: 2;
  padding: 10px 16px;
  background: #ff2442;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: background 0.2s;
}

.btn-publish:hover:not(:disabled) {
  background: #e01e3a;
}

.btn-publish:disabled,
.btn-clear:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>

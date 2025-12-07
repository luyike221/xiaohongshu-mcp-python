<script setup lang="ts">
import { ref } from 'vue'

const settings = ref({
  autoSave: true,
  theme: 'light'
})

const saveSettings = async () => {
  await chrome.storage.local.set({ settings: settings.value })
  alert('设置已保存')
}
</script>

<template>
  <div class="options">
    <h1>小红书发布助手 - 设置</h1>
    <div class="setting-item">
      <label>
        <input type="checkbox" v-model="settings.autoSave" />
        自动保存
      </label>
    </div>
    <div class="setting-item">
      <label>
        主题：
        <select v-model="settings.theme">
          <option value="light">浅色</option>
          <option value="dark">深色</option>
        </select>
      </label>
    </div>
    <button @click="saveSettings">保存设置</button>
  </div>
</template>

<style scoped>
.options {
  width: 500px;
  padding: 20px;
}

.setting-item {
  margin: 15px 0;
}

button {
  margin-top: 20px;
  padding: 8px 16px;
}
</style>

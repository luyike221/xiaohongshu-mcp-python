import type { PlasmoCSConfig } from "plasmo"

// Plasmo Content Script 配置
// 注意：对于 content.vue，Plasmo 会自动处理，这个配置文件主要用于非 Vue 的 content script
export const config: PlasmoCSConfig = {
  matches: ["<all_urls>"],
  css: ["src/content.css"]
}

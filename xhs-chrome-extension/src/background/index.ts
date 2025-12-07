// 监听扩展安装
chrome.runtime.onInstalled.addListener(() => {
  console.log('小红书发布助手扩展已安装')
})

// 存储已加载 content script 的标签页
const loadedTabs = new Set<number>()

// 监听来自 content script 的消息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getData') {
    sendResponse({ data: '来自后台的数据' })
  } else if (request.action === 'contentScriptReady') {
    if (sender.tab?.id) {
      loadedTabs.add(sender.tab.id)
      console.log(`Content script 已在标签页 ${sender.tab.id} 加载`)
    }
    sendResponse({ status: 'ok' })
  }
  return true
})

// 监听标签页更新，清除已加载标记（页面刷新后需要重新标记）
chrome.tabs.onUpdated.addListener((tabId, changeInfo) => {
  if (changeInfo.status === 'loading') {
    loadedTabs.delete(tabId)
  }
})

// 监听扩展图标点击，切换侧边栏显示/隐藏
chrome.action.onClicked.addListener(async (tab) => {
  if (!tab.id) return
  
  // 检查是否是特殊页面（无法注入 content script）
  if (tab.url?.startsWith('chrome://') || tab.url?.startsWith('chrome-extension://') || tab.url?.startsWith('edge://')) {
    console.warn('当前页面不支持 content script:', tab.url)
    return
  }
  
  // 向当前标签页的 content script 发送消息
  try {
    await chrome.tabs.sendMessage(tab.id, { action: 'toggleSidebar' })
    console.log('已发送切换侧边栏消息')
  } catch (error) {
    // 如果发送消息失败，可能是因为 content script 还未加载
    console.warn('发送消息失败，content script 可能未加载:', error)
    console.log('提示：请刷新页面以确保 content script 正确加载')
  }
})

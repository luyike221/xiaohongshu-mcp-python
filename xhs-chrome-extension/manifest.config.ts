import { defineManifest } from '@crxjs/vite-plugin'
import packageJson from './package.json'

const { version, name, description } = packageJson

export default defineManifest({
  manifest_version: 3,
  name: name,
  description: description,
  version: version,
  
  // 权限配置
  permissions: ['tabs', 'scripting', 'storage'],
  host_permissions: ['<all_urls>'],
  
  // 图标配置
  icons: {
    16: 'src/assets/icon-16.png',
    48: 'src/assets/icon-48.png',
    128: 'src/assets/icon-128.png'
  },
  
  // 弹出窗口（通过右键菜单访问）
  action: {
    // 不设置 default_popup，让点击图标触发 onClicked 事件来切换侧边栏
    // 用户可以通过右键菜单 → "检查弹出内容" 来打开 popup
  },
  
  // 后台服务
  background: {
    service_worker: 'src/background/index.ts',
    type: 'module'
  },
  
  // 内容脚本
  content_scripts: [
    {
      matches: ['<all_urls>'],
      js: ['src/content/index.ts'],
      run_at: 'document_end' // 在 DOM 加载完成后运行
    }
  ],
  
  // 选项页面
  options_page: 'src/options/index.html'
})

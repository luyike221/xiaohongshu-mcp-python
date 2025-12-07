# 小红书发布助手 Chrome 扩展

基于 Vue3 + Vite + TypeScript 开发的 Chrome 浏览器扩展，用于辅助小红书内容发布。

## 技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **Vite** - 下一代前端构建工具
- **TypeScript** - JavaScript 的超集
- **Pinia** - Vue 状态管理
- **Vue Router** - Vue 路由管理
- **@crxjs/vite-plugin** - Chrome 扩展开发插件

## 项目结构

```
xhs-chrome-extension/
├── src/
│   ├── popup/              # 弹出窗口
│   │   ├── index.html
│   │   ├── index.ts
│   │   └── App.vue
│   ├── background/         # 后台服务
│   │   └── index.ts
│   ├── content/           # 内容脚本
│   │   └── index.ts
│   ├── options/           # 选项页面
│   │   ├── index.html
│   │   ├── index.ts
│   │   └── App.vue
│   ├── components/        # 共享组件
│   ├── stores/           # Pinia状态管理
│   └── assets/           # 静态资源
├── manifest.config.ts
├── vite.config.ts
└── package.json
```

## 开发指南

### 1. 安装依赖

```bash
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

### 3. 加载扩展到 Chrome

1. 打开 Chrome 浏览器，访问 `chrome://extensions/`
2. 开启右上角的 **"开发者模式"**
3. 点击 **"加载已解压的扩展程序"**
4. 选择项目的 `dist` 文件夹

### 4. 调试方法

#### 调试 Popup 页面
- 右键点击扩展图标 → **"检查弹出内容"**
- 或者点击扩展图标后按 `F12`

#### 调试 Background Service Worker
- 在 `chrome://extensions/` 页面
- 找到你的扩展，点击 **"service worker"** 链接

#### 调试 Content Script
- 在目标网页上按 `F12` 打开开发者工具
- 在 Console 中可以看到 content script 的日志

### 5. 构建生产版本

```bash
npm run build
```

构建完成后，`dist` 文件夹包含可发布的扩展文件。

## 功能特性

- [ ] 小红书内容发布辅助
- [ ] 内容预览和编辑
- [ ] 图片上传和管理
- [ ] 标签建议
- [ ] 发布历史记录

## 许可证

MIT

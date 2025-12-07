# 小红书发布助手 Chrome 扩展

基于 **Plasmo** + **Vue 3** + **TypeScript** 开发的 Chrome 浏览器扩展，用于辅助小红书内容发布。

> 📚 **新手入门？** 查看 [Plasmo 新手教程](./PLASMO_TUTORIAL.md) - 从零开始学习 Plasmo 框架

## 技术栈

- **Plasmo** - 浏览器扩展开发框架
- **Vue 3** - 渐进式 JavaScript 框架
- **TypeScript** - JavaScript 的超集
- **Pinia** - Vue 状态管理（可选）

## 项目结构

```
xhs-chrome-extension/
├── src/
│   ├── content.vue          # Content Script UI (右侧边栏)
│   ├── popup.vue            # Popup 弹出窗口
│   ├── background.ts        # Background Service Worker
│   ├── options.vue          # 选项设置页面
│   ├── content.css          # Content Script 样式
│   └── assets/              # 图标和静态资源
│       ├── icon-16.png
│       ├── icon-48.png
│       └── icon-128.png
├── plasmo.config.ts         # Plasmo 配置文件
├── package.json             # 项目配置和依赖
├── tsconfig.json            # TypeScript 配置
└── README.md                # 项目说明
```

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

开发服务器会自动：
- 监听文件变化
- 重新构建扩展
- 输出构建文件到 `build/chrome-mv3-dev` 目录

### 3. 加载扩展到 Chrome

1. 打开 Chrome 浏览器，访问 `chrome://extensions/`
2. 开启右上角的 **"开发者模式"**
3. 点击 **"加载已解压的扩展程序"**
4. 选择项目的 `build/chrome-mv3-dev` 文件夹

### 4. 使用扩展

- **侧边栏**: 访问任意网页，侧边栏会自动显示在页面右侧
- **切换侧边栏**: 点击浏览器工具栏中的扩展图标
- **Popup**: 右键扩展图标 → "检查弹出内容"
- **设置**: 右键扩展图标 → "选项"

## 开发指南

### 调试方法

#### 调试 Popup 页面
- 右键点击扩展图标 → **"检查弹出内容"**

#### 调试 Background Service Worker
- 在 `chrome://extensions/` 页面
- 找到你的扩展，点击 **"service worker"** 链接

#### 调试 Content Script (侧边栏)
- 在目标网页上按 `F12` 打开开发者工具
- 在 Console 中可以看到 content script 的日志
- 侧边栏使用 Shadow DOM，样式已自动隔离

### 构建生产版本

```bash
npm run build
```

构建完成后，扩展文件在 `build/chrome-mv3-prod` 目录。

### 打包扩展

```bash
npm run package
```

会生成 `.zip` 文件，可直接提交到 Chrome Web Store。

## 功能特性

- ✅ 右侧边栏 UI（使用 Plasmo Content Script UI）
- ✅ 侧边栏展开/收起功能
- ✅ Popup 控制面板
- ✅ Background Service Worker
- ✅ 选项设置页面
- ✅ 热重载开发体验

## Plasmo 优势

1. **约定优于配置**: 文件结构清晰，减少配置文件
2. **自动 Shadow DOM**: Content Script UI 自动使用 Shadow DOM，避免样式冲突
3. **更好的热重载**: 开发体验更流畅
4. **类型安全**: 完整的 TypeScript 支持
5. **支持 src 目录**: 符合前端项目最佳实践

## 文件说明

- `src/content.vue`: 右侧边栏组件，使用 Plasmo 的 Content Script UI 功能
- `src/popup.vue`: 扩展图标点击后的弹出窗口
- `src/background.ts`: 后台服务，处理扩展逻辑
- `src/options.vue`: 扩展设置页面
- `src/content.css`: Content Script 样式文件
- `plasmo.config.ts`: Plasmo 框架配置

## 许可证

MIT

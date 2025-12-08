# 小红书发布助手 Chrome 扩展

## 项目结构

```
src/
├── components/          # Vue 组件
│   ├── SidebarHeader.vue      # 侧边栏头部组件
│   ├── CollapsibleCard.vue    # 可折叠卡片组件
│   ├── PublishSection.vue      # 发布内容区块
│   ├── AISection.vue          # AI 仿写区块
│   └── TipsSection.vue        # 使用小贴士区块
├── composables/       # Vue Composition API 组合式函数
│   ├── useSidebar.ts          # 侧边栏状态管理
│   └── usePublish.ts           # 发布功能逻辑
├── services/          # 业务服务层
│   ├── api.ts                 # API 调用服务
│   └── storage.ts             # Chrome Storage 服务
├── types/             # TypeScript 类型定义
│   └── index.ts
├── constants/         # 常量配置
│   └── index.ts
├── background.ts      # Background Script
├── content.vue        # Content Script (主入口)
├── popup.vue          # Popup 页面
└── options.vue        # Options 页面
```

## 架构说明

### 组件化设计
- **SidebarHeader**: 独立的头部组件，负责显示标题和关闭按钮
- **CollapsibleCard**: 可复用的折叠卡片组件，支持图标插槽和徽章
- **功能区块组件**: PublishSection、AISection、TipsSection 各自独立

### 组合式函数 (Composables)
- **useSidebar**: 管理侧边栏的显示/隐藏、折叠状态
- **usePublish**: 处理发布相关的业务逻辑，包括内容输入、API 调用、状态管理

### 服务层 (Services)
- **api.ts**: 封装所有 API 调用，统一处理错误和响应
- **storage.ts**: 封装 Chrome Storage 操作，提供类型安全的数据存取

### 类型安全
- 所有类型定义集中在 `types/index.ts`
- 使用 TypeScript 严格模式，确保类型安全

### 常量管理
- 所有魔法数字和字符串提取到 `constants/index.ts`
- 便于维护和修改

## 开发指南

### 添加新功能
1. 在 `types/index.ts` 中定义相关类型
2. 在 `services/` 中添加相应的服务函数
3. 在 `composables/` 中创建或扩展组合式函数
4. 在 `components/` 中创建 UI 组件
5. 在主文件中组合使用

### 代码规范
- 使用 TypeScript 严格模式
- 组件使用 `<script setup>` 语法
- 样式使用 scoped CSS
- 遵循单一职责原则

## 技术栈

- Vue 3 (Composition API)
- TypeScript
- Plasmo Framework
- Chrome Extension API

# 问题排查指南

## 图标问题 ✅ 已解决

如果遇到 "No icon found" 警告：

```bash
python3 create_icon_for_plasmo.py
```

## TypeScript 配置问题

### 错误：`Cannot load file './tsconfig.base' from module 'plasmo'`

**解决方案：**

确保 `tsconfig.json` 中的 `extends` 使用正确的路径：

```json
{
  "extends": "plasmo/templates/tsconfig.base",
  ...
}
```

**不是：** `plasmo/tsconfig.base`  
**而是：** `plasmo/templates/tsconfig.base`

### 错误：`Failed to resolve '../../src/popup.vue'`

**可能的原因：**

1. **Vue 依赖未安装**
   ```bash
   pnpm add -D @vitejs/plugin-vue vue-tsc
   ```

2. **文件路径问题**
   - 确保文件在 `src/` 目录下
   - 确保文件名正确（popup.vue, content.vue 等）

3. **重新安装依赖**
   ```bash
   rm -rf node_modules pnpm-lock.yaml
   pnpm install
   ```

## 其他常见问题

### 构建失败

1. **清理构建缓存**
   ```bash
   rm -rf .plasmo build
   pnpm dev
   ```

2. **检查依赖**
   ```bash
   pnpm install
   ```

3. **使用详细模式**
   ```bash
   pnpm dev --verbose
   ```

### Vue 组件不工作

确保安装了必要的依赖：

```bash
pnpm add vue
pnpm add -D @vitejs/plugin-vue vue-tsc
```

### 热重载不工作

1. 在扩展管理页面点击扩展的 **"刷新"** 按钮
2. 或重新加载扩展
3. 某些修改（如 manifest）需要完全重新加载

## 获取帮助

- 查看 [Plasmo 官方文档](https://docs.plasmo.com/)
- 查看 [完整教程](./PLASMO_TUTORIAL.md)
- 查看 [快速开始](./QUICK_START.md)

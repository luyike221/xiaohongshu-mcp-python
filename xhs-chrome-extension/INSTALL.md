# 安装指南

## 快速开始

### 1. 安装依赖

```bash
cd xhs-chrome-extension
npm install
```

### 2. 添加图标文件

在 `src/assets/` 目录下添加以下图标文件（PNG 格式）：
- `icon-16.png` (16x16 像素)
- `icon-48.png` (48x48 像素)
- `icon-128.png` (128x128 像素)

如果没有图标，可以暂时使用占位图片，或者从网上下载免费的图标资源。

### 3. 启动开发服务器

```bash
npm run dev
```

这将启动 Vite 开发服务器，并自动构建扩展文件到 `dist` 目录。

### 4. 加载扩展到 Chrome

1. 打开 Chrome 浏览器
2. 访问 `chrome://extensions/`
3. 开启右上角的 **"开发者模式"**
4. 点击 **"加载已解压的扩展程序"**
5. 选择项目的 `dist` 文件夹

### 5. 使用扩展

- 点击浏览器工具栏中的扩展图标，打开 Popup 页面
- 右键点击扩展图标 → **"选项"**，打开设置页面
- 在任意网页上，Content Script 会自动注入

## 开发提示

### 热更新

- Popup 页面：修改后需要关闭并重新打开 Popup
- Content Script：修改后需要刷新网页
- Background Service Worker：会自动重启

### 调试

- **Popup**: 右键扩展图标 → "检查弹出内容"
- **Background**: 在 `chrome://extensions/` 页面点击 "service worker"
- **Content Script**: 在网页上按 F12，在 Console 中查看日志

### 构建生产版本

```bash
npm run build
```

构建完成后，`dist` 文件夹包含可发布的扩展文件。

## 常见问题

### 1. 依赖安装失败

如果遇到依赖安装问题，可以尝试：
```bash
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### 2. 扩展无法加载

- 确保已开启开发者模式
- 检查 `dist` 文件夹是否存在
- 查看 Chrome 扩展页面的错误信息

### 3. TypeScript 类型错误

确保已安装 `@types/chrome`：
```bash
npm install -D @types/chrome
```

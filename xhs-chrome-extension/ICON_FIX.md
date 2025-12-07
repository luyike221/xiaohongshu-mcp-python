# 图标问题修复指南

## 问题说明

Plasmo 框架需要在**根目录**的 `assets/` 目录中放置 `icon.png` 文件，而不是 `src/assets/`。

## 快速修复

### 方法 1: 使用修复脚本（推荐）

```bash
# 运行修复脚本
python3 create_icons_for_plasmo.py
```

这个脚本会：
1. 自动从 `src/assets/` 查找现有图标
2. 如果找到，复制到 `assets/icon.png`
3. 如果没找到，创建一个占位图标

### 方法 2: 手动复制

如果你确定 `src/assets/` 中有图标文件：

```bash
# 创建 assets 目录
mkdir -p assets

# 复制图标（使用最大的图标）
cp src/assets/icon-128.png assets/icon.png

# 或者如果有其他尺寸的图标
cp src/assets/icon-48.png assets/icon.png
```

### 方法 3: 使用原始图标生成脚本

如果你有原始图标文件：

```bash
# 1. 先运行原始脚本生成图标到 src/assets/
python3 create_icons_simple.py

# 2. 然后运行 Plasmo 修复脚本
python3 create_icons_for_plasmo.py
```

## Plasmo 图标要求

- **位置**: `assets/icon.png`（项目根目录）
- **格式**: PNG
- **推荐尺寸**: 512x512 或更大
- **自动生成**: Plasmo 会自动从这个文件生成 16x16, 48x48, 128x128 等尺寸

## 验证

修复后，运行：

```bash
pnpm dev
```

如果不再出现 "No icon found" 警告，说明修复成功！

## 常见问题

**Q: 为什么图标要在根目录？**

A: 这是 Plasmo 框架的约定，它会在构建时从根目录的 `assets/` 目录读取资源文件。

**Q: 可以同时保留 src/assets 中的图标吗？**

A: 可以，但 Plasmo 只会使用根目录 `assets/icon.png` 中的图标。

**Q: 图标尺寸有要求吗？**

A: 推荐使用 512x512 或更大的 PNG 文件，Plasmo 会自动生成所需的小尺寸版本。

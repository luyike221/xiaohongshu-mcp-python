# 图标文件说明

## 图标文件位置

Chrome 扩展需要三个不同尺寸的图标文件，必须放在以下位置：

```
src/assets/
├── icon-16.png   (16x16 像素) - 用于扩展工具栏
├── icon-48.png   (48x48 像素) - 用于扩展管理页面
└── icon-128.png (128x128 像素) - 用于 Chrome 网上应用店
```

## 如何创建图标

### 方法 1: 使用 Python + Pillow（推荐）

1. 确保已安装 Pillow：
   ```bash
   pip3 install Pillow
   ```

2. 运行脚本：
   ```bash
   python3 create_icons.py
   ```

   脚本会从源图片 `/data/project/ai_project/yy_运营/xhs_小红书运营/z-images/output/generated_20251207_224402_177423.png` 创建三个尺寸的图标。

### 方法 2: 手动创建

1. 使用图片编辑工具（如 GIMP、Photoshop、在线工具）打开源图片
2. 分别调整为 16x16、48x48、128x128 像素
3. 保存为 PNG 格式
4. 放到 `src/assets/` 目录下，命名为 `icon-16.png`、`icon-48.png`、`icon-128.png`

### 方法 3: 使用在线工具

访问在线图片调整工具（如 https://www.iloveimg.com/resize-image），上传源图片，分别调整为三个尺寸，然后下载并放到 `src/assets/` 目录。

## 注意事项

- 图标必须是 PNG 格式
- 图标应该是正方形（宽高相等）
- 建议使用透明背景或白色背景
- 图标应该清晰可见，即使在 16x16 的小尺寸下也能识别

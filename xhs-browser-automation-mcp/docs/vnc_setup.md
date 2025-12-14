# VNC 远程桌面配置指南

## 什么是 VNC？

VNC（Virtual Network Computing）允许你在远程服务器上运行图形界面应用，并通过网络在本地查看和操作。适合调试浏览器自动化时查看浏览器窗口。

## 快速开始

### 1. 在服务器上安装 VNC

```bash
sudo apt update
sudo apt install -y tigervnc-standalone-server
```

### 2. 设置密码并启动 VNC

```bash
# 设置 VNC 密码
vncpasswd

# 启动 VNC 服务器（显示编号 :1，分辨率 1920x1080）
vncserver :1 -geometry 1920x1080 -depth 24 -localhost no
```

### 3. 在本地连接

**步骤 1：下载并安装 VNC 客户端**

- **Windows/Mac/Linux**: [TigerVNC Viewer](https://github.com/TigerVNC/tigervnc/releases)
- **Mac**: [RealVNC Viewer](https://www.realvnc.com/en/connect/download/viewer/)

**步骤 2：连接 VNC**

- 打开 VNC 客户端
- 连接地址：`服务器IP:5901`（例如：`192.168.1.100:5901`）
- 输入之前设置的 VNC 密码

**当前服务器连接信息：**
- 服务器 IP: `192.168.56.2`
- VNC 端口: `5901`
- 连接地址: `192.168.56.2:5901`

**端口说明：**
- 显示 `:1` 对应端口 `5901`
- 显示 `:2` 对应端口 `5902`
- 端口计算：5900 + 显示编号

### 4. 在 VNC 中使用浏览器自动化

**⚠️ 重要：必须在 VNC 会话的终端中运行，而不是在 SSH 终端中！**

**步骤：**

1. **在 VNC 客户端中打开终端**（在 VNC 桌面中右键或使用菜单打开终端）

2. **在 VNC 会话的终端中运行：**

```bash
# 设置 DISPLAY 环境变量（脚本会自动检测，但手动设置更保险）
export DISPLAY=:1

# 运行浏览器自动化
cd /data/project/ai_project/yy_运营/xhs_小红书运营/xhs-browser-automation-mcp
./run.sh dev
```

3. **浏览器窗口会显示在 VNC 桌面中**，你可以通过 VNC 客户端查看和操作。

**常见问题：**
- ❌ 在 SSH 终端中运行 → 浏览器窗口不会显示在 VNC 中
- ✅ 在 VNC 会话的终端中运行 → 浏览器窗口会显示在 VNC 桌面中

## 常见问题

### 浏览器窗口不显示

**问题：** 在 SSH 终端中运行，浏览器窗口不显示在 VNC 中

**解决方案：**
1. **确保在 VNC 会话的终端中运行**（在 VNC 桌面中打开终端，不要用 SSH 终端）
2. 检查 DISPLAY 环境变量：`echo $DISPLAY`（应该是 `:1`）
3. 如果 DISPLAY 未设置，运行：`export DISPLAY=:1`
4. 然后重新运行 `./run.sh dev`

### 连接后黑屏

```bash
# 检查 VNC 服务器是否运行
vncserver -list

# 检查 DISPLAY 环境变量
echo $DISPLAY

# 重新启动 VNC 服务器
vncserver -kill :1
vncserver :1 -geometry 1920x1080 -depth 24 -localhost no
```

### 无法连接

检查防火墙是否允许 VNC 端口：
```bash
# 在服务器上检查防火墙
sudo ufw status
# 如果需要，开放端口
sudo ufw allow 5901/tcp
```

## 总结

VNC 适合在远程服务器上调试浏览器自动化时查看浏览器窗口。对于生产环境，建议使用无头模式。

**完整流程：**
1. 服务器：安装 VNC → 设置密码 → 启动 VNC
2. 本地：打开 VNC 客户端（如 TigerVNC Viewer）→ 连接到 `192.168.56.2:5901` → 输入 VNC 密码
3. VNC 中：设置 `DISPLAY=:1` → 运行 `./run.sh dev`

**当前服务器信息：**
- 服务器 IP: `192.168.56.2`
- VNC 端口: `5901`
- 连接地址: `192.168.56.2:5901`

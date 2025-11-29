# XHS Content Generator MCP

基于 FastMCP 的小红书内容生成 MCP 服务。

## 功能特性

- 🎨 小红书内容生成
- 📝 支持多种内容类型（笔记、标题、描述等）
- 🔌 基于 FastMCP 框架
- 🚀 易于扩展和集成

## 项目结构

```
xhs-content-generator-mcp/
├── src/
│   └── xhs_content_generator_mcp/
│       ├── __init__.py
│       └── main.py
├── pyproject.toml
└── README.md
```

## 安装

使用 `uv` 进行项目管理：

```bash
# 安装依赖
uv sync

# 运行服务
uv run python -m xhs_content_generator_mcp.main
```

## 使用

### 启动服务

```bash
# 默认端口 8000
uv run python -m xhs_content_generator_mcp.main

# 指定端口
uv run python -m xhs_content_generator_mcp.main 8080
```

### 在 MCP Inspector 中测试

1. 启动服务后，打开 MCP Inspector
2. 连接到服务：`http://localhost:8000`
3. 在 Tools 标签页中测试 `generate_content` 工具

## 开发

### 添加新功能

1. 在 `main.py` 中添加新的 `@mcp.tool()` 装饰的函数
2. 实现具体的业务逻辑
3. 重启服务测试

## 许可证

MIT


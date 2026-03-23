# OpenClaw 接入 MCP 与编写 Skills 指南

本文档面向本仓库使用者，目标是帮助你在 OpenClaw 中完成两件事：

1. 接入外部 MCP 服务（例如 `xhs-browser-automation-mcp`）
2. 编写可复用的 Skills，让 Agent 更稳定地调用工具

---

## 1. 先理解两层职责

- **MCP 接入层（底层）**：负责把外部能力接进 OpenClaw（`mcp.servers`）。
- **Skills 指导层（上层）**：负责告诉模型“什么时候、如何、按什么规则”使用这些工具（`SKILL.md`）。

建议流程始终是：**先接入 MCP，再写 Skill 约束调用策略**。

---

## 2. 接入 MCP（OpenClaw 侧）

### 2.1 启动你的 MCP 服务

以 `xhs-browser-automation-mcp` 为例，先保证服务可用（示例端口 `8000`）：

```bash
cd xhs-browser-automation-mcp
uv sync
uv run playwright install chromium
uv run python -m xiaohongshu_mcp_python.main
```

确认服务端点可访问：

- `http://127.0.0.1:8002/mcp`

### 2.2 在 OpenClaw 中注册 MCP server

当前实践建议使用 stdio 方式接入。  
如果你的 MCP 是 HTTP 服务，可用 `mcp-remote` 做桥接：

```bash
pnpm openclaw mcp set xhs "{\"command\":\"npx\",\"args\":[\"-y\",\"mcp-remote@latest\",\"http://127.0.0.1:8002/mcp\"]}"
```

查看是否写入成功：

```bash
pnpm openclaw mcp list
pnpm openclaw mcp show xhs --json
```

重启网关：

```bash
pnpm  openclaw gateway restart
```

### 2.3 等价配置写法（`~/.openclaw/openclaw.json`）

```json5
{
  mcp: {
    servers: {
      xhs: {
        command: "npx",
        args: ["-y", "mcp-remote@latest", "http://127.0.0.1:8000/mcp"],
      },
    },
  },
}
```

---

## 3. 编写 Skills（让 Agent 会正确用工具）

### 3.1 Skill 放在哪

OpenClaw 会从这些位置加载技能（优先级从高到低）：

1. `<workspace>/skills`
2. `~/.openclaw/skills`
3. OpenClaw 内置 bundled skills

如果你在当前项目做定制，推荐放在：

- `openclaw/skills/<你的skill名>/SKILL.md`（用于仓库内协作）

### 3.2 最小可用 `SKILL.md` 模板

```markdown
---
name: xhs-publisher
description: 使用小红书 MCP 工具完成登录检查、图文发布、视频发布与内容查询。
metadata: { "openclaw": { "requires": { "bins": ["npx"] } } }
---

# 目标
你是小红书运营执行助手，优先保证安全、可追踪、可回滚。

# 工具使用顺序
1. 先检查登录状态；未登录先走登录流程。
2. 发布前校验参数：标题长度、图片/视频路径、标签格式。
3. 发布后返回结构化结果：是否成功、note_id、失败原因、重试建议。

# 发布策略
- 默认单次只发布 1 条，避免高频触发平台风控。
- 用户未明确要求时，不自动批量发布。
- 对包含敏感或风险内容的请求，先提示用户确认再执行。

# 错误处理
- 如果工具超时：最多重试 1 次，并给出手动排查步骤。
- 如果鉴权失效：明确提示重新登录，不盲目重试发布。
```

说明：

- `name` 建议全局唯一，避免与已有技能重名。
- `metadata.openclaw.requires` 可用于 gating（例如依赖 `npx`、环境变量等）。
- 指令尽量写成“可执行规则”，避免空泛描述。

### 3.3 在配置里启用或覆盖 Skill

`~/.openclaw/openclaw.json` 示例：

```json5
{
  skills: {
    entries: {
      "xhs-publisher": {
        enabled: true,
        env: {
          XHS_ENV: "production",
        },
        config: {
          maxPublishPerRun: 1,
        },
      },
    },
  },
}
```

---

## 4. 推荐联调顺序

1. 先单独验证 `xhs-browser-automation-mcp` 可工作
2. 再验证 OpenClaw `mcp list/show` 能看到 `xhs`
3. 新开会话，让 Agent 读到 Skill
4. 从“读操作”开始压测（登录状态、查询）再做“写操作”（发布）

---

## 5. 常见问题排查

### 问题 A：OpenClaw 看不到 MCP 工具

- 检查 `openclaw mcp show xhs --json` 是否存在
- 检查 `xhs-browser-automation-mcp` 是否仍在运行
- 检查 `npx` 在网关进程 PATH 中是否可用
- 重启 `openclaw gateway`

### 问题 B：Skill 写了但模型没有按规则执行

- 确认 Skill 文件名是 `SKILL.md`
- 确认 frontmatter 字段是单行可解析格式
- 确认 skill 已启用，且无同名高优先级覆盖
- 新开一个会话再测试（避免旧会话缓存）

### 问题 C：发布动作不稳定

- 先把 Skill 中策略改为“先检查登录再发布”
- 将一次任务拆成“生成内容 -> 人工确认 -> 发布”
- 降低并发与发布频率，避免平台风控

---

## 6. 一句话最佳实践

把 MCP 当作“连接层”，把 Skill 当作“操作手册层”：  
**连接先稳定，规则再收敛，最后再放自动化强度。**


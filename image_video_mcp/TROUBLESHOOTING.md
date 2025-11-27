# 故障排除指南

## 常见问题及解决方案

### 1. Resource Template URI 格式错误

**错误信息**:
```
Input should be a valid URL, relative URL without a base [type=url_parsing, input_value='negative_prompts://landscape']
```

**原因**: Resource Template 的 URI 必须使用标准的 `resource://` scheme 格式

**解决方案**: 
- ✅ 已修复：所有 Resource Template URI 已更新为 `resource://路径/{参数}` 格式
- 正确的格式示例：
  - `resource://styles/{style_name}` ✅
  - `resource://negative_prompts/{image_type}` ✅
  - `resource://sizes/{size_name}` ✅
- 错误的格式示例：
  - `styles://{style_name}` ❌
  - `negative_prompts://{image_type}` ❌

### 2. Session ID 错误

**错误信息**:
```
Error POSTing to endpoint (HTTP 400): Bad Request: No valid session ID provided
```

**可能原因**:
1. MCP Inspector 连接中断
2. 服务器重启导致 session 失效
3. 网络连接问题

**解决方案**:
1. **重新连接 MCP Inspector**:
   - 关闭当前的 Inspector 连接
   - 重新启动 Inspector
   - 重新连接到服务器

2. **重启服务器**:
   ```bash
   # 停止当前服务器（Ctrl+C）
   # 重新启动
   ./run.sh
   ```

3. **检查服务器状态**:
   ```bash
   # 检查服务器是否运行
   curl http://127.0.0.1:8003/mcp
   ```

4. **清理并重新连接**:
   - 在 Inspector 中断开连接
   - 等待几秒钟
   - 重新连接

### 3. SSE Stream 断开连接

**错误信息**:
```
SSE stream disconnected: TypeError: terminated
Failed to reconnect SSE stream: fetch failed
Maximum reconnection attempts (2) exceeded
```

**原因**: Server-Sent Events (SSE) 连接中断

**解决方案**:
1. **检查服务器是否运行**:
   ```bash
   ps aux | grep "python.*image_video_mcp"
   ```

2. **检查端口是否被占用**:
   ```bash
   netstat -tlnp | grep 8003
   # 或
   ss -tlnp | grep 8003
   ```

3. **重启服务器和 Inspector**:
   - 停止服务器
   - 停止 Inspector
   - 重新启动服务器
   - 重新启动 Inspector

### 4. Resource Template 无法访问

**错误信息**: 在 Inspector 中无法读取 Resource Template

**检查清单**:
1. ✅ 确保服务器已启动
2. ✅ 确保 Resource Template 已注册（查看服务器日志）
3. ✅ 使用正确的 URI 格式：`resource://路径/参数值`
4. ✅ 参数值必须有效（参考可用参数列表）

**示例**:
```python
# 正确
mcp.get_resource("resource://styles/anime")

# 错误
mcp.get_resource("styles://anime")  # 旧格式
mcp.get_resource("resource://styles")  # 缺少参数
```

### 5. 代码验证

**验证所有功能**:
```bash
cd /root/project/ai_project/yx_运营/xhs_小红书运营/image_video_mcp
uv run python -c "from src.image_video_mcp.main import mcp; print('✓ 验证成功')"
```

**预期输出**:
```
✓ 已注册 6 个 Resource 资源
✓ 已注册 8 个 Resource Template 模板
✓ 已注册 5 个 Prompt 模板
✓ 验证成功
```

## 🔍 调试步骤

### 步骤 1: 检查服务器日志

查看服务器启动日志，确认所有资源已注册：
```
已注册 6 个 Resource 资源
已注册 8 个 Resource Template 模板
已注册 5 个 Prompt 模板
```

### 步骤 2: 测试服务器连接

```bash
# 测试服务器是否响应
curl -v http://127.0.0.1:8003/mcp
```

### 步骤 3: 检查 Inspector 连接

1. 确保 Inspector 使用正确的传输方式：**HTTP/HTTPS**
2. 确保服务器地址正确：`http://127.0.0.1:8003/mcp`
3. 检查浏览器控制台是否有错误

### 步骤 4: 验证 Resource Template URI

确保所有 Resource Template 使用正确的 URI 格式：
- ✅ `resource://styles/{style_name}`
- ✅ `resource://negative_prompts/{image_type}`
- ✅ `resource://sizes/{size_name}`
- ✅ `resource://combined_config/{style_name}/{size_name}`
- ✅ `resource://generation_plan/{theme}/{style_name}/{size_name}`

## 📞 获取帮助

如果问题仍然存在：

1. **查看服务器日志**: 检查详细的错误信息
2. **检查 FastMCP 版本**: 确保使用最新版本
3. **查看文档**: 
   - [RESOURCE_TEMPLATES_USAGE.md](./RESOURCE_TEMPLATES_USAGE.md)
   - [RESOURCES_USAGE.md](./RESOURCES_USAGE.md)
   - [FastMCP 文档](https://fastmcp.wiki/zh/servers/resources)

## ✅ 已修复的问题

- ✅ Resource Template URI 格式错误（已全部修复为 `resource://` 格式）
- ✅ 代码中的 URI 引用错误（已修复）
- ✅ 函数签名错误（已移除不必要的 `async`）


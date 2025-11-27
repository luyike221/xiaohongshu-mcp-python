好的，我来详细讲解 Python 版本 FastMCP 的 resource templates：

## 一、核心概念

Resources 代表 MCP 客户端可以读取的数据或文件，resource templates 扩展了这一概念，允许客户端根据 URI 中传递的参数请求动态生成的资源。

**关键特点：**
- 只读访问（类似 REST API 的 GET）
- 支持静态和动态内容
- 使用装饰器 `@mcp.resource()` 定义

## 二、基础用法

### 1. 静态资源

```python
from fastmcp import FastMCP

mcp = FastMCP("My Server")

@mcp.resource("config://version")
def get_version() -> str:
    """返回应用版本"""
    return "2.0.1"

@mcp.resource("schema://main")
def get_schema() -> str:
    """数据库架构"""
    import sqlite3
    conn = sqlite3.connect("database.db")
    schema = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table'"
    ).fetchall()
    return "\n".join(sql[0] for sql in schema if sql[0])
```

### 2. 动态资源模板（带路径参数）

```python
@mcp.resource("users://{user_id}/profile")
def get_user_profile(user_id: str) -> str:
    """获取用户资料
    
    Args:
        user_id: 用户ID（从URI中提取）
    """
    # 从数据库或API获取用户数据
    user = fetch_user_from_db(user_id)
    return f"Name: {user.name}, Email: {user.email}"

@mcp.resource("files://{path}")
def read_file(path: str) -> str:
    """读取文件内容"""
    with open(f"/data/{path}", "r") as f:
        return f.read()
```

**重要规则：**
- URI 中的 `{参数名}` 必须与函数参数名完全匹配
- 所有路径参数都是**必需的**（不能有默认值）

## 三、高级 URI 模板语法

### 1. 多个路径参数

```python
@mcp.resource("repos://{owner}/{repo}/issues/{issue_id}")
def get_issue(owner: str, repo: str, issue_id: int) -> str:
    """获取 GitHub issue
    
    示例 URI: repos://pytorch/pytorch/issues/12345
    """
    return f"Issue #{issue_id} in {owner}/{repo}"
```

### 2. 通配符参数（捕获路径段）

FastMCP 支持通配符参数来构建类似 REST API 的 URL 模式：

```python
# 单个通配符（捕获一个路径段）
@mcp.resource("api://{version}/users/{*user_path}")
def get_user_resource(version: str, user_path: str) -> str:
    """
    匹配: api://v1/users/profile
         api://v1/users/settings
    user_path 会是: "profile" 或 "settings"
    """
    return f"API {version}: {user_path}"

# 贪婪通配符（捕获多个路径段）
@mcp.resource("files://{**file_path}")
def get_nested_file(file_path: str) -> str:
    """
    匹配: files://docs/guide.md
         files://docs/api/intro.md
    file_path 会是: "docs/guide.md" 或 "docs/api/intro.md"
    """
    return read_file(file_path)
```

### 3. 查询参数（可选参数）

FastMCP 支持 RFC 6570 形式风格的查询参数，使用 `{?param1,param2}` 语法：

```python
@mcp.resource("search://{query}{?limit,offset,sort}")
def search_items(
    query: str,                    # 必需的路径参数
    limit: int = 10,               # 可选的查询参数
    offset: int = 0,               # 可选的查询参数
    sort: str = "relevance"        # 可选的查询参数
) -> str:
    """搜索功能
    
    示例 URI:
    - search://python
    - search://python?limit=20
    - search://python?limit=20&offset=10&sort=date
    """
    results = perform_search(query, limit, offset, sort)
    return json.dumps(results)
```

**查询参数规则：**
- 必须有默认值
- 提供可选配置，不影响核心功能
- 清晰分离：必需数据在路径中，可选配置在查询参数中

## 四、类型注解和返回值

### 1. 支持的返回类型

```python
# 返回字符串
@mcp.resource("text://example")
def text_resource() -> str:
    return "Plain text content"

# 返回字典（自动转换为 JSON）
@mcp.resource("json://data")
def json_resource() -> dict:
    return {"key": "value", "items": [1, 2, 3]}

# 返回列表
@mcp.resource("list://items")
def list_resource() -> list:
    return ["item1", "item2", "item3"]

# 返回自定义对象（需要可序列化）
from dataclasses import dataclass, asdict

@dataclass
class User:
    name: str
    email: str

@mcp.resource("user://{id}")
def user_resource(id: str) -> dict:
    user = User(name="Alice", email="alice@example.com")
    return asdict(user)
```

### 2. 类型转换

FastMCP 会自动处理类型转换：

```python
@mcp.resource("items://{item_id}")
def get_item(item_id: int) -> str:  # item_id 会自动从字符串转为 int
    """URI: items://42 -> item_id=42 (int类型)"""
    return f"Item {item_id * 2}"

@mcp.resource("posts://{post_id}/comments/{comment_id}")
def get_comment(post_id: int, comment_id: int) -> dict:
    return {
        "post": post_id,
        "comment": comment_id,
        "text": "Comment content"
    }
```

## 五、配置选项

Resource 装饰器支持多个配置参数：

```python
@mcp.resource(
    "data://items/{id}",
    name="Item Resource",              # 资源名称
    description="获取指定ID的项目",     # 描述
    mime_type="application/json",      # MIME 类型
    enabled=True,                      # 是否启用
    tags={"category", "public"},       # 标签分类
    # annotations={...},               # 额外元数据
    # read_only=True,                  # 只读（默认 True）
    # idempotent=True                  # 幂等性
)
def get_item(id: str) -> dict:
    return {"id": id, "name": "Item name"}
```

## 六、错误处理

如果资源函数遇到错误，可以抛出标准 Python 异常或 FastMCP ResourceError：

```python
from fastmcp.exceptions import ResourceError

@mcp.resource("files://{filename}")
def read_file(filename: str) -> str:
    # 方式1：抛出标准异常
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File {filename} not found")
    
    # 方式2：抛出 ResourceError
    if not is_authorized(filename):
        raise ResourceError(
            f"Unauthorized access to {filename}",
            error_code="UNAUTHORIZED"
        )
    
    with open(filename) as f:
        return f.read()
```

**错误处理配置：**

```python
# 隐藏错误详情（用于生产环境）
mcp = FastMCP("Server", mask_error_details=True)
```

## 七、实际应用示例

### 示例 1：文件系统浏览器

```python
import os
import json

mcp = FastMCP("File Browser")

@mcp.resource("fs://list{?path}")
def list_directory(path: str = "/") -> str:
    """列出目录内容"""
    try:
        items = os.listdir(path)
        return json.dumps({
            "path": path,
            "items": items,
            "count": len(items)
        })
    except PermissionError:
        raise ResourceError(f"Permission denied: {path}")

@mcp.resource("fs://read/{**filepath}")
def read_file_content(filepath: str) -> str:
    """读取文件内容"""
    full_path = os.path.join("/data", filepath)
    if not os.path.isfile(full_path):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    with open(full_path, 'r') as f:
        return f.read()
```

### 示例 2：数据库查询

```python
import sqlite3

mcp = FastMCP("Database Explorer")

@mcp.resource("db://tables")
def list_tables() -> list:
    """列出所有表"""
    conn = sqlite3.connect("app.db")
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables

@mcp.resource("db://table/{table_name}{?limit}")
def get_table_data(table_name: str, limit: int = 100) -> dict:
    """获取表数据"""
    conn = sqlite3.connect("app.db")
    cursor = conn.execute(f"SELECT * FROM {table_name} LIMIT ?", (limit,))
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    conn.close()
    
    return {
        "table": table_name,
        "columns": columns,
        "rows": rows,
        "count": len(rows)
    }
```

### 示例 3：API 代理

```python
import httpx

mcp = FastMCP("GitHub Proxy")

@mcp.resource("github://user/{username}")
async def get_github_user(username: str) -> dict:
    """获取 GitHub 用户信息（异步）"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/users/{username}",
            headers={"Accept": "application/vnd.github.v3+json"}
        )
        response.raise_for_status()
        return response.json()

@mcp.resource("github://repo/{owner}/{repo}/issues{?state,per_page}")
async def get_repo_issues(
    owner: str,
    repo: str,
    state: str = "open",
    per_page: int = 30
) -> list:
    """获取仓库 issues"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/issues",
            params={"state": state, "per_page": per_page}
        )
        return response.json()
```

## 八、最佳实践

1. **明确的 URI 命名**
   ```python
   # 好的命名
   @mcp.resource("users://{user_id}/profile")
   @mcp.resource("api://v1/products/{product_id}")
   
   # 避免模糊命名
   @mcp.resource("data://{id}")  # 太泛化
   ```

2. **使用类型注解**
   ```python
   @mcp.resource("items://{id}")
   def get_item(id: int) -> dict:  # 明确类型
       ...
   ```

3. **提供详细的文档字符串**
   ```python
   @mcp.resource("search://{query}{?limit,offset}")
   def search(query: str, limit: int = 10, offset: int = 0) -> dict:
       """搜索资源
       
       Args:
           query: 搜索关键词
           limit: 返回结果数量上限
           offset: 结果偏移量
           
       Returns:
           包含搜索结果的字典
       """
       ...
   ```

4. **错误处理**
   ```python
   @mcp.resource("data://{id}")
   def get_data(id: str) -> dict:
       if not id.isdigit():
           raise ValueError("ID must be numeric")
       
       data = fetch_data(id)
       if not data:
           raise ResourceError(f"Data not found: {id}")
       
       return data
   ```

希望这个详细说明对你有帮助！有什么特定的使用场景需要讨论吗？
# LSP-MCP Server

基于 [LSAP (Language Server Agent Protocol)](https://github.com/lsp-client/LSAP) 的 MCP (Model Context Protocol) 服务器实现。

## 概述

LSP-MCP 将底层的 Language Server Protocol (LSP) 能力转换为高级的、对 AI 代理友好的认知工具。它通过 LSAP 协议层，将原子化的 LSP 操作组合成语义化的接口。

## 功能特性

- **定义导航**: 查找符号的定义、声明或类型定义
- **引用查找**: 查找符号的所有引用或实现
- **文件大纲**: 获取文件的结构化大纲，显示所有符号
- **悬停信息**: 获取符号的悬停信息和文档
- **工作区搜索**: 在整个工作区中搜索符号

## 安装

```bash
# 克隆仓库
git clone https://github.com/lsp-client/lsp-mcp.git
cd lsp-mcp

# 安装依赖（使用 uv）
uv sync

# 或使用 pip
pip install -e .
```

## 使用方法

### 作为 MCP 服务器运行

```bash
python main.py
```

### 可用工具

#### 1. 初始化 LSP 客户端

在使用其他工具之前，必须先初始化 LSP 客户端：

```python
init_lsp_client(
    workspace_root="/path/to/project",
    language="python",
    server_command="pyright-langserver",
    server_args=["--stdio"]
)
```

支持的语言：
- `python` - Python (使用 pyright-langserver, pylsp 等)
- `typescript` - TypeScript
- `javascript` - JavaScript
- `rust` - Rust
- `go` - Go
- `java` - Java
- `cpp` - C++
- `c` - C

#### 2. 获取定义

```python
get_definition(
    file_path="src/models.py",
    symbol_name="User.validate",
    mode="definition",  # "definition", "declaration", "type_definition"
    include_code=True
)
```

#### 3. 查找引用

```python
find_references(
    file_path="src/models.py",
    symbol_name="User.validate",
    mode="references",  # "references" or "implementations"
    max_items=20,
    context_lines=3
)
```

#### 4. 获取文件大纲

```python
get_outline(
    file_path="src/models.py"
)
```

#### 5. 获取悬停信息

```python
get_hover_info(
    file_path="src/main.py",
    symbol_name="process_data"
)
```

#### 6. 搜索工作区

```python
search_workspace(
    query="User",
    file_pattern="*.py",
    max_items=20
)
```

#### 7. 关闭 LSP 客户端

```python
shutdown_lsp_client()
```

## 示例工作流

```python
# 1. 初始化客户端
init_lsp_client(
    workspace_root="/home/user/my-python-project",
    language="python",
    server_command="pyright-langserver",
    server_args=["--stdio"]
)

# 2. 获取文件大纲
outline = get_outline(file_path="src/models.py")

# 3. 查找符号定义
definition = get_definition(
    file_path="src/main.py",
    symbol_name="User",
    mode="definition"
)

# 4. 查找所有引用
references = find_references(
    file_path="src/models.py",
    symbol_name="User.validate",
    mode="references",
    max_items=50
)

# 5. 完成后关闭客户端
shutdown_lsp_client()
```

## 测试

运行测试：

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_basic.py -v
```

## 架构

```
┌─────────────────┐
│   AI Agent      │
│  (MCP Client)   │
└────────┬────────┘
         │ MCP Protocol
         │
┌────────▼────────┐
│  LSP-MCP Server │
│  (FastMCP)      │
└────────┬────────┘
         │
┌────────▼────────┐
│  LSAP Layer     │
│ (lsap-sdk)      │
└────────┬────────┘
         │ LSP Protocol
         │
┌────────▼────────┐
│ Language Server │
│ (pyright, etc)  │
└─────────────────┘
```

## 技术栈

- **MCP**: Model Context Protocol - AI 代理通信协议
- **LSAP**: Language Server Agent Protocol - LSP 的高级抽象层
- **LSP**: Language Server Protocol - 代码分析和导航协议
- **Python 3.13+**: 主要编程语言
- **FastMCP**: 快速 MCP 服务器框架
- **lsap-sdk**: LSAP 协议 Python SDK

## 相关项目

- [LSAP](https://github.com/lsp-client/LSAP) - Language Server Agent Protocol
- [lsp-client](https://pypi.org/project/lsp-client/) - Python LSP 客户端库
- [Model Context Protocol](https://github.com/modelcontextprotocol) - MCP 协议规范

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 贡献

欢迎贡献！请查看 [LSAP 贡献指南](https://github.com/lsp-client/LSAP/blob/main/CONTRIBUTING.md)。

# MCP Review

对本次改动的 MCP 进行完整 review，流程如下：

## 1. 确认改动范围

```bash
git diff HEAD~1 --stat
git diff HEAD~1 --name-only
```

列出本次 commit 涉及的文件，识别改动了哪些 MCP（`*-mcp/server.py`）。

## 2. 逐 MCP 代码审查

对每个改动的 `server.py`，重点检查：

- **API 端点**：URL 路径、参数名、响应结构是否与实际 API 一致（若有文档变更，优先以最新文档为准）
- **响应解析**：字段名、嵌套层级、null 处理、类型转换是否正确
- **错误处理**：HTTP 错误、空结果、缺少 API key 的情况是否有清晰提示
- **格式化输出**：数值单位（M/B）、百分比、N/A 的处理是否一致
- **逻辑 bug**：变量遮蔽、死代码、条件判断错误

## 3. MCP 工具实测

对每个改动的 MCP，通过 MCP tool call 直接测试：

- 用真实 ticker（AAPL、NVDA、BTC 等）测试所有改动的 tool
- 测试边界情况：无效参数、不存在的 ticker、缺少 key 时的错误提示
- **注意**：避免同时并发调用有限频限制的 API（如 GDELT 需间隔 5s）

## 4. 文档同步检查

对照当前实际 tool 清单，逐一检查以下文件是否同步：

- `<mcp>/SKILL.md` — tool 签名、参数说明、使用示例
- `financial-research-agent/SKILL.md` — Ecosystem Map、API Key 表、Desktop Config、Decision Tree、Tools Quick Reference、Rate Limits、Data Freshness
- `README.md` / `README_zh.md` — MCP 概览表、API Keys 表、Available Tools 节、MCP 数量计数
- `install.sh` — API key 读取/提示/write_config、MCP 注册、Desktop config、skill 安装

## 5. install.sh 完整性检查

确认每个 MCP 均已覆盖：

| 检查项 | 说明 |
|--------|------|
| `json_get` 读取现有 key | 对有 key 的 MCP |
| `prompt_key` / `prompt_required_key` 提示 | 对有 key 的 MCP |
| `write_config` 写入 config 文件 | 对有 key 的 MCP |
| `register` 注册到 Claude CLI | 所有 MCP |
| Desktop config 入口 | 所有 MCP |
| `install_skill` 安装 SKILL.md | 所有 MCP |

## 6. 修复与提交

- 修复发现的所有问题
- 按改动性质分 commit：
  - `fix(<mcp>): ...` — bug 修复
  - `docs: ...` — 纯文档同步
- 若有遗留已知问题无法修复，在此处说明原因

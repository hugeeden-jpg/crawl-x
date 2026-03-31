# 规格：Wikipedia MCP Server

**项目**：crawl-x
**日期**：2026-03-31
**描述**：基于 `wikipedia` Python 库的 MCP server，为 agent 提供英文 Wikipedia 检索与内容获取能力；全文内容写入本地缓存文件，agent 通过文件路径读取。

---

## 背景与目标

crawl-x 缺乏通用知识库查询能力。Wikipedia MCP 填补这一空白，让 agent 在研究任务中能快速检索和获取百科内容，与现有金融/宏观/加密数据形成互补。

---

## 实现规格

### 文件位置

```
/Users/eden/crawl-x/wikipedia-mcp/server.py   # MCP server
/Users/eden/crawl-x/wikipedia-mcp/SKILL.md    # 独立 skill
```

### 依赖（PEP 723 inline）

```
mcp[cli]>=1.0.0
wikipedia>=1.4.0
```

无需 API key，无 configure 工具。

### 缓存目录

全文内容写入 `~/.cache/wikipedia-mcp/<sanitized_title>.md`（标题做文件名安全处理：空格→下划线，去除特殊字符）。

- 目录不存在时自动创建
- 同名文件直接覆盖（无过期逻辑，agent 每次调用即刷新）

---

## 工具规格

### 1. `search_wikipedia`

搜索 Wikipedia，返回匹配文章标题列表。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | str | 是 | 搜索词 |
| `limit` | int | 否 | 最多返回条数，默认 10，最大 20 |

**返回**：文章标题列表（str），以及各标题对应的摘要片段（snippet）。

---

### 2. `get_summary`

获取文章摘要（Wikipedia 第一段 / introductory section）。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | str | 是 | 文章标题（精确或接近精确） |
| `sentences` | int | 否 | 返回句子数，默认 5 |

**返回**：摘要文本（str）。

---

### 3. `get_article`

获取文章全文，写入本地缓存文件。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | str | 是 | 文章标题 |

**返回**：
```json
{
  "title": "Quantum computing",
  "file_path": "/Users/<user>/.cache/wikipedia-mcp/Quantum_computing.md",
  "char_count": 42381,
  "url": "https://en.wikipedia.org/wiki/Quantum_computing"
}
```
agent 通过 `file_path` 用 Read 工具读取全文内容。

---

### 4. `get_sections`

获取文章章节结构及各节内容。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | str | 是 | 文章标题 |

**返回**：章节列表，每项含 `section`（标题）和 `content`（正文，截断至 500 字符）。

---

### 5. `get_links`

获取文章内所有维基内链。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | str | 是 | 文章标题 |
| `limit` | int | 否 | 最多返回条数，默认 50 |

**返回**：链接标题列表（str）。

---

### 6. `get_related_topics`

基于文章分类和链接，获取相关话题。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | str | 是 | 文章标题 |
| `limit` | int | 否 | 最多返回条数，默认 10 |

**返回**：相关话题标题列表（str）。

---

### 7. `extract_key_facts`

从文章摘要中提取 N 条关键事实（句子级别切分）。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | str | 是 | 文章标题 |
| `count` | int | 否 | 提取条数，默认 5 |

**返回**：事实列表（每条一句话）。

---

### 8. `get_coordinates`

获取地理类条目的经纬度。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | str | 是 | 文章标题（地名、地标等） |

**返回**：
```json
{
  "title": "Eiffel Tower",
  "latitude": 48.8584,
  "longitude": 2.2945,
  "url": "https://en.wikipedia.org/wiki/Eiffel_Tower"
}
```
若文章无坐标，返回明确错误信息。

---

## 异常处理

| 异常 | 处理方式 |
|------|----------|
| `wikipedia.DisambiguationError` | 返回消歧义页的候选标题列表，提示用户选择 |
| `wikipedia.PageError` | 返回 "Article not found: {title}"，建议用 search_wikipedia 先查 |
| 网络超时 | 返回错误信息，不抛出未捕获异常 |

---

## install.sh 集成

1. 无需安装额外 CLI 工具（`wikipedia` 库由 `uv run` 自动安装）
2. 在 `register` 区块添加：`register "wikipedia-data" "wikipedia-mcp/server.py"`
3. 在 `install_skill` 区块添加：`install_skill "wikipedia-mcp" "wikipedia-mcp/SKILL.md"`
4. desktop config 添加对应条目

---

## 验收清单

- [ ] `search_wikipedia` 返回标题列表，limit 参数有效
- [ ] `get_summary` 正确返回摘要，sentences 参数有效
- [ ] `get_article` 将全文写入 `~/.cache/wikipedia-mcp/`，返回 file_path + char_count
- [ ] `get_sections` 返回所有章节，每节内容截断至 500 字符
- [ ] `get_links` 返回内链列表，limit 有效
- [ ] `get_related_topics` 基于 categories 返回相关话题
- [ ] `extract_key_facts` 返回指定条数的句子
- [ ] `get_coordinates` 有坐标返回经纬度，无坐标返回明确错误
- [ ] `DisambiguationError` 返回候选列表而非抛出异常
- [ ] `PageError` 返回友好错误信息
- [ ] 缓存目录自动创建，文件名安全处理
- [ ] `uv run server.py` 可直接启动，依赖自动安装
- [ ] 注册到 Claude CLI（`claude mcp list` 可见 `wikipedia-data`）
- [ ] `wikipedia-mcp/SKILL.md` 存在，`install.sh` 可正确分发
- [ ] `financial-research-agent/SKILL.md` 的 MCP 生态表已更新

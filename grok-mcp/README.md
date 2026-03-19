# grok-mcp

使用 Grok API 获取 X/Twitter 实时资讯和市场情绪的 MCP Server。

## 安装

依赖通过 PEP 723 内联声明，`uv run` 会自动安装，无需手动操作。

```bash
# 直接运行即可（依赖自动安装）
uv run /path/to/crawl-x/grok-mcp/server.py
```

## 配置 API Key

**方式一：环境变量（推荐）**

```bash
export XAI_API_KEY="xai-xxxxxxxxxxxxxxxx"
```

**方式二：通过工具写入（在 Claude 中调用）**

```
set_api_key("xai-xxxxxxxxxxxxxxxx")
```

会保存到 `~/.config/grok-mcp/config.json`。

xAI API Key 申请地址：https://console.x.ai

## 接入 Claude Desktop

在 `claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "grok-news": {
      "command": "uv",
      "args": ["run", "/Users/eden/crawl-x/grok-mcp/server.py"],
      "env": {
        "XAI_API_KEY": "xai-xxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

## 可用工具

| 工具 | 说明 |
|------|------|
| `set_api_key` | 配置并保存 API Key |
| `search_x_news` | 搜索 X 上指定主题的最新讨论 |
| `get_ticker_sentiment` | 获取股票/加密货币的 X 情绪分析 |
| `get_financial_news` | 获取金融资讯摘要（X + 网页） |
| `get_kol_mentions` | 追踪 KOL 最新发言 |

## 使用示例

- `search_x_news("$NVDA", hours=12)` — 搜索 NVDA 近 12 小时讨论
- `get_ticker_sentiment("BTC", asset_type="crypto")` — BTC 情绪分析
- `get_financial_news("美联储降息", source="both")` — 美联储资讯
- `get_kol_mentions("@elonmusk")` — Elon 最新发言

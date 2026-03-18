#!/usr/bin/env python3
"""
Grok MCP Server - 使用 Grok API 获取 X/Twitter 资讯和市场情绪
"""

import os
import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from openai import OpenAI

CONFIG_FILE = Path.home() / ".config" / "grok-mcp" / "config.json"


def load_api_key() -> str:
    key = os.environ.get("XAI_API_KEY", "")
    if key:
        return key
    if CONFIG_FILE.exists():
        cfg = json.loads(CONFIG_FILE.read_text())
        key = cfg.get("api_key", "")
        if key:
            return key
    raise ValueError(
        "未找到 XAI API Key。请设置环境变量 XAI_API_KEY，"
        "或使用 set_api_key 工具写入配置文件。"
    )


def get_client() -> OpenAI:
    return OpenAI(api_key=load_api_key(), base_url="https://api.x.ai/v1")


mcp = FastMCP("grok-news")


@mcp.tool()
def set_api_key(api_key: str) -> str:
    """配置 xAI Grok API Key，持久化保存到本地配置文件 (~/.config/grok-mcp/config.json)"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({"api_key": api_key}, indent=2))
    return f"API Key 已保存到 {CONFIG_FILE}"


@mcp.tool()
def search_x_news(query: str, hours: int = 24) -> str:
    """
    搜索 X/Twitter 上关于特定主题的最新资讯和讨论

    Args:
        query: 搜索关键词（如 "$TSLA 特斯拉"、"BTC 比特币"、"美联储 降息"）
        hours: 搜索最近多少小时内的内容（默认 24）
    """
    client = get_client()
    prompt = f"""请搜索 X（原 Twitter）上最近 {hours} 小时内关于"{query}"的帖子和讨论，并提供：

1. **热门观点摘要**：列出 5-8 条代表性观点或帖子内容
2. **整体情绪**：看多 / 看空 / 中性，并给出大致比例
3. **关键信息**：重要新闻、KOL 发言或异常讨论
4. **相关标签**：热门 hashtag 和 $cashtag

请用中文回答，内容简洁有用。"""

    response = client.chat.completions.create(
        model="grok-3",
        messages=[{"role": "user", "content": prompt}],
        extra_body={
            "search_parameters": {
                "mode": "on",
                "sources": [{"type": "x"}, {"type": "web"}],
            }
        },
    )
    return response.choices[0].message.content


@mcp.tool()
def get_ticker_sentiment(ticker: str, asset_type: str = "stock") -> str:
    """
    获取特定股票或加密货币在 X 上的市场情绪分析

    Args:
        ticker: 股票代码或加密货币符号（如 TSLA、BTC、ETH、NVDA）
        asset_type: "stock"（股票）或 "crypto"（加密货币）
    """
    client = get_client()
    asset_label = "股票" if asset_type == "stock" else "加密货币"
    cashtag = f"${ticker.upper()}"

    prompt = f"""请分析 X（原 Twitter）上当前关于 {cashtag}（{asset_label}）的市场情绪，包括：

1. **情绪评分**：0-100 分（0=极度恐慌，50=中性，100=极度贪婪）
2. **看多/看空比例**：基于近期帖子估算
3. **主要叙事**：散户当前关注的核心话题（2-3 点）
4. **异常信号**：是否有异常大量讨论、名人发言或可疑炒作
5. **近期催化剂**：影响情绪的最新事件

请用中文简洁回答。"""

    response = client.chat.completions.create(
        model="grok-3",
        messages=[{"role": "user", "content": prompt}],
        extra_body={
            "search_parameters": {
                "mode": "on",
                "sources": [{"type": "x"}],
            }
        },
    )
    return response.choices[0].message.content


@mcp.tool()
def get_financial_news(topic: str, source: str = "both") -> str:
    """
    获取金融市场相关资讯摘要（结合 X 和网页新闻）

    Args:
        topic: 主题（如 "美联储政策"、"纳斯达克"、"A股"、"黄金"、"比特币"）
        source: 数据来源，"x"（仅X平台）/ "web"（仅网页新闻）/ "both"（两者）
    """
    client = get_client()

    sources = []
    if source in ("x", "both"):
        sources.append({"type": "x"})
    if source in ("web", "both"):
        sources.append({"type": "web"})

    prompt = f"""请汇总关于"{topic}"的最新金融资讯，提供：

1. **今日要闻**：3-5 条最重要的新闻（含大致时间）
2. **市场影响**：对相关资产可能的短期影响分析
3. **关注事项**：未来 24-48 小时需关注的关键事件或数据发布

请用中文回答，突出关键数据和数字。"""

    response = client.chat.completions.create(
        model="grok-3",
        messages=[{"role": "user", "content": prompt}],
        extra_body={"search_parameters": {"mode": "on", "sources": sources}},
    )
    return response.choices[0].message.content


@mcp.tool()
def get_kol_mentions(handle: str) -> str:
    """
    追踪特定 KOL 的最新发言和市场观点

    Args:
        handle: KOL 的名字或 X 用户名（如 "Elon Musk"、"@elonmusk"、"Michael Saylor"）
    """
    client = get_client()

    prompt = f"""请搜索 {handle} 在 X（Twitter）上的最新发言，重点关注：

1. **最新帖子**：近期 3-5 条重要发言（含大致时间）
2. **市场相关内容**：涉及投资、市场、具体资产的言论
3. **观点变化**：与之前立场相比是否有新变化
4. **市场反应**：相关帖子的互动量和市场反响

请用中文回答。"""

    response = client.chat.completions.create(
        model="grok-3",
        messages=[{"role": "user", "content": prompt}],
        extra_body={
            "search_parameters": {
                "mode": "on",
                "sources": [{"type": "x"}],
            }
        },
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    mcp.run()

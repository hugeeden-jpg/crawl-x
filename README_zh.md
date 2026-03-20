[English](README.md)

# crawl-x — 金融智能 MCP 套件

一套 MCP（模型上下文协议）服务器集合，让 Claude 实时访问股票行情、宏观经济指标、加密货币分析、市场情绪、内部人交易/国会交易记录，以及 Twitter/X、Reddit、YouTube 等社交媒体数据。

## MCP 概览

| MCP | 服务器名称 | 功能描述 | API Key |
|-----|-----------|---------|---------|
| `market-data-mcp` | `market-data` | 股票报价、财务报表、新闻、财报日历、SimFin 标准化财务数据 | Finnhub / SimFin（可选） |
| `macro-mcp` | `macro-data` | FRED 经济数据、SEC EDGAR 文件 | FRED（必须） |
| `news-mcp` | `news-data` | GDELT 全球新闻搜索（100+ 语言）+ 情绪时间线 | 无需 |
| `crypto-mcp` | `crypto-data` | CoinGecko 价格、DeFi TVL、Glassnode 链上数据 | 可选 |
| `sentiment-mcp` | `sentiment-data` | 恐慌贪婪指数、国会/内部人情绪（Quiver） | 可选 |
| `scrape-mcp` | `financial-scraper` | OpenInsider 内部人交易、Capitol Trades、CME FedWatch、Circle 储备透明度、The Block 新闻、QuiverQuant 国会交易图表 | 无需 |
| `grok-mcp` | `grok-news` | 通过 Grok AI 获取 X/Twitter 新闻与情绪分析 | XAI（可选） |
| `social-mcp` | `social-data` | Reddit（公开）、Twitter/X（xreach）、YouTube（yt-dlp） | 可选 |

---

## 前置条件

**[Claude Code](https://claude.ai/code)**（CLI 使用）— 需手动安装：

```bash
npm install -g @anthropic-ai/claude-code
```

**[uv](https://docs.astral.sh/uv/getting-started/installation/)** — macOS/Linux 下 `install.sh` 会自动安装；Windows 用户请提前手动安装。

---

## 安装

```bash
git clone https://github.com/you/crawl-x
cd crawl-x
bash install.sh
```

脚本会自动完成以下操作：
- macOS/Linux 下自动安装 `uv`（若未检测到）
- 安装 Scrapling + Playwright 浏览器（`scrape-mcp` 抓取 Capitol Trades 和 CME FedWatch 所需）
- 自动安装 `yt-dlp`（`social-mcp` YouTube 工具所需）
- 提示输入 API Key — **回车可保留已有值**
- 通过 `claude mcp add` 注册全部 8 个 MCP 到 Claude CLI

同时生成 Claude Desktop 配置文件：

```bash
bash install.sh --desktop
```

> **注意：** 生成的 `claude_desktop_config.json` 包含当前机器的绝对路径。若分享给他人使用，需将路径替换为对方机器上的实际仓库位置。

---

## API Keys

| Key | 使用方 | 获取地址 |
|-----|--------|---------|
| `XAI_API_KEY` | grok-mcp | [console.x.ai](https://console.x.ai) — 可选；原始推文可通过 `social-data` 获取 |
| `FRED_API_KEY` | macro-mcp | [fred.stlouisfed.org/docs/api](https://fred.stlouisfed.org/docs/api/api_key.html) |
| `FINNHUB_API_KEY` | market-data-mcp | [finnhub.io](https://finnhub.io) |
| `SIMFIN_API_KEY` | market-data-mcp | [simfin.com](https://simfin.com) — 免费（2000 次/天） |
| `QUIVER_API_KEY` | sentiment-mcp | [quiverquant.com](https://www.quiverquant.com) |
| `COINGECKO_API_KEY` | crypto-mcp | [coingecko.com/api](https://www.coingecko.com/en/api) |
| `GLASSNODE_API_KEY` | crypto-mcp | [glassnode.com](https://glassnode.com) |
| `TWITTER_AUTH_TOKEN` | social-mcp | x.com cookie（Cookie Picker 扩展 → `auth_token`） |
| `TWITTER_CT0` | social-mcp | x.com cookie（Cookie Picker 扩展 → `ct0`） |

Key 可在运行 `install.sh` 时输入，也可通过各 MCP 的 `configure()` 工具在之后配置。

> **Twitter Cookie 配置：** 使用本项目内置的 **Cookie Picker** Chrome 扩展（`extensions/cookie-picker/`）——在 Chrome 中以"加载已解压的扩展程序"方式安装，打开 x.com，点击插件图标，`auth_token` 和 `ct0` 已默认勾选，点击"Copy selected"复制后粘贴到 `configure_twitter(auth_token=..., ct0=...)` 即可。

---

## Claude Desktop 配置

运行 `bash install.sh --desktop` 后，将生成的 `claude_desktop_config.json` 内容合并到：

```
~/Library/Application Support/Claude/claude_desktop_config.json   # macOS
%APPDATA%\Claude\claude_desktop_config.json                        # Windows
```

重启 Claude Desktop 即可加载所有 MCP。

---

## 可用工具

### market-data
| 工具 | 功能 |
|------|------|
| `get_quote` | 实时股票报价 |
| `get_stock_info` | 公司概览与核心指标 |
| `get_stock_history` | OHLCV 历史价格 |
| `get_financials` | 利润表 / 资产负债表 / 现金流量表 |
| `get_analyst_recommendations` | 买入/持有/卖出评级 |
| `get_market_news` | 市场综合新闻（Finnhub） |
| `get_company_news` | 指定股票最新新闻（Finnhub） |
| `get_earnings_calendar` | 即将发布的财报日历（Finnhub） |
| `get_economic_calendar` | 宏观经济事件日历：CPI、NFP、GDP、FOMC、PMI（Investing.com，无需 key） |
| `get_ipo_calendar` | 即将上市的 IPO 日历：价格区间、交易所（Finnhub） |
| `get_dividend_calendar` | 双模式：指定 ticker → 该股除息日/付息日/历史股息（yfinance）；不传 ticker → 全市场除息日历，按时间段/国家筛选（Investing.com，无需 Key） |
| `get_options_expiry` | 期权到期日历：Call/Put 未平仓量、P/C 比率（yfinance） |
| `get_news_sentiment` | 新闻情绪与热度评分（Finnhub） |
| `get_simfin_financials` | 标准化财务报表：利润表 / 资产负债表 / 现金流 / 衍生指标（SimFin） |

### macro-data
| 工具 | 功能 |
|------|------|
| `search_fred_series` | 按关键词搜索 FRED 经济数据系列 |
| `get_fred_data` | 获取任意 FRED 时间序列数据 |
| `get_key_indicators` | 联储利率、10Y 收益率、CPI、失业率 |
| `search_edgar_company` | 搜索 SEC EDGAR 公司数据库 |
| `get_recent_filings` | 获取公司近期 10-K/10-Q/8-K 文件列表 |
| `get_13f_holdings` | 基金 13F 持仓元数据与归档链接 |
| `get_filing_text` | 特定 SEC 文件的元数据与归档 URL |

### crypto-data
| 工具 | 功能 |
|------|------|
| `get_crypto_price` | 币种价格与 24h 统计 |
| `get_crypto_market_data` | 历史最高价、供应量、多周期涨跌幅 |
| `get_global_market` | 全球加密市场概览 |
| `get_trending_coins` | CoinGecko 热门币种 |
| `get_defi_tvl_overview` | TVL 排名前列的 DeFi 协议 |
| `get_protocol_tvl` | 指定协议的 TVL 历史与跨链分布 |
| `get_all_chains` | 全部公链 TVL 排名 |
| `get_chain_tvl` | 指定链的 TVL 趋势（30 天） |
| `get_stablecoins` | 稳定币市场：供应量、锚定类型、机制 |
| `get_stablecoin_detail` | 单一稳定币详情：跨链分布、供应历史 |
| `get_yields` | DeFi 最高 APY 收益/借贷池 |
| `get_onchain_metric` | Glassnode 链上指标（需 Key） |
| `get_exchange_flows` | 交易所资金流入/流出（需 Key） |

### sentiment-data
| 工具 | 功能 |
|------|------|
| `get_fear_greed_index` | 加密恐慌贪婪指数历史 |
| `get_congressional_trades` | 国会议员股票交易（Quiver，需 Key） |
| `get_wsb_mentions` | WSB 提及次数与情绪（需 Key） |
| `get_insider_sentiment` | 内部人交易情绪汇总（需 Key） |

### financial-scraper
| 工具 | 功能 |
|------|------|
| `get_insider_trades` | OpenInsider SEC Form 4 交易（无需 Key，约 2s） |
| `get_congressional_trades` | Capitol Trades 国会实时交易（约 15s） |
| `get_fed_rate_probabilities` | CME FedWatch FOMC 利率概率（约 14s） |
| `get_circle_reserves` | Circle USDC/EURC 流通量、储备构成、铸造/赎回流量（约 10s） |
| `search_theblock(query, size, fetch_body, fetch_index)` | The Block 加密新闻搜索，可按序号获取正文（约 1-2s） |
| `get_quiverquant_congress(ticker, use_cache, output)` | QuiverQuant：国会交易 vs 股价交互图（HTML，自动在浏览器打开）+ CSV；按日缓存（首次约 15s） |
| `clear_quiverquant_cache(ticker)` | 清除指定股票或全部 QuiverQuant 缓存文件 |

### grok-news
| 工具 | 功能 |
|------|------|
| `search_x_news` | 搜索 X/Twitter 新闻与帖子 |
| `get_ticker_sentiment` | 指定股票/加密货币的 X 平台情绪分析 |
| `get_financial_news` | 来自 X 及网络的金融新闻摘要 |
| `get_kol_mentions` | 关键意见领袖近期发帖 |

### news-data
| 工具 | 功能 |
|------|------|
| `search_news` | GDELT 全球新闻搜索（100+ 语言、65+ 国家），无需 Key |
| `get_news_sentiment` | 每小时情绪数据聚合为每日均值（正值=乐观，负值=悲观） |

### social-data
| 工具 | 功能 | 依赖 |
|------|------|------|
| `configure_twitter(auth_token, ct0)` | 保存 Twitter Cookie 凭据 | — |
| `search_tweets(query, n)` | 按关键词或 $TICKER 搜索原始推文 | xreach + cookie |
| `get_tweet(url_or_id)` | 获取单条推文 | xreach + cookie |
| `get_user_timeline(username, n)` | 获取用户时间线 | xreach + cookie |
| `get_thread(url_or_id)` | 获取完整对话串 | xreach + cookie |
| `get_subreddit_posts(subreddit, sort, limit)` | 浏览子版块帖子（热门/最新/最高） | 无 |
| `search_reddit(query, limit, subreddit)` | Reddit 帖子搜索 | 无 |
| `get_post_comments(post_url, limit)` | 获取帖子与顶部评论 | 无 |
| `get_video_info(url)` | YouTube 视频元数据 | yt-dlp |
| `get_video_transcript(url, lang)` | YouTube 字幕 / 讲稿提取 | yt-dlp |
| `search_youtube(query, n)` | YouTube 视频搜索 | yt-dlp |

---

## 测试

测试套件覆盖全部 8 个 MCP。

```bash
cd tests

# 运行所有快速测试（约 60s，无浏览器，自动跳过未配置的 Key）
uv run pytest -m "not slow"

# 包含浏览器抓取测试（Capitol Trades、CME FedWatch，约 5 分钟）
uv run pytest

# 单独运行某个 MCP 的测试
uv run pytest test_scrape.py -v
```

**测试分类：**

| 分类 | 覆盖范围 | 说明 |
|------|---------|------|
| 免费 API（始终运行） | CoinGecko、DeFi Llama、恐慌贪婪指数、SEC EDGAR、OpenInsider、yfinance、Reddit | 无需 Key |
| Key 限制（自动跳过） | FRED、Finnhub、Quiver、Glassnode、XAI、Twitter（xreach） | 未配置 Key 时自动 skip |
| `slow`（按需运行） | Capitol Trades、CME FedWatch、YouTube（yt-dlp） | 浏览器/CLI；用 `-m "not slow"` 跳过 |

免费层 API 的瞬时限速错误（HTTP 429、超时）会自动 skip，不计入失败。

---

## 项目结构

```
crawl-x/
├── install.sh                    # 一键安装脚本
├── market-data-mcp/server.py
├── macro-mcp/server.py
├── crypto-mcp/server.py
├── sentiment-mcp/server.py
├── scrape-mcp/server.py
├── grok-mcp/server.py
├── social-mcp/server.py
├── financial-research-agent/     # 主 Agent Skill
│   └── SKILL.md
└── tests/                        # 回归测试套件
    ├── pyproject.toml
    ├── conftest.py
    ├── test_market_data.py
    ├── test_macro.py
    ├── test_crypto.py
    ├── test_sentiment.py
    ├── test_scrape.py
    ├── test_grok.py
    └── test_social.py
```

每个 `server.py` 均使用 [PEP 723 内联脚本依赖](https://peps.python.org/pep-0723/) — `uv run` 会在首次启动时自动安装所有依赖，无需手动 `pip install`。

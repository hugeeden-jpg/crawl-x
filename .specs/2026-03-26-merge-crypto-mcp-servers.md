# 规格：合并 crypto-mcp-servers 工具到 crawl-x

**项目**：crawl-x
**日期**：2026-03-26
**描述**：将 `/Users/eden/Downloads/crypto-mcp-servers` 中的 5 个 MCP 的工具合并到当前项目，其中 3 个 MCP 的工具合并进 macro-mcp，2 个作为全新 MCP 加入。

---

## 背景与目标

`crypto-mcp-servers` 包含 Binance 期货数据、BLS 劳工统计、CoinMarketCap、SEC EDGAR 扩展和美国国债专项工具。通过合并去重，扩充现有 MCP 能力，避免重复 server 维护成本。

---

## 合并决策总览

| 来源 MCP | 目标 | 操作 |
|----------|------|------|
| `binance-mcp` | `crawl-x/binance-mcp/` | 新建独立 MCP |
| `cmc-mcp` | `crawl-x/cmc-mcp/` | 新建独立 MCP |
| `sec-mcp` | `crawl-x/macro-mcp/server.py` | 追加 4 个新工具 |
| `bls-mcp` | `crawl-x/macro-mcp/server.py` | 追加 6 个新工具 |
| `treasury-mcp` | `crawl-x/macro-mcp/server.py` | 追加 6 个新工具 |

---

## 任务一：macro-mcp 新增工具

### 来源：sec-mcp（仅新增，不替换已有工具）

新增以下 4 个工具（跳过与现有 get_recent_filings / get_13f_holdings 近似的工具）：

| 工具名 | 功能 |
|--------|------|
| `search_filings` | 全文搜索 SEC EDGAR 公告（query + form_type + date_range） |
| `get_company_facts` | 获取公司 XBRL 财务数据（如 Revenues、Assets），支持指定 concept |
| `get_insider_transactions` | 获取 Form 4 内部人交易记录（ticker + limit） |
| `get_company_info` | 获取公司基本信息（名称、CIK、SIC、州、交易所等） |

**注意**：`lookup_ticker` 与现有 `search_edgar_company` 功能近似，不加入。`get_company_filings` 与 `get_recent_filings` 近似，不加入。`get_institutional_holdings` 与 `get_13f_holdings` 近似，不加入。

### 来源：bls-mcp（全部工具）

新增以下 6 个工具：

| 工具名 | 功能 |
|--------|------|
| `configure_bls` | 配置 BLS API key（存入 macro-mcp config） |
| `get_cpi` | CPI（含核心 CPI）月度数据，支持 breakdown 模式 |
| `get_ppi` | PPI（生产者价格指数）月度数据 |
| `get_jobs_report` | 非农就业/失业率综合报告 |
| `get_jolts` | JOLTS 职位空缺、招聘、离职数据 |
| `get_bls_series` | 按 series_id 获取任意 BLS 数据序列 |

**注意**：`list_series` 工具为辅助说明工具，可选加入（无 API 调用，仅列举常用 series_id）。

**依赖**：BLS_API_KEY（可选，免费注册，无 key 时访问有限）。按可选 configure 模式，key 缺失时降级运行。

### 来源：treasury-mcp（全部工具）

新增以下 6 个工具：

| 工具名 | 功能 |
|--------|------|
| `get_yield_curve` | 完整美债收益率曲线（1M-30Y），支持 N 个月历史 |
| `get_real_yield_curve` | 实际收益率曲线（TIPS） |
| `get_breakeven_inflation` | 盈亏平衡通胀率（名义 - 实际） |
| `get_tga_balance` | 财政部一般账户（TGA）余额历史 |
| `get_treasury_auctions` | 近期国债拍卖结果 |
| `get_fed_balance_sheet` | 美联储资产负债表（总资产/证券/MBS等） |

**数据源**：美国财政部官方 XML API + FiscalData API（无需 key）。

**注意**：与 blockbeats-mcp 的 `get_us_treasury_yield` 区别——blockbeats 提供历史点位数据，treasury 提供完整收益率曲线及财政工具，互补不重复。

### macro-mcp configure 工具更新

现有 `configure` 工具仅处理 `fred_api_key`，需扩展以支持 `bls_api_key`（可选）。

---

## 任务二：新建 binance-mcp

**目录**：`/Users/eden/crawl-x/binance-mcp/`

**工具清单**（来自源文件，全部保留）：

| 工具名 | 功能 |
|--------|------|
| `get_funding_rate` | 期货资金费率历史（symbol + limit） |
| `get_open_interest` | 合约持仓量历史（symbol + period） |
| `get_long_short_ratio` | 多空持仓比（symbol + period） |
| `get_liquidations_summary` | 爆仓摘要（多空爆仓量） |
| `get_market_stats` | 单合约市场统计（24h 成交量/价格变动等） |
| `get_top_movers` | 涨跌幅榜（futures，limit） |
| `get_futures_kline` | 期货 K 线数据 |
| `get_basis` | 期现基差历史 |

**数据源**：Binance FAPI（期货）+ 现货 API（公开端点，无需 API key）。

**文件**：直接复制源 `server.py`，保持 PEP 723 inline 依赖格式（requests）。

---

## 任务三：新建 cmc-mcp

**目录**：`/Users/eden/crawl-x/cmc-mcp/`

**工具清单**（来自源文件，全部保留）：

| 工具名 | 功能 |
|--------|------|
| `configure` | 配置 CMC_API_KEY |
| `get_listings` | 加密货币市值排行榜（limit/sort） |
| `get_quote` | 单币或多币实时报价（symbols 逗号分隔） |
| `get_global_metrics` | 全球加密市场指标（总市值/BTC 占比等） |
| `get_category_list` | 加密货币分类列表 |
| `get_category` | 某分类下的币种列表（category_id） |
| `get_trending` | 趋势币种榜单 |
| `get_fear_greed` | CMC 恐慌贪婪指数 |

**与现有工具的区别**：`get_global_metrics` 与 crypto-mcp 的 `get_global_market` 数据源不同（CMC vs CoinGecko），并行保留；`get_fear_greed` 与 sentiment-mcp 的 `get_fear_greed_index` 数据源不同（CMC vs Alternative.me），并行保留。

**依赖**：CMC_API_KEY（必须，免费 Basic plan 可用）。按可选 configure 模式，key 缺失时工具报错提示配置。

**文件**：直接复制源 `server.py`，保持 PEP 723 inline 依赖格式（requests）。

---

## 任务四：install.sh 更新

新增两个 MCP 的注册逻辑：

| MCP | 命令路径 | 环境变量 |
|-----|----------|---------|
| `binance-mcp` | `uv run /Users/eden/crawl-x/binance-mcp/server.py` | 无（公开 API） |
| `cmc-mcp` | `uv run /Users/eden/crawl-x/cmc-mcp/server.py` | `CMC_API_KEY`（可选） |

macro-mcp 注册命令不变（路径不变），但需新增 `BLS_API_KEY` 环境变量传入（可选）。

---

## 任务五：financial-research-agent/SKILL.md 更新

在能力描述中新增：
- **Binance 期货数据**：资金费率、多空比、爆仓、基差（via binance-mcp）
- **CoinMarketCap**：币种排行、分类、全球指标（via cmc-mcp）
- **BLS 劳工数据**：CPI、PPI、非农、JOLTS（via macro-mcp）
- **美国国债专项**：完整收益率曲线、TGA 余额、国债拍卖、美联储资产负债表（via macro-mcp）
- **SEC EDGAR 扩展**：全文搜索公告、XBRL 财务数据、内部人交易（via macro-mcp）

---

## 不加入的工具（重复/近似）

| 来源 | 工具名 | 原因 |
|------|--------|------|
| sec-mcp | `lookup_ticker` | ≈ macro-mcp `search_edgar_company` |
| sec-mcp | `get_company_filings` | ≈ macro-mcp `get_recent_filings` |
| sec-mcp | `get_institutional_holdings` | ≈ macro-mcp `get_13f_holdings` |

---

## 验收清单

### macro-mcp 扩展
- [ ] 新增 4 个 SEC 工具，函数名不与现有冲突
- [ ] 新增 6 个 BLS 工具，`configure_bls` 独立存储 key（不影响现有 FRED key）
- [ ] 新增 6 个 Treasury 工具，无需 API key，直接可用
- [ ] `configure` 工具更新或新增 `configure_bls` 以支持 BLS key 配置
- [ ] PEP 723 inline deps 包含新增依赖（如有）
- [ ] macro-mcp 现有工具功能不受影响（回归测试通过）

### binance-mcp
- [ ] server.py 复制到正确目录，PEP 723 格式正确
- [ ] `uv run server.py` 可启动，无需额外安装
- [ ] 所有 8 个工具可调用，基本参数验证通过
- [ ] 生成 SKILL.md（描述工具能力和使用场景）

### cmc-mcp
- [ ] server.py 复制到正确目录，PEP 723 格式正确
- [ ] key 未配置时工具返回明确提示（非崩溃）
- [ ] `configure` 工具存储 key 到 `~/.config/cmc-mcp/config.json`
- [ ] 生成 SKILL.md

### install.sh
- [ ] 新增 binance-mcp 注册逻辑（无 env var）
- [ ] 新增 cmc-mcp 注册逻辑（含 CMC_API_KEY prompt，可选跳过）
- [ ] macro-mcp 注册命令新增 BLS_API_KEY 传入（可选）
- [ ] 已有 MCP 注册逻辑不受影响

### financial-research-agent/SKILL.md
- [ ] 新能力描述准确反映 5 个 MCP 的新工具
- [ ] 使用场景举例涵盖主要查询类型

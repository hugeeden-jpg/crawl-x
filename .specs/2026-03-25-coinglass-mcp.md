# 规格：coinglass-mcp

**项目**：coinglass-mcp
**日期**：2026-03-25
**描述**：逆向 CoinGlass 加密 API，在 Python 中复现完整解密流程，封装为 MCP server

---

## 背景与目标

CoinGlass 对所有 API 响应进行 AES-ECB 加密 + gzip 压缩，防止直接抓包使用。本项目通过逆向混淆 JS 代码，在 Python 中复现完整解密流程，封装为 MCP server 供 Claude 调用。

---

## 解密算法（已完全逆向并验证）

### 核心结论

| 项目 | 值 | 备注 |
|------|----|------|
| AES 模式 | **ECB**（不是 CBC！） | JS 中 `mode: CryptoJS.mode.ECB` |
| AES padding | PKCS7 | JS 中 `padding: CryptoJS.pad.Pkcs7` |
| IV | 无（ECB 不需要） | 最初误判为 CBC+IV=zeros |
| 解密后数据 | 直接 gzip/zlib 压缩字节 | 不经过 hex 编码中转 |
| 压缩格式 | gzip（wbits=31）为主 | 兼容 zlib/raw deflate |
| key 长度 | 恰好 16 bytes | `btoa(seed)[:16]` |

### 请求端必要请求头

```python
headers = {
    "accept": "application/json",
    "accept-language": "zh-CN,zh;q=0.9",
    "cache-control": "no-cache",
    "cache-ts-v2": str(int(time.time() * 1000)),  # 每次请求新生成
    "encryption": "true",
    "language": "en",
    "origin": "https://www.coinglass.com",
    "pragma": "no-cache",
    "referer": "https://www.coinglass.com/",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
}
```

### 响应头关键字段

| 响应头 | 示例值 | 说明 |
|--------|--------|------|
| `v` | `"1"` | key 派生模式（实测常为 1） |
| `user` | `"wH17HAVf..."` | 加密的真实 AES key（base64，每次唯一） |
| `encryption` | `"true"` | 确认响应已加密 |

### 解密 Pipeline

```
输入：
  cache_ts   = 请求时发送的 cache-ts-v2 头值（字符串）
  v          = response.headers["v"]
  user_hdr   = response.headers["user"]
  enc_data   = response.json()["data"]   # base64 字符串

Step 1: 推导 seed（根据 V 模式）
  V=0 → seed = cache_ts（毫秒时间戳字符串）
  V=1 → seed = url_path（如 "/api/exchange/chain/v3/balance"）
  V=66 → seed = "d6537d845a964081"（hardcoded）
  V=55 → seed = "170b070da9654622"（hardcoded，来自混淆数组）
  V=77 → seed = "863f08689c97435b"（hardcoded，来自混淆数组）
  V=2  → seed = 某响应头值（暂未遇到）

Step 2: 初始 key
  key1 = base64.b64encode(seed.encode()).decode()[:16]
  # 例：seed="/api/exchange/chain/v3/balance" → key1="L2FwaS9leGNoYW5n"

Step 3: 解密 user 响应头，得到真实 key
  key2 = decrypt_field(user_hdr, key1)
  # 例：key2="97aacb3e8efc4630"（16字符，每次唯一）

Step 4: 解密响应体
  result_str = decrypt_field(enc_data, key2)

Step 5: 解析 JSON
  return json.loads(result_str)
```

### `decrypt_field` 实现（已验证）

```python
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64, zlib

def decrypt_field(ciphertext_b64: str, key_str: str) -> str:
    """AES-ECB + PKCS7 unpad → gzip/zlib decompress → UTF-8 string"""
    key = key_str.encode("utf-8")   # 必须恰好 16 bytes
    assert len(key) == 16
    raw = base64.b64decode(ciphertext_b64)
    cipher = AES.new(key, AES.MODE_ECB)
    dec = unpad(cipher.decrypt(raw), AES.block_size)
    # dec 直接是压缩字节，试各种 zlib 模式
    for wbits in (31, 15, -15, 47):   # gzip, zlib, raw deflate, auto
        try:
            return zlib.decompress(dec, wbits=wbits).decode("utf-8")
        except Exception:
            pass
    raise ValueError(f"decompress failed for {len(dec)}-byte payload")
```

### Ground Truth 验证（来自浏览器断点调试）

| 输入 ciphertext | 输入 key | 期望输出 |
|-----------------|----------|----------|
| `wH17HAVf7pFi0Pc/yGxQqk7qth0BYiKCoDZabZEeYTr17Bq4QY/YmY7nZc5PjJbq` | `L2FwaS9leGNoYW5n` | `97aacb3e8efc4630` |

Python 验证通过 ✅

---

## JS 逆向详情

### 字符串解码机制

JS 混淆通过 `te(index, key)` / `Qt` 解码所有字符串常量：
- 字符串数组 `ee()` 在运行时被 shuffle
- 每个字符串用自定义 base64（小写优先字母表）+ RC4 编码
- 解码后的关键常量见下表

### 关键常量对照（Qt = te，offset=364）

| 调用 | 解码值 | 用途 |
|------|--------|------|
| `Qt(392, "]abs")` | `"ECB"` | AES 模式 |
| `Qt(457, "fEC)")` | `"Pkcs7"` | AES padding |
| `Qt(451, "sTnZ")` | `"AES"` | CryptoJS.AES |
| `Qt(435, "ESiB")` | `"decrypt"` | .decrypt() |
| `Qt(437, "vCsp")` | `"pad"` | CryptoJS.pad |
| `Qt(546, "5#Jj")` | `"mode"` | options.mode |
| `Qt(386, "]abs")` | `"enc"` | CryptoJS.enc |
| `Qt(439, "Twrm")` | `"Utf8"` | .Utf8 |
| `Qt(380, "]abs")` | `"parse"` | .parse() |
| `Qt(410, "DiW(")` | `"toString"` | .toString() |
| `Qt(537, "z)Qv")` | `"0\|4\|2\|1\|3"` | re() 内部 pipeline |
| `Qt(467, "6#gF")` | `"4\|0\|2\|6\|3\|1\|5"` | axios 拦截器 pipeline |
| `Qt(431, "@zuU")` | `"user"` | 响应头字段名 |
| `Qt(474, "X59d")` | `"substring"` | key 截取 |

### re() 函数 pipeline（解密单个字段）

顺序：`0→4→2→1→3`
- Case 0：`CryptoJS.AES.decrypt(cipher, CryptoJS.enc.Utf8.parse(key), {mode: ECB, padding: Pkcs7}).toString(Hex)` → 但实测明文直接是压缩字节，不是 hex 中间格式
- Case 4：`ne(hex_str)` → hex 解析 + pako.inflate（wbits=15 zlib）
- Case 2/1：strip 首尾 `"` 引号
- Case 3：return

> **注**：JS 端 `.toString(Hex)` 将解密后的 WordArray 转为 hex 字符串，`ne()` 再 fromHex→inflate。Python 端等效：直接 `unpad` 后对字节 inflate，结果相同。

### axios 拦截器 pipeline（响应处理）

顺序：`4→0→2→6→3→1→5`
- Case 4：`s = ie(url)` → URL path（seed for V=1）
- Case 0：`o = Xt(response, s)` → key 派生，返回 `btoa(seed)`
- Case 2：`o = o.substring(0, 16)` → key1
- Case 6：`o = re(headers.user, o)` → key2
- Case 3：`a = re(data.data, o)` → 解密 body
- Case 1：`JSON.parse(a)` 赋值
- Case 5：return

---

## 待接入端点（第一期）

| 工具名 | 端点 | 主要参数 |
|--------|------|---------|
| `get_exchange_balance` | `GET /api/exchange/chain/v3/balance` | `exName=all`, `symbol=BTC/ETH/...` |
| （后续扩展） | 更多端点 | — |

---

## MCP Server 规格

- 文件：`coinglass-mcp/server.py`（PEP 723 inline deps）
- 依赖：`pycryptodome`、`requests`、`mcp`
- 运行：`uv run server.py`
- Host：`capi.coinglass.com`（非 `api.coinglass.com`）
- SSL：`verify=False`（企业代理拦截 TLS，需绕过证书验证）

---

## 验收清单

- [x] JS 逆向完成：AES 模式确认为 ECB
- [x] `decrypt_field` ground truth 验证通过（key2="97aacb3e8efc4630"）
- [x] 端到端测试通过：`/api/exchange/chain/v3/balance` 返回 3 条记录
- [x] `cache-ts-v2` 每次请求新生成
- [x] `user` 响应头存在时走解密 pipeline，否则直接返回 data
- [x] AES key 长度恰好 16 bytes
- [ ] server.py MCP server 实现
- [ ] 更多端点接入

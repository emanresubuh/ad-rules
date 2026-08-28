# AdBlock Rules

## 订阅链接

```
https://raw.githubusercontent.com/emanresubuh/ad-rules/main/rule_srs/adblock_rules.srs
```

## 最新构建报告

## 📦 AdBlock Rules — 2026-08-28 13:13 CST

### 📊 本次统计

| 项目 | 数量 |
|---|---|
| 订阅源数量 | 4 个 |
| 订阅解析原始域名 | 267219 个 |
| 自定义屏蔽追加 | 13 个 |
| 白名单移除 | 2 个 |
| 子域名去冗余前 | 267230 个 |
| **最终规则数量** | **261473 个** |
| SRS 文件大小 | 1966.1 KB |

### 📈 变化对比

🔺 较上次增加 **138** 条

### 📥 订阅源明细

  - `https://raw.githubusercontent.com/hagezi/dns-blocklists/main/adblock/pro.txt` → 解析出 **225940** 个域名
  - `https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/AWAvenue-Ads-Rule.txt` → 解析出 **896** 个域名
  - `https://anti-ad.net/adguard.txt` → 解析出 **99523** 个域名
  - `https://gitlab.com/hagezi/mirror/-/raw/main/dns-blocklists/adblock/pro.txt?ref_type=heads` → 解析出 **225940** 个域名

### 🚀 使用方式

在 sing-box 配置中引用（DNS 规则和路由规则均可）：

```json
{
  "type": "remote",
  "tag": "adblock",
  "url": "https://raw.githubusercontent.com/emanresubuh/ad-rules/main/rule_srs/adblock_rules.srs",
  "update_interval": "24h"
}
```
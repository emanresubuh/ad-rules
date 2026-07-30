# AdBlock Rules

## 订阅链接

```
https://raw.githubusercontent.com/emanresubuh/ad-rules/main/rule_srs/adblock_rules.srs
```

## 最新构建报告

## 📦 AdBlock Rules — 2026-07-30 12:45 CST

### 📊 本次统计

| 项目 | 数量 |
|---|---|
| 订阅源数量 | 3 个 |
| 订阅解析原始域名 | 264438 个 |
| 自定义屏蔽追加 | 6 个 |
| 白名单移除 | 1 个 |
| 子域名去冗余前 | 264443 个 |
| **最终规则数量** | **258683 个** |
| SRS 文件大小 | 1932.1 KB |

### 📈 变化对比

🔻 较上次减少 **2753** 条

### 📥 订阅源明细

  - `https://raw.githubusercontent.com/hagezi/dns-blocklists/main/adblock/pro.txt` → 解析出 **221198** 个域名
  - `https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/AWAvenue-Ads-Rule.txt` → 解析出 **897** 个域名
  - `https://anti-ad.net/adguard.txt` → 解析出 **101041** 个域名

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
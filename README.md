# AdBlock Rules

## 订阅链接

```
https://raw.githubusercontent.com/emanresubuh/ad-rules/main/rule_srs/adblock_rules.srs
```

## 最新构建报告

## 📦 AdBlock Rules — 2026-06-26 14:00 CST

### 📊 本次统计

| 项目 | 数量 |
|---|---|
| 订阅源数量 | 3 个 |
| 订阅解析原始域名 | 270533 个 |
| 自定义屏蔽追加 | 5 个 |
| 白名单移除 | 1 个 |
| 子域名去冗余前 | 270537 个 |
| **最终规则数量** | **265084 个** |
| SRS 文件大小 | 1998.0 KB |

### 📈 变化对比

🔺 较上次增加 **1239** 条

### 📥 订阅源明细

  - `https://raw.githubusercontent.com/hagezi/dns-blocklists/main/adblock/pro.txt` → 解析出 **228704** 个域名
  - `https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/AWAvenue-Ads-Rule.txt` → 解析出 **899** 个域名
  - `https://anti-ad.net/adguard.txt` → 解析出 **103144** 个域名

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
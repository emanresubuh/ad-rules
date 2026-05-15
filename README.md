# AdBlock Rules

## 订阅链接

```
https://raw.githubusercontent.com/emanresubuh/ad-rules/main/rule_srs/adblock_rules.srs
```

## 最新构建报告

## 📦 AdBlock Rules — 2026-05-15 21:24 CST

### 📊 本次统计

| 项目 | 数量 |
|---|---|
| 订阅源数量 | 6 个 |
| 订阅解析原始域名 | 298662 个 |
| 自定义屏蔽追加 | 1 个 |
| 白名单移除 | 1 个 |
| 子域名去冗余前 | 298661 个 |
| **最终规则数量** | **289553 个** |
| SRS 文件大小 | 2342.0 KB |

### 📈 变化对比

🔻 较上次减少 **8655** 条

### 📥 订阅源明细

  - `https://raw.githubusercontent.com/hagezi/dns-blocklists/main/adblock/pro.txt` → 解析出 **199973** 个域名
  - `https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/AWAvenue-Ads-Rule.txt` → 解析出 **905** 个域名
  - `https://anti-ad.net/adguard.txt` → 解析出 **106207** 个域名
  - `https://raw.githubusercontent.com/AdguardTeam/FiltersRegistry/master/filters/filter_11_Mobile/filter.txt` → 解析出 **1023** 个域名
  - `https://raw.githubusercontent.com/AdguardTeam/FiltersRegistry/master/filters/filter_15_DnsFilter/filter.txt` → 解析出 **164269** 个域名
  - `https://raw.githubusercontent.com/cjx82630/cjxlist/master/cjx-annoyance.txt` → 解析出 **188** 个域名

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
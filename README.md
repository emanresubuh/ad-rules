# AdBlock Rules

## 订阅链接

```
https://raw.githubusercontent.com/emanresubuh/ad-rules/main/rule_srs/adblock_rules.srs
```

## 最新构建报告

## 📦 AdBlock Rules — 2026-06-14 14:24 CST

### 📊 本次统计

| 项目 | 数量 |
|---|---|
| 订阅源数量 | 3 个 |
| 订阅解析原始域名 | 266773 个 |
| 自定义屏蔽追加 | 5 个 |
| 白名单移除 | 1 个 |
| 子域名去冗余前 | 266777 个 |
| **最终规则数量** | **261398 个** |
| SRS 文件大小 | 1938.0 KB |

### 📈 变化对比

🔺 较上次增加 **4024** 条

### 📥 订阅源明细

  - `https://raw.githubusercontent.com/hagezi/dns-blocklists/main/adblock/pro.txt` → 解析出 **222903** 个域名
  - `https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/AWAvenue-Ads-Rule.txt` → 解析出 **905** 个域名
  - `https://anti-ad.net/adguard.txt` → 解析出 **103464** 个域名

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
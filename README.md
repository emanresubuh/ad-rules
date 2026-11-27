# AdBlock Rules

## 订阅链接

```
https://raw.githubusercontent.com/emanresubuh/ad-rules/main/rule_srs/adblock_rules.srs
```

## 最新构建报告

## 📦 AdBlock Rules — 2026-11-27 22:50 CST

### 📊 本次统计

| 项目 | 数量 |
|---|---|
| 订阅源数量 | 5 个 |
| 订阅解析原始域名 | 281900 个 |
| 自定义屏蔽追加 | 91 个 |
| 白名单移除 | 2 个 |
| 子域名去冗余前 | 281988 个 |
| **最终规则数量** | **273706 个** |
| SRS 文件大小 | 2095.1 KB |

### 📈 变化对比

🔺 较上次增加 **5** 条

### 📥 订阅源明细

  - `https://raw.githubusercontent.com/hagezi/dns-blocklists/main/adblock/pro.txt` → 解析出 **240463** 个域名
  - `https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/AWAvenue-Ads-Rule.txt` → 解析出 **978** 个域名
  - `https://anti-ad.net/adguard.txt` → 解析出 **101924** 个域名
  - `https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists-legacy@latest/domains/native.vivo.txt` → 解析出 **306** 个域名
  - `https://gitlab.com/hagezi/mirror/-/raw/main/dns-blocklists/adblock/pro.txt?ref_type=heads` → 解析出 **240463** 个域名

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
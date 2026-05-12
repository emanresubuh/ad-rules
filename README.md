# AdBlock Rules

## 订阅链接

```
https://raw.githubusercontent.com/emanresubuh/ad-rules/main/rule_srs/adblock_rules.srs
```

## 最新构建报告

## 📦 AdBlock Rules — 2026-05-12 21:14 CST

### 📊 本次统计

| 项目 | 数量 |
|---|---|
| 订阅源数量 | 5 个 |
| 订阅解析原始域名 | 220717 个 |
| 自定义屏蔽追加 | 1 个 |
| 白名单移除 | 1 个 |
| 子域名去冗余前 | 220717 个 |
| **最终规则数量** | **215576 个** |
| SRS 文件大小 | 1658.2 KB |

### 📈 变化对比

🔺 较上次增加 **9** 条

### 📥 订阅源明细

  - `https://raw.githubusercontent.com/hagezi/dns-blocklists/main/adblock/native.vivo.txt` → 解析出 **237** 个域名
  - `https://raw.githubusercontent.com/hagezi/dns-blocklists/main/adblock/pro.txt` → 解析出 **182749** 个域名
  - `https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/AWAvenue-Ads-Rule.txt` → 解析出 **804** 个域名
  - `https://anti-ad.net/adguard.txt` → 解析出 **97055** 个域名
  - `https://raw.githubusercontent.com/AdguardTeam/FiltersRegistry/master/filters/filter_11_Mobile/filter.txt` → 解析出 **919** 个域名

### 🚀 使用方式

在 sing-box 配置中引用：

```json
{
  "type": "remote",
  "tag": "adblock",
  "url": "https://raw.githubusercontent.com/emanresubuh/ad-rules/main/rule_srs/adblock_rules.srs",
  "update_interval": "24h"
}
```
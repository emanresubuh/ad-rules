#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert.py - 增强安全版
针对 sing-box 1.13.x 优化
新增：Public Suffix 校验 + 私有域过滤 + CDN 误杀保护
"""

import re
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta
import requests

# -------- 配置区域 --------
SOURCE_FILE      = "source.txt"
BLOCK_FILE       = "custom_block.txt"
ALLOW_FILE       = "custom_allow.txt"
JSON_OUTPUT      = "adblock_rules.json"
SRS_OUTPUT       = "adblock_rules.srs"
STATS_FILE       = "stats.json"
REPORT_FILE      = "release_notes.md"
SING_BOX_BIN     = "sing-box"
RULESET_VERSION  = 2
TIMEOUT          = 60
CST              = timezone(timedelta(hours=8))
REPO_USER        = "emanresubuh"
REPO_NAME        = "ad-rules"
SRS_URL          = f"https://raw.githubusercontent.com/{REPO_USER}/{REPO_NAME}/main/rule_srs/adblock_rules.srs"

# PSL 下载地址
PSL_URL = "https://publicsuffix.org/list/public_suffix_list.dat"
# -------------------------

HOSTS_RE       = re.compile(r"^(?:0\.0\.0\.0|127\.0\.0\.1|::1)\s+([a-z0-9.-]+\.[a-z]{2,})")
ADGUARD_RE     = re.compile(r"^\|\|([a-z0-9.-]+\.[a-z]{2,})\^")
DOMAIN_RE      = re.compile(r"^([a-z0-9][a-z0-9-]{0,61}[a-z0-9](?:\.[a-z0-9][a-z0-9-]{0,61}[a-z0-9])+)$")

SKIP_LINE_RE   = re.compile(r"https?://|/")
COSMETIC_RE    = re.compile(r"#[@$?]?#|#%#|#script:")
PAGE_OPTION_RE = re.compile(r"\$(document|popup|genericblock|generichide|specifichide|third-party)")

INVALID_DOMAINS = {
    "localhost", "local", "broadcasthost", "ip6-localhost",
    "ip6-loopback", "ip6-localnet", "ip6-mcastprefix",
    "ip6-allnodes", "ip6-allrouters", "ip6-allhosts"
}

# 扩展 CDN + 主流服务白名单（防误杀核心）
WHITELIST_DOMAINS = {
    # GitHub & 开发平台
    "github.com", "githubusercontent.com", "raw.githubusercontent.com",
    "github.io", "vercel.app", "vercel.com", "pages.dev", "cloudflare.com",
    # 苹果
    "apple.com", "icloud.com", "mzstatic.com", "apple-dns.net",
    # Google
    "google.com", "gstatic.com", "googlesyndication.com", "doubleclick.net",
    # Microsoft
    "microsoft.com", "windows.com", "office.com", "live.com", "azure.com",
    # AWS & CDN
    "amazonaws.com", "cloudfront.net", "akamai.net", "akamaiedge.net",
    "akadns.net", "edgekey.net", "fastly.net", "fastlylb.net",
    # 其他主流 CDN / 服务
    "cdn77.net", "cdn77.org", "incapsula.com", "cloudflare.net",
    "bootstrapcdn.com", "jsdelivr.net", "cdnjs.com", "unpkg.com",
}

# 私有/保留域名后缀
PRIVATE_SUFFIXES = {".local", ".internal", ".lan", ".home", ".corp", ".test", ".example"}

# 全局 PSL Set（运行时加载）
PUBLIC_SUFFIXES = set()


def load_public_suffix_list():
    """下载并加载 Public Suffix List"""
    global PUBLIC_SUFFIXES
    print("[+] 正在加载 Public Suffix List...")
    try:
        resp = requests.get(PSL_URL, timeout=30)
        resp.raise_for_status()
        for line in resp.text.splitlines():
            line = line.strip().lower()
            if line and not line.startswith("//"):
                PUBLIC_SUFFIXES.add(line)
        print(f"[+] PSL 加载完成，共 {len(PUBLIC_SUFFIXES)} 条公共后缀")
    except Exception as e:
        print(f"[!] PSL 加载失败，使用内置保护: {e}")


def is_public_suffix(domain: str) -> bool:
    """检查域名是否为 Public Suffix 或其直接子域不应被完全屏蔽"""
    if not domain:
        return False
    parts = domain.split('.')
    # 检查是否为公共后缀本身
    if domain in PUBLIC_SUFFIXES:
        return True
    # 检查二级公共后缀（如 co.uk, github.io）
    if len(parts) >= 2:
        suffix = '.'.join(parts[-2:])
        if suffix in PUBLIC_SUFFIXES:
            return True
    return False


def normalize_domain(domain: str) -> str:
    return domain.strip().lower().lstrip('.').rstrip('.')


def load_sources(path: str) -> list:
    p = Path(path)
    if not p.is_file():
        print("[-] 错误: 找不到 " + path)
        exit(1)
    sources = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith(("#", "//", ";")):
                sources.append(line)
    return sources


def load_custom(path: str) -> set:
    p = Path(path)
    if not p.is_file():
        return set()
    domains = set()
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip().lower()
            if line and not line.startswith(("#", "//", ";")):
                d = normalize_domain(line)
                if DOMAIN_RE.match(d) and d not in INVALID_DOMAINS:
                    domains.add(d)
    return domains


def load_last_stats() -> dict:
    p = Path(STATS_FILE)
    if not p.is_file():
        return {}
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_stats(data: dict):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def fetch_text(url: str) -> str:
    print("[+] 正在抓取: " + url)
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print("[!] 抓取失败 " + url + ": " + str(e))
        return ""


def parse_rules(text: str) -> set:
    """增强版解析：PSL + 私有域 + CDN 保护"""
    domains = set()
    bad_keywords = {'/^', '/$', 'regex', 'domain=', '$dnstype', 'denyallow',
                   '[$', 'important', 'third-party', 'popup', 'generichide'}

    for line in text.splitlines():
        line = line.strip().lower()
        if not line:
            continue
        if line.startswith(("!", "#", "@@", "[adblock", ";")):
            continue
        if COSMETIC_RE.search(line) or PAGE_OPTION_RE.search(line):
            continue
        if SKIP_LINE_RE.search(line):
            continue
        if any(kw in line for kw in bad_keywords) or '*' in line:
            continue

        # 1. AdGuard 格式
        m = ADGUARD_RE.match(line)
        if m:
            d = normalize_domain(m.group(1))
            if should_keep_domain(d):
                domains.add(d)
            continue

        # 2. Hosts 格式
        m = HOSTS_RE.match(line)
        if m:
            d = normalize_domain(m.group(1))
            if should_keep_domain(d):
                domains.add(d)
            continue

        # 3. 纯域名兜底
        parts = line.split()
        if parts:
            candidate = normalize_domain(parts[0])
            if should_keep_domain(candidate):
                domains.add(candidate)

    return domains


def should_keep_domain(d: str) -> bool:
    """核心域名过滤逻辑"""
    if not d or len(d) < 4 or '.' not in d or '..' in d:
        return False
    if d in INVALID_DOMAINS or d in WHITELIST_DOMAINS:
        return False
    if any(d.endswith(suf) for suf in PRIVATE_SUFFIXES):
        return False
    if is_public_suffix(d) or any(is_public_suffix(s) for s in [d, '.'.join(d.split('.')[-2:])]):
        return False
    if not DOMAIN_RE.match(d):
        return False
    return True


def dedupe_subdomains(domains: set) -> list:
    sorted_domains = sorted(domains, key=lambda d: (d.split('.')[::-1], d))
    result = []
    domain_set = set(domains)
    for domain in sorted_domains:
        parts = domain.split('.')
        is_redundant = False
        for i in range(1, len(parts)):
            parent = '.'.join(parts[i:])
            if parent in domain_set:
                is_redundant = True
                break
        if not is_redundant:
            result.append(domain)
    return result


def generate_report(
    now_str, sources, source_counts, total_raw,
    custom_block_count, custom_allow_count, allow_removed,
    before_dedup, final_count, last_stats, srs_size_kb
):
    # （保持你原来的 generate_report 函数完全不变）
    last_count = last_stats.get("final_count", None)
    diff_str = "_(首次生成，无历史数据对比)_" if last_count is None else \
               (f"🔺 较上次增加 **{final_count - last_count}** 条" if final_count > last_count else
                f"🔻 较上次减少 **{last_count - final_count}** 条" if final_count < last_count else "➡️ 与上次相比无变化")

    source_lines = "\n".join(f"  - `{url}` → 解析出 **{source_counts.get(url, 0)}** 个域名" for url in sources)

    sing_box_snippet = f'''```json
{{
  "type": "remote",
  "tag": "adblock",
  "url": "{SRS_URL}",
  "update_interval": "24h"
}}
```'''

    lines = [
        f"## 📦 AdBlock Rules — {now_str}",
        "",
        "### 📊 本次统计", "",
        "| 项目 | 数量 |",
        "|---|---|",
        f"| 订阅源数量 | {len(sources)} 个 |",
        f"| 订阅解析原始域名 | {total_raw} 个 |",
        f"| 自定义屏蔽追加 | {custom_block_count} 个 |",
        f"| 白名单移除 | {allow_removed} 个 |",
        f"| 子域名去冗余前 | {before_dedup} 个 |",
        f"| **最终规则数量** | **{final_count} 个** |",
        f"| SRS 文件大小 | {round(srs_size_kb, 1)} KB |",
        "",
        "### 📈 变化对比", "", diff_str, "",
        "### 📥 订阅源明细", "", source_lines, "",
        "### 🚀 使用方式", "",
        "在 sing-box 配置中引用：", "", sing_box_snippet,
    ]
    return "\n".join(lines)


def main():
    print("[*] 启动转换流程 (sing-box v1.13.x) - PSL + CDN 安全版")
    load_public_suffix_list()

    now = datetime.now(CST)
    now_str = now.strftime("%Y-%m-%d %H:%M CST")

    sources = load_sources(SOURCE_FILE)
    all_domains: set = set()
    source_counts: dict = {}

    for url in sources:
        text = fetch_text(url)
        if text:
            extracted = parse_rules(text)
            source_counts[url] = len(extracted)
            print(f"[+] 解析出 {len(extracted)} 个独立域名")
            all_domains |= extracted

    if not all_domains:
        print("[-] 没有抓取到任何有效域名，任务停止。")
        return

    total_raw = len(all_domains)

    custom_block = load_custom(BLOCK_FILE)
    if custom_block:
        print(f"[+] 自定义屏蔽追加: {len(custom_block)} 个")
        all_domains |= custom_block

    custom_allow = load_custom(ALLOW_FILE)
    allow_removed = 0
    if custom_allow:
        before = len(all_domains)
        all_domains = {d for d in all_domains if not any(
            d == a or d.endswith('.' + a) or a.endswith('.' + d)
            for a in custom_allow
        )}
        allow_removed = before - len(all_domains)
        print(f"[+] 白名单放行: 移除 {allow_removed} 个域名")

    before_dedup = len(all_domains)
    print(f"[*] 去重前总计: {before_dedup} 个域名")
    deduped = dedupe_subdomains(all_domains)
    final_count = len(deduped)
    print(f"[*] 子域名去冗余后: {final_count} 个域名")

    # 生成 JSON
    ruleset_json = {"version": RULESET_VERSION, "rules": [{"domain_suffix": deduped}]}
    with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(ruleset_json, f, ensure_ascii=False, indent=2)

    # 编译 SRS
    print("[+] 正在编译 SRS...")
    try:
        result = subprocess.run(
            [SING_BOX_BIN, "rule-set", "compile", "--output", SRS_OUTPUT, JSON_OUTPUT],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("[#] SRS 编译成功")
        else:
            print("[!] 编译失败:\n" + result.stderr)
            exit(result.returncode)
    except FileNotFoundError:
        print("[-] sing-box 命令未找到")
        exit(1)

    srs_size_kb = Path(SRS_OUTPUT).stat().st_size / 1024

    last_stats = load_last_stats()
    report = generate_report(
        now_str, sources, source_counts, total_raw,
        len(custom_block), len(custom_allow), allow_removed,
        before_dedup, final_count, last_stats, srs_size_kb
    )

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(f"# AdBlock Rules\n\n## 订阅链接\n\n```\n{SRS_URL}\n```\n\n## 最新构建报告\n\n{report}")

    save_stats({"final_count": final_count, "updated_at": now_str})
    print("[+] 全部完成！")


if __name__ == "__main__":
    main()
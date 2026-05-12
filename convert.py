#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert.py
融合 217heidai 优化 + AdBlock + FakeIP Filter
所有输出文件统一存放到 rule_srs/ 目录
"""

import re
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta
import requests
from typing import Set, List, Dict

# -------- 配置区域 --------
SOURCE_FILE      = "source.txt"
BLOCK_FILE       = "custom_block.txt"
ALLOW_FILE       = "custom_allow.txt"

# 输出目录
OUTPUT_DIR       = Path("rule_srs")
OUTPUT_DIR.mkdir(exist_ok=True)

# AdBlock 输出
JSON_OUTPUT      = OUTPUT_DIR / "adblock_rules.json"
SRS_OUTPUT       = OUTPUT_DIR / "adblock_rules.srs"

# FakeIP Filter 输出
FAKEIP_JSON      = OUTPUT_DIR / "fakeipfilter.json"
FAKEIP_SRS       = OUTPUT_DIR / "fakeipfilter.srs"

STATS_FILE       = "stats.json"
REPORT_FILE      = "release_notes.md"
SING_BOX_BIN     = "sing-box"
RULESET_VERSION  = 2
TIMEOUT          = 60
CST              = timezone(timedelta(hours=8))

REPO_USER        = "emanresubuh"
REPO_NAME        = "ad-rules"
SRS_URL          = f"https://raw.githubusercontent.com/{REPO_USER}/{REPO_NAME}/main/rule_srs/adblock_rules.srs"
FAKEIP_SRS_URL   = f"https://raw.githubusercontent.com/{REPO_USER}/{REPO_NAME}/main/rule_srs/fakeipfilter.srs"

PSL_URL = "https://publicsuffix.org/list/public_suffix_list.dat"
# -------------------------

HOSTS_RE     = re.compile(r"^(?:0\.0\.0\.0|127\.0\.0\.1|::1)\s+([a-z0-9.-]+\.[a-z]{2,})")
ADGUARD_RE   = re.compile(r"^\|\|([a-z0-9*.-]+)\^")
DOMAIN_RE    = re.compile(r"^([a-z0-9][a-z0-9-]{0,61}[a-z0-9](?:\.[a-z0-9][a-z0-9-]{0,61}[a-z0-9])+\.?)$")

SKIP_LINE_RE   = re.compile(r"https?://|/")
COSMETIC_RE    = re.compile(r"#[@$?]?#|#%#|#script:")
PAGE_OPTION_RE = re.compile(r"\$(document|popup|genericblock|generichide|specifichide|third-party)")

INVALID_DOMAINS = {
    "localhost", "local", "broadcasthost", "ip6-localhost", "ip6-loopback",
    "ip6-localnet", "ip6-mcastprefix", "ip6-allnodes", "ip6-allrouters", "ip6-allhosts"
}

WHITELIST_DOMAINS = {
    "youtube.com", "youtu.be", "googlevideo.com", "ytimg.com",
    "google.com", "gstatic.com", "googleapis.com", "doubleclick.net", "googlesyndication.com",
    "apple.com", "icloud.com", "mzstatic.com", "apple-dns.net",
    "github.com", "githubusercontent.com", "raw.githubusercontent.com",
    "vercel.app", "pages.dev", "cloudflare.com", "fastly.net",
    "microsoft.com", "windows.com", "office.com"
}

PRIVATE_SUFFIXES = {".local", ".internal", ".lan", ".home", ".corp", ".test", ".example"}
PUBLIC_SUFFIXES: Set[str] = set()


def load_public_suffix_list():
    global PUBLIC_SUFFIXES
    print("[+] 正在加载 Public Suffix List...")
    try:
        resp = requests.get(PSL_URL, timeout=30)
        resp.raise_for_status()
        for line in resp.text.splitlines():
            line = line.strip().lower()
            if line and not line.startswith(("//", "!")):
                PUBLIC_SUFFIXES.add(line)
        print(f"[+] PSL 加载完成: {len(PUBLIC_SUFFIXES)} 条")
    except Exception as e:
        print(f"[!] PSL 加载失败: {e}")


def is_public_suffix(domain: str) -> bool:
    if not domain:
        return False
    if domain in PUBLIC_SUFFIXES:
        return True
    parts = domain.split('.')
    if len(parts) >= 2 and '.'.join(parts[-2:]) in PUBLIC_SUFFIXES:
        return True
    return False


def normalize_domain(domain: str) -> str:
    return domain.strip().lower().lstrip('.').rstrip('.')


def load_sources(path: str) -> List[str]:
    p = Path(path)
    if not p.is_file():
        print(f"[-] 错误: 找不到 {path}")
        exit(1)
    return [line.strip() for line in p.open(encoding="utf-8") 
            if line.strip() and not line.startswith(("#", "//", ";"))]


def load_custom(path: str) -> Set[str]:
    p = Path(path)
    if not p.is_file():
        return set()
    domains: Set[str] = set()
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip().lower()
            if line and not line.startswith(("#", "//", ";")):
                d = normalize_domain(line)
                if DOMAIN_RE.match(d) and d not in INVALID_DOMAINS:
                    domains.add(d)
    return domains


def fetch_text(url: str) -> str:
    print(f"[+] 正在抓取: {url}")
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"[!] 抓取失败 {url}: {e}")
        return ""


def parse_rules(text: str) -> Set[str]:
    domains: Set[str] = set()
    bad_keywords = {'/^', '/$', 'regex', 'domain=', '\( dnstype', 'denyallow', '[ \)', 
                   'important', 'third-party', 'popup', 'generichide', '*'}

    for line in text.splitlines():
        line = line.strip().lower()
        if not line or line.startswith(("!", "#", "@@", "[adblock", ";")):
            continue
        if COSMETIC_RE.search(line) or PAGE_OPTION_RE.search(line) or SKIP_LINE_RE.search(line):
            continue
        if any(kw in line for kw in bad_keywords):
            continue

        candidate = None
        m = ADGUARD_RE.match(line)
        if m:
            candidate = normalize_domain(m.group(1).replace('*', ''))
        elif (m := HOSTS_RE.match(line)):
            candidate = normalize_domain(m.group(1))
        else:
            parts = line.split()
            if parts:
                cand = normalize_domain(parts[0])
                if DOMAIN_RE.match(cand) and len(cand) >= 6 and cand.count('.') >= 1:
                    candidate = cand

        if candidate and should_keep_domain(candidate):
            domains.add(candidate)

    return domains


def should_keep_domain(d: str) -> bool:
    if not d or len(d) < 4 or '..' in d or d in INVALID_DOMAINS or d in WHITELIST_DOMAINS:
        return False
    if is_public_suffix(d) or any(d.endswith(s) for s in PRIVATE_SUFFIXES):
        return False
    if any(y in d for y in ["youtube", "googlevideo", "ytimg"]):
        return False
    if not DOMAIN_RE.match(d):
        return False
    return True


def dedupe_subdomains(domains: Set[str]) -> List[str]:
    sorted_domains = sorted(domains, key=lambda x: (len(x), x))
    result = []
    domain_set = set(domains)
    for domain in sorted_domains:
        is_redundant = False
        parts = domain.split('.')
        for i in range(1, len(parts)):
            parent = '.'.join(parts[i:])
            if parent in domain_set and parent != domain:
                is_redundant = True
                break
        if not is_redundant:
            result.append(domain)
    return result


def compile_to_srs(json_path: str, srs_path: str, name: str):
    print(f"[+] 正在编译 {name} → {srs_path}")
    try:
        subprocess.run(
            [SING_BOX_BIN, "rule-set", "compile", "--output", str(srs_path), str(json_path)],
            check=True, capture_output=True, text=True
        )
        print(f"[#] {name} 编译成功")
    except subprocess.CalledProcessError as e:
        print(f"[!] {name} 编译失败: {e.stderr}")
        exit(1)
    except FileNotFoundError:
        print("[-] sing-box 命令未找到")
        exit(1)


def process_fakeip_filter():
    print("[*] 开始处理 FakeIP Filter...")
    text = fetch_text(FAKEIP_URL.replace("rule_srs", "rule_json").replace(".srs", ".txt"))
    if not text:
        print("[!] FakeIP Filter 下载失败")
        return False

    try:
        with open(FAKEIP_JSON, "w", encoding="utf-8") as f:
            f.write(text.strip())
        print(f"[+] FakeIP JSON 已保存: {FAKEIP_JSON}")
        return True
    except Exception as e:
        print(f"[!] FakeIP 处理失败: {e}")
        return False


def load_last_stats() -> Dict:
    p = Path(STATS_FILE)
    if not p.is_file():
        return {}
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_stats(data: Dict):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def generate_report(
    now_str: str,
    sources: List[str],
    source_counts: Dict,
    total_raw: int,
    custom_block_count: int,
    custom_allow_count: int,
    allow_removed: int,
    before_dedup: int,
    final_count: int,
    last_stats: Dict,
    srs_size_kb: float
) -> str:
    last_count = last_stats.get("final_count")
    if last_count is None:
        diff_str = "_(首次生成，无历史数据对比)_"
    else:
        delta = final_count - last_count
        if delta > 0:
            diff_str = f"🔺 较上次增加 **{delta}** 条"
        elif delta < 0:
            diff_str = f"🔻 较上次减少 **{abs(delta)}** 条"
        else:
            diff_str = "➡️ 与上次相比无变化"

    source_lines = "\n".join(f"  - `{url}` → **{source_counts.get(url, 0)}** 个" for url in sources)

    lines = [
        f"## 📦 AdBlock Rules — {now_str}",
        "",
        "### 📊 本次统计",
        "",
        "| 项目 | 数量 |",
        "|---|---|",
        f"| 订阅源数量 | {len(sources)} 个 |",
        f"| 订阅解析原始域名 | {total_raw} 个 |",
        f"| 自定义屏蔽追加 | {custom_block_count} 个 |",
        f"| 白名单移除 | {allow_removed} 个 |",
        f"| 子域名去冗余前 | {before_dedup} 个 |",
        f"| **最终规则数量** | **{final_count} 个** |",
        f"| AdBlock SRS 大小 | {round(srs_size_kb, 1)} KB |",
        "",
        "### 📈 变化对比",
        "",
        diff_str,
        "",
        "### 📥 订阅源明细",
        "",
        source_lines,
        "",
        "### 🚀 使用方式",
        "",
        f"**AdBlock Rules**：\n`{SRS_URL}`",
        f"**FakeIP Filter**：\n`{FAKEIP_SRS_URL}`",
    ]
    return "\n".join(lines)


def main():
    print("[*] 启动 AdBlock + FakeIP Filter 转换流程")
    load_public_suffix_list()

    now = datetime.now(CST)
    now_str = now.strftime("%Y-%m-%d %H:%M CST")

    # ==================== AdBlock 处理 ====================
    sources = load_sources(SOURCE_FILE)
    all_domains: Set[str] = set()
    source_counts: Dict = {}

    for url in sources:
        text = fetch_text(url)
        if text:
            extracted = parse_rules(text)
            source_counts[url] = len(extracted)
            print(f"[+] 解析出 {len(extracted)} 个域名")
            all_domains |= extracted

    total_raw = len(all_domains)

    custom_block = load_custom(BLOCK_FILE)
    all_domains |= custom_block

    custom_allow = load_custom(ALLOW_FILE)
    allow_removed = 0
    if custom_allow:
        before = len(all_domains)
        all_domains = {d for d in all_domains if not any(
            d == a or d.endswith('.' + a) or a.endswith('.' + d) for a in custom_allow)}
        allow_removed = before - len(all_domains)

    before_dedup = len(all_domains)
    deduped = dedupe_subdomains(all_domains)
    final_count = len(deduped)

    ruleset_json = {"version": RULESET_VERSION, "rules": [{"domain_suffix": deduped}]}
    with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(ruleset_json, f, ensure_ascii=False, indent=2)

    compile_to_srs(JSON_OUTPUT, SRS_OUTPUT, "AdBlock")

    # ==================== FakeIP Filter 处理 ====================
    fakeip_success = process_fakeip_filter()
    if fakeip_success:
        compile_to_srs(FAKEIP_JSON, FAKEIP_SRS, "FakeIP Filter")

    # ==================== 报告 ====================
    srs_size_kb = SRS_OUTPUT.stat().st_size / 1024
    last_stats = load_last_stats()
    report = generate_report(
        now_str, sources, source_counts, total_raw,
        len(custom_block), len(custom_allow), allow_removed,
        before_dedup, final_count, last_stats, srs_size_kb
    )

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(f"# AdBlock Rules\n\n## 订阅链接\n\nAdBlock: {SRS_URL}\nFakeIP: {FAKEIP_SRS_URL}\n\n## 最新构建报告\n\n{report}")

    save_stats({"final_count": final_count, "updated_at": now_str})
    print(f"[+] 全部完成！文件已输出到 rule_srs/ 目录")


if __name__ == "__main__":
    main()
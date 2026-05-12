#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
convert.py
工业级安全版 sing-box SRS 规则转换器

功能:
- 下载广告规则
- 安全解析 Hosts / ABP DNS 规则
- 严格过滤非 DNS 规则
- 防止误杀主域
- 防止 Public Suffix 污染
- 防止 CDN / 多租户域误封
- 自定义 allow/block
- 输出 sing-box JSON
- 编译 SRS
"""

import json
import re
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta

import idna
import requests
from publicsuffix2 import PublicSuffixList


# =========================
# 配置
# =========================

SOURCE_FILE = "source.txt"

BLOCK_FILE = "custom_block.txt"
ALLOW_FILE = "custom_allow.txt"

JSON_OUTPUT = "adblock_rules.json"
SRS_OUTPUT = "adblock_rules.srs"

STATS_FILE = "stats.json"

SING_BOX_BIN = "sing-box"

RULESET_VERSION = 2

TIMEOUT = 60

CST = timezone(timedelta(hours=8))


# =========================
# Public Suffix
# =========================

psl = PublicSuffixList()


# =========================
# Regex
# =========================

DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)"
    r"(?:[a-z0-9]"
    r"(?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z]{2,63}$"
)


# =========================
# 内置保护
# =========================

INVALID_DOMAINS = {
    "localhost",
    "local",
    "broadcasthost",
    "ip6-localhost",
    "ip6-loopback",
    "ip6-localnet",
    "ip6-mcastprefix",
    "ip6-allnodes",
    "ip6-allrouters",
    "ip6-allhosts",
}

PRIVATE_SUFFIXES = {
    "local",
    "lan",
    "arpa",
    "home",
    "internal",
    "localhost",
    "invalid",
    "test",
}

HIGH_RISK_DOMAINS = {
    # CDN / 多租户 / 平台
    "cloudfront.net",
    "amazonaws.com",
    "github.io",
    "githubusercontent.com",
    "azureedge.net",
    "fastly.net",
    "akamai.net",
    "vercel.app",
    "workers.dev",
    "pages.dev",
    "netlify.app",
}

CRITICAL_DOMAINS = {
    "youtube.com",
    "google.com",
    "github.com",
    "apple.com",
    "icloud.com",
    "microsoft.com",
    "openai.com",
    "cloudflare.com",
}


# =========================
# 工具函数
# =========================

def normalize_domain(domain: str) -> str | None:
    """
    标准化域名
    """

    if not domain:
        return None

    domain = domain.strip().lower()

    domain = domain.lstrip(".").rstrip(".")

    if not domain:
        return None

    if ".." in domain:
        return None

    if len(domain) > 253:
        return None

    try:
        domain = idna.encode(domain).decode("ascii")
    except Exception:
        return None

    return domain


def is_public_suffix(domain: str) -> bool:
    """
    防止:
    com
    co.uk
    github.io
    """

    try:
        return domain == psl.get_public_suffix(domain)
    except Exception:
        return True


def is_private_domain(domain: str) -> bool:
    suffix = domain.split(".")[-1]
    return suffix in PRIVATE_SUFFIXES


def is_high_risk(domain: str) -> bool:
    return any(
        domain == d or domain.endswith("." + d)
        for d in HIGH_RISK_DOMAINS
    )


def validate_domain(domain: str) -> bool:

    if not domain:
        return False

    if domain in INVALID_DOMAINS:
        return False

    if not DOMAIN_RE.fullmatch(domain):
        return False

    if is_private_domain(domain):
        return False

    if is_public_suffix(domain):
        return False

    if is_high_risk(domain):
        return False

    return True


# =========================
# 规则类型过滤
# =========================

def should_skip(line: str) -> bool:

    if not line:
        return True

    # 注释
    if line.startswith(("!", "#", ";")):
        return True

    # 白名单
    if line.startswith("@@"):
        return True

    # cosmetic
    cosmetic_tokens = [
        "##",
        "#@#",
        "#$#",
        "#?#",
        "#%#",
    ]

    if any(token in line for token in cosmetic_tokens):
        return True

    # scriptlet
    if "#script:" in line:
        return True

    # regex
    if line.startswith("/") and line.endswith("/"):
        return True

    # URL/path
    if "://" in line:
        return True

    # 非 DNS 安全 modifier
    dangerous_modifiers = [
        "redirect",
        "replace",
        "removeparam",
        "csp",
        "urlblock",
    ]

    if any(mod in line for mod in dangerous_modifiers):
        return True

    return False


# =========================
# Parser
# =========================

def extract_abp_domain(line: str) -> str | None:
    """
    解析:
    ||example.com^
    ||example.com^$third-party
    """

    if not line.startswith("||"):
        return None

    body = line[2:]

    for sep in ["^", "$"]:
        if sep in body:
            body = body.split(sep, 1)[0]

    body = normalize_domain(body)

    if not body:
        return None

    if not DOMAIN_RE.fullmatch(body):
        return None

    return body


def extract_hosts_domain(line: str) -> str | None:

    parts = line.split()

    if len(parts) < 2:
        return None

    ip = parts[0]

    if ip not in {"0.0.0.0", "127.0.0.1", "::1"}:
        return None

    domain = normalize_domain(parts[1])

    if not domain:
        return None

    if not DOMAIN_RE.fullmatch(domain):
        return None

    return domain


def parse_rules(text: str) -> set:

    domains = set()

    for raw in text.splitlines():

        line = raw.strip().lower()

        if should_skip(line):
            continue

        domain = None

        # ABP DNS
        if line.startswith("||"):
            domain = extract_abp_domain(line)

        # Hosts
        elif line.startswith(("0.0.0.0", "127.0.0.1", "::1")):
            domain = extract_hosts_domain(line)

        # 纯域名
        elif DOMAIN_RE.fullmatch(line):
            domain = normalize_domain(line)

        if not domain:
            continue

        if validate_domain(domain):
            domains.add(domain)

    return domains


# =========================
# 文件
# =========================

def load_sources(path: str) -> list:

    p = Path(path)

    if not p.is_file():
        raise FileNotFoundError(path)

    result = []

    with p.open("r", encoding="utf-8") as f:
        for line in f:

            line = line.strip()

            if not line:
                continue

            if line.startswith(("#", ";", "//")):
                continue

            result.append(line)

    return result


def load_custom(path: str) -> set:

    p = Path(path)

    if not p.is_file():
        return set()

    domains = set()

    with p.open("r", encoding="utf-8") as f:

        for line in f:

            line = line.strip().lower()

            if not line:
                continue

            if line.startswith(("#", ";", "//")):
                continue

            domain = normalize_domain(line)

            if not domain:
                continue

            if validate_domain(domain):
                domains.add(domain)

    return domains


# =========================
# 网络
# =========================

def fetch_text(url: str) -> str:

    print(f"[+] 下载: {url}")

    try:

        r = requests.get(
            url,
            timeout=TIMEOUT,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        r.raise_for_status()

        return r.text

    except Exception as e:

        print(f"[!] 下载失败: {url}")
        print(f"    {e}")

        return ""


# =========================
# 主流程
# =========================

def main():

    print("[*] 启动安全规则转换")

    now = datetime.now(CST)

    print("[*] 时间:", now.strftime("%Y-%m-%d %H:%M:%S CST"))

    sources = load_sources(SOURCE_FILE)

    all_domains = set()

    for url in sources:

        text = fetch_text(url)

        if not text:
            continue

        parsed = parse_rules(text)

        print(f"[+] 提取域名: {len(parsed)}")

        all_domains |= parsed

    print(f"[*] 合并后域名总数: {len(all_domains)}")

    # =====================
    # custom block
    # =====================

    custom_block = load_custom(BLOCK_FILE)

    if custom_block:

        print(f"[+] 自定义屏蔽: {len(custom_block)}")

        all_domains |= custom_block

    # =====================
    # custom allow
    # =====================

    custom_allow = load_custom(ALLOW_FILE)

    if custom_allow:

        before = len(all_domains)

        all_domains = {
            d for d in all_domains
            if not any(
                d == a or d.endswith("." + a)
                for a in custom_allow
            )
        }

        removed = before - len(all_domains)

        print(f"[+] 白名单移除: {removed}")

    # =====================
    # Critical Check
    # =====================

    blocked_critical = sorted(
        d for d in all_domains
        if d in CRITICAL_DOMAINS
    )

    if blocked_critical:

        print("\n[!!!] 检测到关键域名被屏蔽:\n")

        for d in blocked_critical:
            print("   ", d)

        raise RuntimeError(
            "Critical domains detected"
        )

    # =====================
    # 输出 JSON
    # =====================

    final_domains = sorted(all_domains)

    ruleset_json = {
        "version": RULESET_VERSION,
        "rules": [
            {
                "domain_suffix": final_domains
            }
        ]
    }

    with open(JSON_OUTPUT, "w", encoding="utf-8") as f:

        json.dump(
            ruleset_json,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(f"[+] 已生成 JSON: {JSON_OUTPUT}")

    # =====================
    # 编译 SRS
    # =====================

    print("[+] 编译 SRS...")

    try:

        result = subprocess.run(
            [
                SING_BOX_BIN,
                "rule-set",
                "compile",
                "--output",
                SRS_OUTPUT,
                JSON_OUTPUT,
            ],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:

            print(result.stderr)

            raise RuntimeError(
                "sing-box compile failed"
            )

    except FileNotFoundError:

        raise RuntimeError(
            "未找到 sing-box"
        )

    size_kb = Path(SRS_OUTPUT).stat().st_size / 1024

    print(f"[+] SRS 编译完成: {SRS_OUTPUT}")
    print(f"[+] SRS 大小: {size_kb:.2f} KB")

    # =====================
    # stats
    # =====================

    stats = {
        "updated_at": now.isoformat(),
        "domains": len(final_domains),
        "srs_kb": round(size_kb, 2),
    }

    with open(STATS_FILE, "w", encoding="utf-8") as f:

        json.dump(
            stats,
            f,
            ensure_ascii=False,
            indent=2
        )

    print("[+] stats.json 已更新")

    print("\n[#] 完成")


if __name__ == "__main__":
    main()
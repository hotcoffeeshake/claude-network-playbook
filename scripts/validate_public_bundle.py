#!/usr/bin/env python3
"""扫描公开包中的常见秘密和机器专属值；不会读取 Git 忽略的私密目录。"""

from __future__ import annotations

import ipaddress
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_PUBLIC_IPS = {
    "1.0.0.1",
    "1.1.1.1",
    "8.8.8.8",
    "8.8.4.4",
    "223.5.5.5",
}
ALLOWED_SPECIAL_NETWORKS = tuple(
    ipaddress.ip_network(value)
    for value in (
        "100.64.0.0/10",
        "198.18.0.0/15",
        "224.0.0.0/4",
        "240.0.0.0/4",
    )
)
TEXT_SUFFIXES = {
    ".md", ".py", ".json", ".example", ".service", ".module",
    ".conf", ".txt", ".sh", ".gitignore",
}
PATTERNS = {
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "aws-access-key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "aws-secret-key-label": re.compile(r"(?i)aws_secret_access_key\s*=\s*[^<\s][^\s]*"),
    "trojan-uri": re.compile(r"(?i)trojan" + r"://(?!<)[^\s]+"),
    "home-path": re.compile(r"/Users" + r"/(?!<|\$|your-name\b|example\b)[^/\s]+/"),
    "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    "unsafe-tls-json": re.compile(r'"insecure"\s*:\s*true', re.I),
    "unsafe-tls-client": re.compile(r"(?i)allowInsecure\s*[=:]\s*(?:1|true|yes)"),
}
IPV4 = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")
PASSWORD_JSON = re.compile(r'"password"\s*:\s*"([^"]+)"')


def candidate_files() -> list[Path]:
    proc = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    result = []
    for raw in proc.stdout.split(b"\0"):
        if not raw:
            continue
        path = ROOT / raw.decode("utf-8")
        if path.is_file() and (path.suffix.lower() in TEXT_SUFFIXES or path.name == ".gitignore"):
            result.append(path)
    return result


def allowed_ip(value: str) -> bool:
    address = ipaddress.ip_address(value)
    if address.is_loopback or address.is_private or address.is_link_local:
        return True
    if value in ALLOWED_PUBLIC_IPS:
        return True
    if any(address in network for network in ALLOWED_SPECIAL_NETWORKS):
        return True
    return address in ipaddress.ip_network("192.0.2.0/24") or address in ipaddress.ip_network("198.51.100.0/24") or address in ipaddress.ip_network("203.0.113.0/24")


def main() -> int:
    findings: list[str] = []
    for path in candidate_files():
        relative = path.relative_to(ROOT)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(f"{relative}: 非 UTF-8 文本")
            continue
        for label, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append(f"{relative}:{line}: {label}")
        for match in PASSWORD_JSON.finditer(text):
            value = match.group(1)
            if not (value.startswith("<") and value.endswith(">")):
                line = text.count("\n", 0, match.start()) + 1
                findings.append(f"{relative}:{line}: non-placeholder-password")
        for match in IPV4.finditer(text):
            value = match.group(0)
            try:
                if not allowed_ip(value):
                    line = text.count("\n", 0, match.start()) + 1
                    findings.append(f"{relative}:{line}: unapproved-public-ip")
            except ValueError:
                continue
    if findings:
        print("公开包扫描未通过：", file=sys.stderr)
        for finding in findings:
            print("- " + finding, file=sys.stderr)
        return 1
    print(f"公开包扫描通过：检查 {len(candidate_files())} 个文本文件；未发现已定义的秘密模式。")
    print("此扫描不能证明 Git 历史或远端仓库从未包含秘密；发布前仍需人工复核 diff 和历史。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

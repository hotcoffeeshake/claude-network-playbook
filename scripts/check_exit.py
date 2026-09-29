#!/usr/bin/env python3
"""只检测代理出口，不验证防火墙、不启动Claude；不用账户或密钥。"""
import argparse
import ipaddress
import subprocess
import sys
from urllib.parse import urlsplit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-ip', required=True)
    parser.add_argument('--proxy', default='http://127.0.0.1:1082')
    args = parser.parse_args()
    expected = ipaddress.ip_address(args.expected_ip)
    proxy = urlsplit(args.proxy)
    if proxy.scheme != 'http' or proxy.hostname != '127.0.0.1' or proxy.username or proxy.password:
        parser.error('仅支持无凭据的127.0.0.1 HTTP代理')
    for url in ['https://api.ipify.org', 'https://checkip.amazonaws.com']:
        try:
            result = subprocess.run(
                ['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '15',
                 '--noproxy', '', '--proxy', args.proxy, url],
                capture_output=True, text=True, check=True, timeout=20)
            actual = ipaddress.ip_address(result.stdout.strip())
        except (subprocess.SubprocessError, ValueError, OSError) as exc:
            print('未通过：出口检测失败，未启动任何应用。'+type(exc).__name__)
            return 1
        if actual != expected:
            print('未通过：出口与本地指定基线不一致。')
            return 1
        print('通过：'+url+' 与指定基线一致')
    print('仅出口检测通过；另行核对DNS、WebRTC、防火墙及真实会话。')
    return 0

if __name__ == '__main__':
    sys.exit(main())

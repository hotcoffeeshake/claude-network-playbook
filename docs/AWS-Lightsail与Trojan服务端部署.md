# AWS Lightsail 与 Trojan 服务端部署

目标：在美国区域建立一台由你自己管理的 Ubuntu Lightsail，以静态 IPv4、Trojan over TCP 443 和受信任 TLS 证书提供固定出口。本页只使用占位符；账号、密码、设备凭据、SSH 私钥和真实公网地址不得写入仓库。

如果只需把已有服务接到第二台 Mac，不要重建服务器，直接执行[第二台 Mac 完整清单](第二台Mac完整执行清单.md)。创建实例会产生 AWS 费用，选择套餐和确认付款由账号持有人完成。

## 0. 准备和停止条件

准备一个自己控制、能添加 DNS A 记录的域名；以下用“TLS 域名”“静态 IPv4”“设备名”表示真实值。不要使用来历不明的共享域名、共享证书或公开二维码。

遇到以下情况立即停止，不继续覆盖：

- 账号、区域、套餐费用或现有实例归属不明确；
- 目标机已运行其他 sing-box、Nginx、Caddy 或占用 TCP 80/443 的业务；
- DNS A 记录尚未指向新静态 IPv4；
- 证书签发失败、名称不匹配或剩余有效期不足；
- 配置检查失败、服务启动失败或严格 TLS 客户端测试失败。

普通排障不要删除实例、静态 IP、证书目录或现有快照。先保留控制台和 SSH 回滚通道。

## 1. 创建 Lightsail 实例和固定地址

1. AWS Lightsail 控制台选择美国区域和一个可用区。
2. 平台选 Linux/Unix，蓝图选当前受支持的 Ubuntu LTS。
3. 选择满足预算的实例套餐，确认月费后再创建；名称可使用不含身份信息的用途名。
4. 实例进入 Running 后，打开 Networking，创建 Static IP 并绑定到该实例。
5. 在自己的 DNS 服务商添加 A 记录：TLS 域名指向静态 IPv4。没有部署 IPv6 服务时不要添加 AAAA。
6. 在 Lightsail IPv4 firewall 配置：

| 协议/端口 | 来源 | 用途 |
|---|---|---|
| TCP 22 | 当前管理公网 IPv4/32 | SSH 管理；先确认可登录再收紧 |
| TCP 80 | Any IPv4 | ACME HTTP-01 签发和续期 |
| TCP 443 | Any IPv4 | Trojan TLS 服务 |

不要开放公共 SOCKS/HTTP 管理端口。AWS 操作依据：[创建静态 IP](https://docs.aws.amazon.com/lightsail/latest/userguide/lightsail-create-static-ip.html)与[添加实例防火墙规则](https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-editing-firewall-rules.html)。

## 2. 首次登录和安装软件

通过 Lightsail 控制台的浏览器 SSH 或自己的 SSH 密钥登录。先更新系统，再安装 Certbot 和 sing-box 官方 APT 仓库版本：

~~~sh
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
sudo apt-get install -y ca-certificates curl certbot openssl

sudo mkdir -p /etc/apt/keyrings
sudo curl -fsSL https://sing-box.app/gpg.key -o /etc/apt/keyrings/sagernet.asc
sudo chmod a+r /etc/apt/keyrings/sagernet.asc
cat <<'EOF' | sudo tee /etc/apt/sources.list.d/sagernet.sources >/dev/null
Types: deb
URIs: https://deb.sagernet.org/
Suites: *
Components: *
Enabled: yes
Signed-By: /etc/apt/keyrings/sagernet.asc
EOF
sudo apt-get update
sudo apt-get install -y sing-box
/usr/bin/sing-box version
~~~

安装命令来源：[sing-box 官方包管理器文档](https://sing-box.sagernet.org/installation/package-manager/)。如果该页的仓库地址或安装方式已变化，以官方当前页面为准。官方包自带的 sing-box 服务不能与本仓库的专用服务同时占用 443；确认没有其他业务后停止并禁用默认实例：

~~~sh
sudo systemctl disable --now sing-box.service 2>/dev/null || true
sudo ss -lntp | grep -E ':(80|443)[[:space:]]' || true
~~~

若最后一条显示已有未知进程监听，停止部署并先查清用途。

## 3. 建立低权限运行目录

在服务器临时克隆公开仓库，或只把三个模板通过可信方式复制到服务器。公开仓库不含凭据。

~~~sh
sudo useradd --system --no-create-home --shell /usr/sbin/nologin personal-trojan 2>/dev/null || true
sudo install -d -m 750 -o root -g personal-trojan /etc/personal-trojan
sudo install -d -m 750 -o root -g personal-trojan /etc/personal-trojan/certs
sudo install -o root -g root -m 644 templates/personal-trojan.service.example /etc/systemd/system/personal-trojan.service
sudo systemctl daemon-reload
~~~

如果命令不是在仓库根目录执行，先改成模板的实际绝对路径。不要覆盖同名现有服务；已存在时先备份并比较。

## 4. 签发受信任证书

确认 DNS A 记录已生效且 TCP 80 可达后执行。尖括号内容在本机替换，不要把命令结果粘到公开日志：

~~~sh
sudo certbot certonly --standalone \
  --preferred-challenges http \
  --agree-tos --no-eff-email \
  --email '<ACME_EMAIL>' \
  -d '<TLS_DOMAIN>'
~~~

签发成功后保存 TLS 名称并安装续期部署钩子：

~~~sh
printf '%s\n' '<TLS_DOMAIN>' | sudo tee /etc/personal-trojan/tls-name >/dev/null
sudo chmod 640 /etc/personal-trojan/tls-name
sudo chown root:personal-trojan /etc/personal-trojan/tls-name
sudo install -o root -g root -m 750 templates/deploy-certificate.sh.example /usr/local/sbin/personal-trojan-deploy-cert
~~~

模板部署钩子会核对证书名称、有效期、链和私钥匹配，原子切换证书，检查 sing-box 配置，重启后做本机严格 TLS 探测；失败会回到上一代证书。

## 5. 本地生成第一台设备凭据和配置

每台设备使用独立随机密码。下面将密码写到 root-only 文件，不输出到终端；不要把该文件加入 Git、聊天或普通云盘。

~~~sh
sudo sh -c 'umask 077; openssl rand -base64 36 > /root/personal-trojan-device.secret'
sudo chmod 600 /root/personal-trojan-device.secret
~~~

将模板渲染为服务器配置。运行后按提示输入设备名和静态 IPv4；脚本从受限文件读取密码，不打印密码：

~~~sh
sudo python3 - <<'PY'
import grp, ipaddress, json, os, pathlib, re

template = pathlib.Path('templates/sing-box-server.json.example')
target = pathlib.Path('/etc/personal-trojan/config.json')
if target.exists():
    raise SystemExit('停止：目标配置已存在，不能覆盖')
device = input('设备名（仅字母数字和短横线）: ').strip()
static_ip = input('Lightsail 静态 IPv4: ').strip()
if not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,62}[A-Za-z0-9])?', device):
    raise SystemExit('停止：设备名格式无效')
address = ipaddress.ip_address(static_ip)
if address.version != 4 or not address.is_global:
    raise SystemExit('停止：必须填写全局可路由的静态 IPv4')
password = pathlib.Path('/root/personal-trojan-device.secret').read_text().strip()
data = json.loads(template.read_text())
user = data['inbounds'][0]['users'][0]
user['name'] = device
user['password'] = password
cidrs = data['route']['rules'][2]['ip_cidr']
cidrs[cidrs.index('<STATIC_IPV4>/32')] = static_ip + '/32'
temporary = target.with_suffix('.json.new')
temporary.write_text(json.dumps(data, indent=2) + '\n')
os.chmod(temporary, 0o640)
os.chown(temporary, 0, grp.getgrnam('personal-trojan').gr_gid)
temporary.replace(target)
PY
sudo runuser -u personal-trojan -- /usr/bin/sing-box check -c /etc/personal-trojan/config.json
~~~

只有检查成功才继续。配置使用服务器本机解析器并只接受 IPv4 解析结果；同时拒绝访问私网、回环、链路本地、基准测试网段、组播、保留地址、服务器自身地址及全部 IPv6，降低被当作内网跳板的风险。

## 6. 首次部署证书并启动服务

~~~sh
sudo env RENEWED_LINEAGE='/etc/letsencrypt/live/<TLS_DOMAIN>' /usr/local/sbin/personal-trojan-deploy-cert
sudo systemctl enable personal-trojan.service
sudo systemctl status personal-trojan.service --no-pager
sudo journalctl -u personal-trojan.service -n 50 --no-pager
~~~

最终必须同时满足配置检查通过、服务 active、严格 TLS 探测通过。

Certbot 通常已安装 renew timer。确认并做不消耗正式签发配额的演练：

~~~sh
sudo systemctl list-timers --all | grep certbot
sudo certbot renew --dry-run --deploy-hook /usr/local/sbin/personal-trojan-deploy-cert
~~~

如果本机 Certbot 的 systemd 单元没有持久调用部署钩子，在续期部署目录建立 root-owned 链接：

~~~sh
sudo ln -s /usr/local/sbin/personal-trojan-deploy-cert /etc/letsencrypt/renewal-hooks/deploy/personal-trojan-deploy-cert
~~~

## 7. 客户端填写方式和首轮验收

Shadowrocket 新建 Trojan 节点：地址填静态 IPv4 或 TLS 域名；端口 443；密码为该设备独立密码；TLS 开启；SNI 为 TLS 域名；允许不安全关闭；本方案不依赖 UDP。

先用全局代理单测该节点，暂不导入分流。两个出口检测站均应返回同一静态 IPv4。错误密码、错误 SNI 和停止服务三种测试都必须失败，不能回退直连。通过后再执行[第二台 Mac 完整清单](第二台Mac完整执行清单.md)。

密码从服务器 root-only 文件经密码管理器、加密点对点传输或现场输入交给目标设备。不要生成公开二维码，不要把密码拼成 Trojan URI 放入 shell 历史或聊天。

## 8. 为第二台设备添加独立身份

先在服务器生成新的 root-only 密码文件，再备份配置并添加用户。以下示例不会输出密码：

~~~sh
sudo sh -c 'umask 077; openssl rand -base64 36 > /root/personal-trojan-device2.secret'
sudo cp -a /etc/personal-trojan/config.json /etc/personal-trojan/config.json.before-device2
sudo python3 - <<'PY'
import grp, json, os, pathlib, re

path = pathlib.Path('/etc/personal-trojan/config.json')
data = json.loads(path.read_text())
name = input('第二台设备名: ').strip()
if not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,62}[A-Za-z0-9])?', name):
    raise SystemExit('停止：设备名格式无效')
users = data['inbounds'][0]['users']
if any(item.get('name') == name for item in users):
    raise SystemExit('停止：设备名已存在')
secret = pathlib.Path('/root/personal-trojan-device2.secret').read_text().strip()
users.append({'name': name, 'password': secret})
temporary = path.with_suffix('.json.new')
temporary.write_text(json.dumps(data, indent=2) + '\n')
os.chmod(temporary, 0o640)
os.chown(temporary, 0, grp.getgrnam('personal-trojan').gr_gid)
temporary.replace(path)
PY
if ! sudo runuser -u personal-trojan -- /usr/bin/sing-box check -c /etc/personal-trojan/config.json; then
  sudo cp -a /etc/personal-trojan/config.json.before-device2 /etc/personal-trojan/config.json
  exit 1
fi
if ! sudo systemctl restart personal-trojan.service; then
  sudo cp -a /etc/personal-trojan/config.json.before-device2 /etc/personal-trojan/config.json
  sudo systemctl restart personal-trojan.service
  exit 1
fi
sudo systemctl is-active --quiet personal-trojan.service
~~~

目标 Mac 验收成功后，安全删除服务器上的临时明文交付副本；服务配置中的密码仍用于认证，必须保持 0640。某设备丢失时只撤销该设备用户并重启，不轮换其他设备的身份。

## 9. 维护和回滚

~~~sh
sudo /usr/bin/sing-box check -c /etc/personal-trojan/config.json
sudo systemctl status personal-trojan.service --no-pager
sudo journalctl -u personal-trojan.service -n 50 --no-pager
sudo certbot certificates
sudo openssl s_client -connect 127.0.0.1:443 -servername '<TLS_DOMAIN>' -verify_hostname '<TLS_DOMAIN>' -verify_return_error -CApath /etc/ssl/certs </dev/null
~~~

修改配置前总是创建 root-only 备份；检查失败就恢复备份，不重启。服务异常时可停止专用服务，但保留实例、静态 IP、证书和 SSH 通道：

~~~sh
sudo systemctl disable --now personal-trojan.service
~~~

这只停止代理，不删除数据。确认恢复方案后再决定是否释放付费资源。

服务端字段依据：[Trojan 入站](https://sing-box.sagernet.org/configuration/inbound/trojan/)、[TLS 字段](https://sing-box.sagernet.org/configuration/shared/tls/)及[Certbot deploy hook](https://eff-certbot.readthedocs.io/en/stable/using.html#renewing-certificates)。正式执行前要用实际安装版本的 sing-box check 验证模板。

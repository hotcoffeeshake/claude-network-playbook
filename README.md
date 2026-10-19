# Claude 固定出口与国内服务分流手册

更新：2026-10-19。目标环境：**AWS Lightsail + Trojan/TCP/TLS** 服务端，以及另一台 **macOS + Shadowrocket + LuLu**。WireGuard 模板仅保留为历史参考。

**这不是运行中 IP 变化自动断流工具，也不是一键安装器。** 仓库提供固定节点分流、应用直连防护的配置方法、国内 DNS 例外及单次出口检查。新机器必须逐项配置和验收；克隆仓库不会安装防火墙、启动守护进程或保护正在运行的 Claude。

## 从这里开始

1. 先运行[公开包脱敏扫描](scripts/validate_public_bundle.py)。
2. 新建服务器时执行[AWS Lightsail 与 Trojan 服务端部署](docs/AWS-Lightsail与Trojan服务端部署.md)；已有服务器则跳过。
3. 目标电脑按[第二台 Mac 完整执行清单](docs/第二台Mac完整执行清单.md)顺序闭环；[旧版迁移说明](docs/另一台Mac部署.md)保留背景和详细验收原则。
4. [给新机器助手的交接说明](docs/新机器交接提示词.md)。
5. [现在如何保护、哪些没有实现](docs/保护机制与边界.md)：避免把启动前检查当成持续监控。
6. [哪些服务走中国流量](docs/国内流量与DNS清单.md)：业务流量和 DNS 分开说明。
7. [完整操作手册](docs/操作手册.md)：TLS 主通道、LuLu、Code、终端、手机。
8. [服务端模板](templates/sing-box-server.json.example)、[systemd 模板](templates/personal-trojan.service.example)、[证书部署钩子](templates/deploy-certificate.sh.example)、[分流与 DNS 模板](templates/shadowrocket-rules.conf.example)、[微信 DNS 模块](templates/wechat-developer-tools-dns.module)、[Code 环境模板](templates/claude-env.json)。
9. [无账号出口检查](scripts/check_exit.py)、[验证记录](docs/验证记录.md)、[教程文章](docs/教程避坑点与落地方案.md)与[来源](docs/来源.md)。

## 本版本交付范围

| 能力 | 仓库交付 |
|---|---|
| AWS 服务端 | 从实例、静态 IP、防火墙、证书、低权限服务、续期到回滚的手动步骤与脱敏模板 |
| Claude 固定美国节点 | 单成员 `US-FIXED` 分组模板；不含 DIRECT 或其他节点 |
| 国内服务分流 | Flova、Bilibili、飞书、抖音、小红书、WorkBuddy 等显式 DIRECT；国内 CDN 的定向 DNS |
| 限制 Claude 应用外部直连 | LuLu 配置及逐程序验证步骤；需要新机器实际安装、启用和验证 |
| 出口比对 | `check_exit.py` 手动执行一次，比对两个检测站；失败返回非零 |
| 启动阻止 | 旧机器曾有本机专用 CLI 包装器，**未交付为通用安装器**；旧检查器仍绑定历史节点，不应复制使用 |
| 运行中 IP 变化自动切断 | **未实现**；无常驻监控、自动停 Claude 或自动关闭转发功能 |

只包含脱敏文档、公开服务域名、占位模板和检查脚本。真实地址、节点凭据、密钥、账号、设备标识、原始日志及二维码不入库。本仓库公开可读，任何真实设备配置与凭据都必须留在仓库外。公开包扫描器用于阻止常见泄漏，但不能替代对 Git 历史和远端文件的人工复核。

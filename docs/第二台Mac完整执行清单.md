# 第二台 Mac 完整执行清单

本页是另一台 Mac 的顺序化闭环。目标是先证明独立 Trojan 节点可用，再合并 Shadowrocket 分流、Claude Code 环境和 LuLu 应用规则。仓库不含凭据，也不会自动修改系统。

## A. 克隆后先验证公开包

~~~sh
git clone https://github.com/hotcoffeeshake/claude-network-playbook.git
cd claude-network-playbook
python3 scripts/validate_public_bundle.py
python3 -m py_compile scripts/*.py
~~~

扫描失败就停止，不导入任何配置。真实静态 IP、TLS 域名、设备密码和本机路径从 Git 之外的安全渠道取得，保存到权限 0600 的本地目录；不要复用手机或第一台 Mac 的密码。

## B. 备份并确认本机端口

1. 备份 Shadowrocket 当前配置和用户目录下的 .claude/settings.json。
2. 安装并启用官方来源的 Shadowrocket、LuLu、Python 3 和要使用的 Claude 应用。
3. 在 Shadowrocket 查看本机 HTTP 代理端口。文档默认 127.0.0.1:1082；实际不同就统一改模板和 Claude Code env。
4. 不开启局域网共享，不导入来自公开聊天的节点二维码。

记录状态为“已备份”，此时还不能写“已生效”。

## C. 只测试独立 Trojan 节点

1. 新建节点 MY-US-TLS-FIXED：地址、443、独立密码、TLS 开启、SNI 为证书域名、允许不安全关闭。
2. Shadowrocket 使用全局代理；仅选该节点；关闭自动测速、失败回退和 DIRECT 回退。
3. 暂不导入仓库分流规则，先运行：

~~~sh
/usr/bin/curl --fail --silent --show-error --max-time 15 --proxy http://127.0.0.1:1082 https://api.ipify.org
/usr/bin/curl --fail --silent --show-error --max-time 15 --proxy http://127.0.0.1:1082 https://checkip.amazonaws.com
~~~

两个结果必须等于自己的静态 IPv4。若“已连接但零流量”，依次检查节点类型是否确为 Trojan、TCP 443、SNI、严格 TLS、设备密码、服务器服务状态和 Lightsail TCP 443 防火墙。不要先合并复杂规则，也不要改成允许不安全。

单测未通过就停止。通过后记录“节点已测试”，仍未完成应用保护。

## D. 分段合并 Shadowrocket 配置

1. 把 templates/shadowrocket-rules.conf.example 中的 VPS IPv4 占位符替换为自己的静态 IPv4，只存本地。
2. 先合并 General，保存后检查 DNS 键没有重复。
3. 再合并 Proxy Group：US-FIXED 恰好只含 MY-US-TLS-FIXED。
4. 再合并 Rule。VPS 的 DIRECT/no-resolve 规则必须位于所有代理规则之前，防止代理连接自身形成递归。
5. 再合并 Host 的最小国内 DNS 例外。
6. 保留现有 GEOIP、FINAL 和其他业务规则；模板是片段，禁止整份覆盖现有配置。
7. 全局路由切回“配置”，首页默认仍选固定节点，关闭回退。
8. 重开配置页和代理日志，确认实际运行配置与保存内容一致。

执行出口门槛：

~~~sh
python3 scripts/check_exit.py --expected-ip '<STATIC_IPV4>' --proxy http://127.0.0.1:1082
~~~

退出码不是 0 就不要启动 Claude。

## E. 合并 Claude Code 环境

完全退出 Claude/Code。只把 templates/claude-env.json 的 env 对象合并进用户 settings.json；保留原有 plugins、hooks 和权限设置，禁止用模板覆盖整个文件。

~~~sh
python3 -m json.tool ~/.claude/settings.json >/dev/null
~~~

检查用户设置、项目 .claude/settings.json、.claude/settings.local.json 和组织 managed settings 是否覆盖代理。重新启动后在 Code 的 /status 或当前版本提供的网络状态中确认代理。设置保存不等于进程已重新读取。

终端 npm CLI 如果仍共享系统 Node，标记为“未保护”；不要为共享 Node 建全局阻断规则。仓库未提供通用专用运行时安装器。

## F. 配置 LuLu 应用直连限制

按[操作手册第 5 节](操作手册.md#5-lulu-应用级直连保护)确认这台机器的实际可执行路径，为 Claude 主应用和桌面 Code 目录建立永久规则：外部地址阻止，本机回环代理允许。不要照抄旧机器用户名、UUID、哈希或下载路径，不要覆盖整份 LuLu 数据库。

确认 LuLu 网络扩展启用、非被动模式、没有更高优先级的放行。应用升级后重新核对路径和签名。

## G. 无账号故障注入

在可本机恢复的前提下，用与目标程序相同 LuLu 范围的无凭据探针逐项测试：

| 场景 | 通过条件 |
|---|---|
| 正常代理 | 可连接，两个出口站都是静态 IPv4 |
| 错误本地代理端口 | 请求失败，不能转为外部直连 |
| Shadowrocket 停止 | 受保护探针失败，不能显示家庭公网 IP |
| 外部 IPv4/IPv6 | 都被受保护程序范围阻止 |
| 本地回环 | Claude/Code 所需 IPC 正常 |
| 恢复代理 | 出口仍是同一静态 IPv4 |

不要为了测试停止唯一远程管理链路。仓库目前没有常驻监控器；运行期间出口改变不会自动终止 Claude 进程，这一项必须保持“未实现”。

## H. 国内业务和 DNS 验收

逐一打开实际使用的 Flova、Bilibili、飞书、抖音、小红书、WorkBuddy、微信开发者工具，核对 Shadowrocket 日志：业务规则命中 DIRECT，指定域名使用国内 DNS。DIRECT 的实际出口取决于当前网络，在海外网络不保证是中国 IP。

微信开发者工具只对 servicewechat.com 及其子域做国内 DNS 例外；不要扩大到全部腾讯域名。上传、登录、CDN 和长连接要分别测试，一个首页成功不能代替全部业务。

## I. 真实会话和重启验收

无账号测试全通过后才打开用户自己的 Claude 桌面和 Code：

1. 核对真实模型请求命中 US-FIXED；
2. 核对 Code 代理状态和 LuLu 对应进程日志；
3. 正常退出会话；
4. 重启 Mac；
5. 确认 LuLu 仍启用、Shadowrocket 使用正确配置和固定节点；
6. 重跑 check_exit.py，再做一次真实会话。

验收记录使用四种状态：

- 已保存：值写入配置；
- 已生效：运行组件读取了配置；
- 已测试：指定场景得到预期结果；
- 未验收：没有真实证据，不能写成完成。

## J. 回滚

先退出 Claude/Code。只移除本次添加的 Shadowrocket 规则、DNS 键、Code env 键和 LuLu 规则，恢复部署前备份；不要整份覆盖后来新增配置。节点单测仍失败时保留服务器和静态 IP，按服务端日志、证书、TCP 443、防火墙顺序排查。

最终交接不得包含设备密码、节点 URI、二维码、SSH 私钥、真实公网 IP、账号邮箱、认证日志或本机用户名路径。

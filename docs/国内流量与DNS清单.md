# 国内流量与 DNS 清单

日期：2026-10-02。DIRECT 表示从设备当前网络直连。在中国宽带上通常显示国内出口；到国外或叠加其他 VPN 时须重新测量，不能保证仍是中国 IP。

本表记录当前 Mac 核对到的规则和随仓库提供的显式模板。公开域名不含账号或凭据。模板不是整个现有订阅规则库的导出。

| 服务 | 国内直连域名 | 国内 DNS 例外 | 验证边界 |
|---|---|---|---|
| Flova | `flova.tv` 及子域 | `service.flova.tv`、`cdn-ap.flova.tv`、`static-cdn-ap.flova.tv` | API 账户查询曾实测成功；10月2日原始 PNG 完整下载与 CRC 校验通过；static CDN 仅验证 TLS/HTTP，上传及其他 CDN 单独测试 |
| Bilibili | `bilibili.com`、`biliapi.com`、`biliapi.net`、`bilivideo.com`、`bilivideo.cn`、`hdslb.com`、`acgvideo.com`、`b23.tv`、`biliimg.com`、`bilibili.tv` | 当前无专属覆写，使用默认 DNS | 分流规则已核对；所有视频/CDN 未逐项验收 |
| 飞书 | `feishu.cn` 及子域 | 根域及通配子域 → 国内 DNS | 其他上传/CDN、国际 Lark 不自动纳入 |
| 抖音 | `douyin.com`、`douyinvod.com`、`douyinpic.com`、`douyinstatic.com`、`iesdouyin.com` | 根域及通配子域 → 国内 DNS | 不等同于 TikTok 全部域名 |
| 小红书 | `xiaohongshu.com`、`xhscdn.com`、`xhslink.com` | 根域及通配子域 → 国内 DNS | 首页、短链和 CDN 连通曾测试；不代表所有业务 |
| WorkBuddy / CodeBuddy | `workbuddy.cn`、`codebuddy.cn`、`skillhub.cn`、`copilot.tencent.com`、`staging-copilot.tencent.com` | 前三者根域及通配子域、后两者精确域名 → 国内 DNS | 10月2日桌面同步握手、签到查询、技能列表恢复；模型生成未单独验收 |
| 腾讯/QQ基础域名 | `tencent.com`、`qq.com`、`tencent-cloud.net` | 仅上述 copilot 两个域名有例外 | 当前已有国内规则；不代表所有腾讯业务/CDN |
| Apple 登录/网站 | `apple.com`、`apple.com.cn`、`cdn-apple.com` | `appleid.cdn-apple.com`、`www.apple.com` | 来自现有直连规则；不代表 Claude 的 Apple 登录整条链路已验收 |
| 国内出口检测 | `myip.ipip.net` | 无额外覆写 | 用来检查 DIRECT；不应期待它显示美国 |

默认 DNS：Cloudflare DoH 经代理。表中的国内 DNS 例外使用 `server:223.5.5.5`，是动态查询而非固定 CDN IP。解析请求会发往国内 DNS，这是为国内直连服务有意设置的例外，不适用于 Claude 域名。浏览器通用 DNS 检测结果不能替代逐业务规则核对。

## 为什么不能只写 DIRECT

Flova 和 WorkBuddy 曾命中 DIRECT，却由海外 DoH 返回不适合当前国内路径的地址，造成 TLS 失败、延迟或同步断开。指定国内 DNS 后，这些业务仍然 DIRECT，但能选择国内 CDN。临时 curl --resolve 对照可以定位，长期规则不应写死短期 CDN 地址。

## 同时保留的美国流量

`claude.ai`、`claude.com`、`claude.app`、`claudemcpcontent.com`、`anthropic.com`、`claudeusercontent.com`、`anthropicusercontent.com` 和两个出口检测站绑定 US-FIXED。其中 `claude.ai`、`claude.com`、`anthropic.com` 和两个usercontent现有规则已核对；`claude.app`、`claudemcpcontent.com` 作为原仓库兼容域名继续显式绑定，并不表示本轮观察到它们的真实请求。

模板显式保留 `apple-relay.apple.com` 经 PROXY，置于宽泛 Apple DIRECT 之前，避免吞掉原有例外。它不是 Claude 固定出口组的一部分。

## 新域名怎么补

先重现一次失败，在 Shadowrocket 查请求域名、首条命中规则及 DNS 来源；无凭据比较默认路径和国内 DNS 地址，证书校验保持开启。确认属于预期国内业务后，仅补该服务的最小域名范围。不要为省事把全部 `.com`、腾讯云所有 IP 或 Claude 进程都设为 DIRECT。

国内网站可见国内出口，不表示 Claude 模型请求也直连；两者分开查看。反过来，单独检测站显示美国也不能替所有进程证明固定出口。

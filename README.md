# Container Forge · 容器镜像工坊

为 mihomo、FRP、rsyslog 和 wireproxy 提供可直接拉取的容器镜像，发布到 Docker Hub 和 GitHub Container Registry（GHCR）。按需选择镜像、准备软件配置，即可通过 Docker 或 Docker Compose 部署，无需克隆本仓库或自行构建。

本仓库由社区独立维护，与上游项目无隶属关系。各镜像的来源、标签和使用方式见下文。

[镜像目录](#镜像目录) · [快速开始](#快速开始) · [标签与架构](#标签与架构) · [镜像更新](#镜像更新) · [问题反馈](#问题反馈)

## 镜像目录

点击软件名称查看配置和部署说明；Docker Hub 和 GHCR 均提供对应镜像，可任选一个镜像仓库。

| 软件与使用文档 | 用途与特点 | Docker Hub | GHCR |
| --- | --- | --- | --- |
| [mihomo](mihomo/) | 代理核心；打包官方正式版和 Alpha 二进制，补齐 amd64 v1/v2/v3，不修改或重新编译核心 | [`aethersailor/mihomo`](https://hub.docker.com/r/aethersailor/mihomo) | [`ghcr.io/aethersailor/mihomo`](https://github.com/users/Aethersailor/packages/container/package/mihomo) |
| [FRP 客户端 frpc](frp/) | 内网穿透客户端；原样同步官方镜像，提供 `latest` 标签 | [`aethersailor/frpc`](https://hub.docker.com/r/aethersailor/frpc) | [`ghcr.io/aethersailor/frpc`](https://github.com/users/Aethersailor/packages/container/package/frpc) |
| [FRP 服务端 frps](frp/) | 内网穿透服务端；原样同步官方镜像，提供 `latest` 标签 | [`aethersailor/frps`](https://hub.docker.com/r/aethersailor/frps) | [`ghcr.io/aethersailor/frps`](https://github.com/users/Aethersailor/packages/container/package/frps) |
| [rsyslog-min-gtls](rsyslog-min-gtls/) | 精简日志接收服务；内置 GnuTLS，支持配置 TLS/mTLS | [`aethersailor/rsyslog-min-gtls`](https://hub.docker.com/r/aethersailor/rsyslog-min-gtls) | [`ghcr.io/aethersailor/rsyslog-min-gtls`](https://github.com/users/Aethersailor/packages/container/package/rsyslog-min-gtls) |
| [wireproxy](wireproxy/) | 用户态 WireGuard 代理；构建上游开发分支，包含队列扩容和 Landlock 补丁 | [`aethersailor/wireproxy`](https://hub.docker.com/r/aethersailor/wireproxy) | [`ghcr.io/aethersailor/wireproxy`](https://github.com/users/Aethersailor/packages/container/package/wireproxy) |

## 快速开始

使用前安装 Docker；使用 Compose 示例时，还需要 Docker Compose。

### 1. 选择并拉取镜像

以 mihomo 正式版为例：

```sh
docker pull aethersailor/mihomo:latest
```

如需使用 GHCR，改用以下地址：

```sh
docker pull ghcr.io/aethersailor/mihomo:latest
```

其他软件使用镜像目录中的地址，标签选择见下一节。

### 2. 准备配置并启动

拉取镜像后，按对应文档准备配置文件、挂载目录和端口，再启动容器：

- [mihomo](mihomo/#使用)：准备 `config.yaml`，使用文档中的 Compose 示例启动。TUN、透明代理等用法另见上游文档。
- [FRP](frp/#使用)：根据需要选择 frpc 或 frps，配置和启动参数参见 [FRP 官方文档](https://gofrp.org/zh-cn/docs/)。已有容器部署可替换为本仓库的对应镜像地址。
- [rsyslog-min-gtls](rsyslog-min-gtls/#快速开始)：可直接运行示例接收日志。默认监听 TCP/UDP 1514 并输出到 stdout；启用 TLS/mTLS 需要挂载自己的配置和证书。
- [wireproxy](wireproxy/#使用)：准备 WireGuard/wireproxy 配置，使用文档中的 Compose 示例启动。镜像以非 root 用户运行，配置需允许该用户读取；无需 TUN 设备或特权模式。

镜像提供软件运行环境，代理规则、连接凭据和证书等配置需自行准备。wireproxy 队列扩容会增加积压时的内存需求和排队延迟，不保证吞吐提升，详见[补丁说明](wireproxy/#补丁范围)。

## 标签与架构

下表中的架构均指 Linux 容器平台。具体版本标签以镜像仓库中已发布的内容为准。

| 软件 | 标签选择 | 支持架构 |
| --- | --- | --- |
| mihomo | `latest` 为最新正式版；`Alpha` 为最新 Alpha，注意大写 `A`；`v1.x.x` 为已同步的指定正式版 | amd64 v1/v2/v3、386、arm64、arm/v7 |
| frpc / frps | `latest` 跟随官方最新正式版；`vX.Y.Z` 为已同步的指定版本 | 保留官方镜像的完整多架构清单，具体平台见对应镜像标签 |
| rsyslog-min-gtls | `latest` 为最新构建的 rsyslog v8；`v8.x.y` 为已发布的指定版本 | amd64 |
| wireproxy | `latest` 跟随上游 `master`，包含本仓库补丁，不代表官方正式 Release | amd64、arm64 |

mihomo 另提供 `latest-amd64-v1`、`latest-amd64-v2`、`latest-amd64-v3` 等固定指令等级的标签；Alpha 和版本标签也有对应后缀。所选等级须由 CPU 支持，详见 [mihomo 标签说明](mihomo/#选择标签)。

版本标签可能因基础镜像刷新或上游同版本重发而更新。需要固定镜像内容时，使用对应镜像仓库中的 digest（`镜像地址@sha256:…`）。

## 镜像更新

| 软件 | 自动更新方式 |
| --- | --- |
| mihomo | 每 30 分钟检查正式版和 Alpha；每天完整重建，刷新基础镜像和系统包 |
| frpc / frps | 每 6 小时检查官方版本和镜像 digest，原样同步变化 |
| rsyslog-min-gtls | 每天跟踪最新 rsyslog v8 并完整重建，刷新基础镜像和系统包 |
| wireproxy | 每天跟踪上游 `master` 并完整重建，刷新基础镜像和系统包 |

定时任务的实际执行时间可能延迟，执行记录见 [GitHub Actions](https://github.com/Aethersailor/container-forge/actions)。镜像仓库发布更新后，已运行的容器仍需自行更新。

使用 Docker Compose 部署时，在对应的 `compose.yaml` 所在目录运行：

```sh
docker compose pull
docker compose up -d
```

mihomo 和 FRP 会跟随上游撤下已撤回的版本，并调整 `latest`；已拉取到本地的镜像不受影响。历史版本保留范围及具体更新行为见各软件的使用文档。

## 问题反馈

镜像拉取、标签、架构、容器启动或本仓库补丁的问题，可在 [Issues](https://github.com/Aethersailor/container-forge/issues) 反馈。请提供镜像地址与标签、宿主机架构、Docker 版本、启动命令或 Compose 配置，以及相关错误日志。提交前移除密码、Token、私钥等敏感信息。

软件功能和配置用法可先查阅上游项目：[mihomo](https://github.com/MetaCubeX/mihomo)、[FRP](https://github.com/fatedier/frp)、[rsyslog](https://github.com/rsyslog/rsyslog)、[wireproxy](https://github.com/windtf/wireproxy)。

## 维护与许可

维护或新增镜像工程的约定见 [AGENTS.md](AGENTS.md)。各软件及打包文件遵循对应许可证，具体见各目录的 README 和许可证文件。

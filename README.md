# Container Forge · 容器镜像工坊

Container Forge 收纳社区维护的容器镜像打包与分发项目，为软件补齐容器部署、多架构支持或镜像分发能力。镜像发布到 Docker Hub 和 GitHub Container Registry（GHCR），可直接通过 Docker 或 Docker Compose 使用，无需克隆本仓库或自行构建。

目前已提供 mihomo、FRP、rsyslog 和 wireproxy 镜像。未来会继续增加更多软件的打包内容，包括为官方尚未提供 Docker 镜像的软件提供社区容器镜像。已可用的内容以镜像目录为准。

本仓库由社区独立维护，与上游项目无隶属关系。各镜像的来源、标签和使用方式见下文。

[镜像目录](#镜像目录) · [与官方镜像的区别](#与官方镜像的区别) · [快速开始](#快速开始) · [标签与架构](#标签与架构) · [镜像更新](#镜像更新) · [问题反馈](#问题反馈)

## 镜像目录

以下为当前已提供的镜像。点击软件名称查看配置和部署说明；Docker Hub 和 GHCR 均提供对应镜像，可任选一个镜像仓库。

| 软件与使用文档 | 用途与特点 | Docker Hub | GHCR |
| --- | --- | --- | --- |
| [mihomo](mihomo/) | 代理核心；打包官方正式版和 Alpha 二进制，补齐 amd64 v1/v2/v3，不修改或重新编译核心 | [`aethersailor/mihomo`](https://hub.docker.com/r/aethersailor/mihomo) | [`ghcr.io/aethersailor/mihomo`](https://github.com/users/Aethersailor/packages/container/package/mihomo) |
| [FRP 客户端 frpc](frp/) | 内网穿透客户端；原样同步官方镜像，提供 `latest` 标签 | [`aethersailor/frpc`](https://hub.docker.com/r/aethersailor/frpc) | [`ghcr.io/aethersailor/frpc`](https://github.com/users/Aethersailor/packages/container/package/frpc) |
| [FRP 服务端 frps](frp/) | 内网穿透服务端；原样同步官方镜像，提供 `latest` 标签 | [`aethersailor/frps`](https://hub.docker.com/r/aethersailor/frps) | [`ghcr.io/aethersailor/frps`](https://github.com/users/Aethersailor/packages/container/package/frps) |
| [rsyslog-min-gtls](rsyslog-min-gtls/) | 精简日志接收服务；内置 GnuTLS，支持配置 TLS/mTLS | [`aethersailor/rsyslog-min-gtls`](https://hub.docker.com/r/aethersailor/rsyslog-min-gtls) | [`ghcr.io/aethersailor/rsyslog-min-gtls`](https://github.com/users/Aethersailor/packages/container/package/rsyslog-min-gtls) |
| [wireproxy](wireproxy/) | 用户态 WireGuard 代理；构建上游开发分支，包含队列扩容和 Landlock 补丁 | [`aethersailor/wireproxy`](https://hub.docker.com/r/aethersailor/wireproxy) | [`ghcr.io/aethersailor/wireproxy`](https://github.com/users/Aethersailor/packages/container/package/wireproxy) |

## 与官方镜像的区别

当前收录的四个软件均已有上游官方镜像。本仓库分别提供额外的打包选项、标签维护或功能裁剪；选择前可先对照自己的需求。

| 软件 | 官方镜像 | 本仓库提供的区别 |
| --- | --- | --- |
| [mihomo](mihomo/#与官方镜像的区别) | 已有：[`metacubex/mihomo`](https://hub.docker.com/r/metacubex/mihomo) | 官方当前的 amd64 镜像使用 v1 二进制；本仓库打包未修改的官方二进制，提供 amd64 v1/v2/v3 选择、GHCR 分发和每日基础镜像刷新，核心功能不作改动 |
| [FRP（frpc / frps）](frp/#与官方镜像的区别) | 已有：Docker Hub 的 [`fatedier/frpc`](https://hub.docker.com/r/fatedier/frpc)、[`fatedier/frps`](https://hub.docker.com/r/fatedier/frps)，以及官方 GHCR 地址 | 从官方 GHCR 原样同步，保留镜像内容和多架构清单，主要增加跟随正式版的 `latest` 标签及社区分发地址；没有额外的 FRP 功能 |
| [rsyslog-min-gtls](rsyslog-min-gtls/#与官方镜像的区别) | 已有：[`rsyslog/rsyslog`](https://hub.docker.com/r/rsyslog/rsyslog)、[`rsyslog/rsyslog-minimal`](https://hub.docker.com/r/rsyslog/rsyslog-minimal)、[`rsyslog/rsyslog-collector`](https://hub.docker.com/r/rsyslog/rsyslog-collector) 等 | 采用 Debian stable-slim 和源码编译，仅保留网络日志及 GnuTLS 所需模块，默认 TCP/UDP 1514 → stdout；官方 collector 也支持 TLS，本镜像侧重精简配置和模块范围 |
| [wireproxy](wireproxy/#与官方镜像的区别) | 已有：[`ghcr.io/windtf/wireproxy`](https://github.com/windtf/wireproxy/pkgs/container/wireproxy) | 在上游 `master` 基础上应用队列扩容和 Landlock 补丁，使用 Alpine 运行镜像，提供 Docker Hub 分发和每日重建；属于带补丁的构建 |

需要官方原始构建时，可直接使用官方镜像；需要表中的具体差异时，再选择本仓库镜像。官方来源、详细差异及使用条件见各软件 README。

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
- [FRP](frp/#使用)：根据需要部署 frps 服务端和 frpc 客户端，文档提供配置文件和 Compose 示例。已有容器部署可替换为本仓库的对应镜像地址。
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

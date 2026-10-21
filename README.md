# Container Forge · 容器镜像工坊

Container Forge 收纳社区维护的容器镜像打包与分发项目，为软件补齐容器部署、多架构支持或镜像分发能力。镜像发布到 Docker Hub 和 GitHub Container Registry（GHCR），可直接通过 Docker 或 Docker Compose 使用，无需克隆本仓库或自行构建。

打包内容会持续扩充，也会为官方尚未提供 Docker 镜像的软件增加社区打包。已发布的项目见下方镜像目录。

本仓库由社区独立维护，与上游项目无隶属关系。每个项目分别说明用途、官方镜像情况、本仓库的差异和使用方式。

[镜像目录](#镜像目录) · [使用与更新](#使用与更新) · [问题反馈](#问题反馈)

## 镜像目录

展开需要的软件，查看镜像地址、标签和部署入口。各项目独立维护，具体版本标签以对应镜像仓库中已发布的内容为准。

<details>
<summary><strong>mihomo · 代理核心与规则路由</strong></summary>

**用途**：通过容器部署 mihomo 代理核心，按配置中的节点和规则处理应用流量。

**官方镜像**：已有 [`metacubex/mihomo`](https://hub.docker.com/r/metacubex/mihomo)。官方当前的 amd64 镜像使用 v1 二进制。

**本仓库的区别**：直接打包未修改的官方正式版和 Alpha 二进制，提供 amd64 v1/v2/v3 选择、固定指令等级标签、GHCR 分发和每日基础镜像刷新。核心功能不作改动，配置目录和启动参数沿用官方镜像。详细来源和对比见[项目说明](mihomo/#与官方镜像的区别)。

| 镜像仓库 | 地址 |
| --- | --- |
| [Docker Hub](https://hub.docker.com/r/aethersailor/mihomo) | `aethersailor/mihomo` |
| [GHCR](https://github.com/users/Aethersailor/packages/container/package/mihomo) | `ghcr.io/aethersailor/mihomo` |

**标签与架构**：

- `latest`：最新正式版；`Alpha`：最新 Alpha，注意大写 `A`；`v1.x.x`：已同步的指定正式版。
- 支持 Linux amd64 v1/v2/v3、386、arm64、arm/v7。固定指令等级可使用 `latest-amd64-v1`、`latest-amd64-v2`、`latest-amd64-v3`，Alpha 和版本标签也有对应后缀；所选等级须由 CPU 支持。

**使用**：准备 `config.yaml`，按 [Compose 部署示例](mihomo/#使用)启动。普通代理端口、TUN 和透明代理的配置要求见项目文档及 [mihomo 官方文档](https://wiki.metacubex.one/)。

**更新**：每 30 分钟检查正式版和 Alpha，每天完整重建以刷新基础镜像和系统包。官方撤回版本后会移除对应标签，并调整 `latest`；首次同步不回填全部历史版本，详见[更新说明](mihomo/#更新镜像)。

</details>

<details>
<summary><strong>FRP · 内网穿透客户端与服务端</strong></summary>

**用途**：通过具有公网地址的 frps 服务端访问内网服务；frpc 客户端部署在能够访问目标内网服务的设备上。

**官方镜像**：已有 Docker Hub 的 [`fatedier/frpc`](https://hub.docker.com/r/fatedier/frpc)、[`fatedier/frps`](https://hub.docker.com/r/fatedier/frps)，以及 `ghcr.io/fatedier/frpc`、`ghcr.io/fatedier/frps`。官方目前按版本号发布标签，未提供 `latest`。

**本仓库的区别**：从官方 GHCR 按 digest 原样复制，保留镜像内容和完整多架构清单，维护跟随正式版的 `latest` 标签及社区分发地址。不重新构建或修改 FRP，没有额外的协议、配置项或性能补丁。详细来源和对比见[项目说明](frp/#与官方镜像的区别)。

| 组件 | Docker Hub | GHCR |
| --- | --- | --- |
| 客户端 frpc | [`aethersailor/frpc`](https://hub.docker.com/r/aethersailor/frpc) | [`ghcr.io/aethersailor/frpc`](https://github.com/users/Aethersailor/packages/container/package/frpc) |
| 服务端 frps | [`aethersailor/frps`](https://hub.docker.com/r/aethersailor/frps) | [`ghcr.io/aethersailor/frps`](https://github.com/users/Aethersailor/packages/container/package/frps) |

**标签与架构**：

- `latest`：当前可用的官方最新正式版；`vX.Y.Z`：已同步的指定版本。
- 保留官方镜像的完整多架构清单，具体 Linux 平台见对应镜像标签。

**使用**：按[配置与 Compose 示例](frp/#使用)分别部署 frps 和 frpc，准备认证信息、配置文件及端口映射。已有 FRP 容器部署可替换对应镜像地址，保留配置和参数。其他用法见 [FRP 官方文档](https://gofrp.org/zh-cn/docs/)。

**更新**：每 6 小时检查官方版本和镜像 digest，已同步的历史版本也会跟随同版本重发。官方撤回版本时会同步撤下对应标签，并调整 `latest`，详见[更新说明](frp/#更新镜像)。原样同步有检查间隔，不保证与官方同时更新。

</details>

<details>
<summary><strong>rsyslog-min-gtls · 精简网络日志接收服务</strong></summary>

**用途**：集中接收 TCP/UDP syslog 日志，或配合自备配置与证书使用 TLS/mTLS。

**官方镜像**：已有 [`rsyslog/rsyslog`](https://hub.docker.com/r/rsyslog/rsyslog)、[`rsyslog/rsyslog-minimal`](https://hub.docker.com/r/rsyslog/rsyslog-minimal)、[`rsyslog/rsyslog-collector`](https://hub.docker.com/r/rsyslog/rsyslog-collector) 等[官方镜像](https://docs.rsyslog.com/doc/containers/user_images.html)。官方 collector 同样支持可选的 TLS 接收。

**本仓库的区别**：采用 Debian stable-slim 和源码编译，运行镜像仅保留网络日志输入及 GnuTLS 等所需模块，默认监听 TCP/UDP 1514 并输出到 stdout。官方镜像系列采用 Ubuntu LTS 和软件包安装，模块组合、默认端口和配置方式不同。详细对比及模块清单见[项目说明](rsyslog-min-gtls/#与官方镜像的区别)。

| 镜像仓库 | 地址 |
| --- | --- |
| [Docker Hub](https://hub.docker.com/r/aethersailor/rsyslog-min-gtls) | `aethersailor/rsyslog-min-gtls` |
| [GHCR](https://github.com/users/Aethersailor/packages/container/package/rsyslog-min-gtls) | `ghcr.io/aethersailor/rsyslog-min-gtls` |

**标签与架构**：

- `latest`：最新构建的 rsyslog v8；`v8.x.y`：已发布的指定版本。
- 支持 Linux amd64。

**使用**：按[快速开始](rsyslog-min-gtls/#快速开始)或 [Compose 示例](rsyslog-min-gtls/#使用-docker-compose)启动。默认接收明文日志；启用 TLS/mTLS 需要挂载自己的配置和证书。使用自定义配置前需核对内置模块，本镜像不提供官方 collector 的环境变量开关，详见[配置说明](rsyslog-min-gtls/#自定义配置与-tlsmtls)。

**更新**：每天跟踪最新 rsyslog v8 并完整重建，刷新基础镜像和系统包，详见[更新说明](rsyslog-min-gtls/#更新镜像)。

</details>

<details>
<summary><strong>wireproxy · 用户态 WireGuard 代理</strong></summary>

**用途**：将 WireGuard 连接提供为 SOCKS5、HTTP 代理或隧道，让指定应用经 WireGuard 出站。

**官方镜像**：已有 [`ghcr.io/windtf/wireproxy`](https://github.com/windtf/wireproxy/pkgs/container/wireproxy)，官方的 `latest` 同样跟随上游 `master` 开发分支。

**本仓库的区别**：在上游 `master` 基础上应用指定的队列扩容和 Landlock 补丁，使用 Alpine 运行镜像，提供 Docker Hub 分发和每日完整重建。官方使用 Distroless nonroot；非 root 和用户态代理是共同能力。详细对比见[项目说明](wireproxy/#与官方镜像的区别)。

| 镜像仓库 | 地址 |
| --- | --- |
| [Docker Hub](https://hub.docker.com/r/aethersailor/wireproxy) | `aethersailor/wireproxy` |
| [GHCR](https://github.com/users/Aethersailor/packages/container/package/wireproxy) | `ghcr.io/aethersailor/wireproxy` |

**标签与架构**：

- `latest`：上游 `master` 加本仓库补丁，不代表官方正式 Release。
- 支持 Linux amd64、arm64。

**使用**：准备可用的 WireGuard/wireproxy 配置，按 [Compose 部署示例](wireproxy/#使用)启动。镜像以 `65532:65532` 运行，配置需允许该用户读取；纯用户态代理不需要 TUN 设备、特权模式或 `NET_ADMIN`。

队列扩容会增加积压时的内存需求和排队延迟，不保证吞吐提升，也不代表同等数量的并发连接，详见[补丁说明](wireproxy/#补丁范围)。

**更新**：每天跟踪最新 `master` 并完整重建，刷新基础镜像和系统包。版本和构建来源的查看方法见[更新说明](wireproxy/#更新镜像与查看版本)。

</details>

## 使用与更新

使用前安装 Docker；使用 Compose 示例时，还需要 Docker Compose。展开所需项目，选择镜像地址和标签，再按对应文档准备配置、挂载目录和端口。代理规则、连接凭据和证书等配置需自行准备。

使用 Docker Compose 部署时，在准备好配置和 `compose.yaml` 后运行：

```sh
docker compose up -d
```

更新已有部署时，在对应的 `compose.yaml` 所在目录运行：

```sh
docker compose pull
docker compose up -d
```

版本标签可能因基础镜像刷新或上游同版本重发而更新。需要固定镜像内容时，使用对应镜像仓库中的 digest（`镜像地址@sha256:…`）。版本撤回不影响已拉取到本地的镜像，具体行为见各项目文档。

定时任务的实际执行时间可能延迟，执行记录见 [GitHub Actions](https://github.com/Aethersailor/container-forge/actions)。镜像仓库发布更新后，已运行的容器仍需自行更新。

## 问题反馈

镜像拉取、标签、架构、容器启动或本仓库补丁的问题，可在 [Issues](https://github.com/Aethersailor/container-forge/issues) 反馈。请提供镜像地址与标签、宿主机架构、Docker 版本、启动命令或 Compose 配置，以及相关错误日志。提交前移除密码、Token、私钥等敏感信息。

软件功能和配置用法可查阅对应项目文档中的上游入口。

## 维护与许可

维护或新增镜像工程的约定见 [AGENTS.md](AGENTS.md)。各软件及打包文件遵循对应许可证，具体见各目录的 README 和许可证文件。

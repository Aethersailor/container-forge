# 🔐 wireproxy

[wireproxy](https://github.com/windtf/wireproxy) 是用户态 WireGuard 客户端，可将 WireGuard 连接提供为 SOCKS5、HTTP 代理或隧道，适合让指定应用经 WireGuard 出站，无需为宿主机创建 TUN 网络接口。

本目录提供带队列扩容和 Landlock 补丁的社区镜像，跟随上游 `master` 开发分支构建，与上游项目无隶属关系。

[⬅️ 返回镜像目录](../#镜像目录)

## 与官方镜像的区别

上游已提供官方镜像 [`ghcr.io/windtf/wireproxy`](https://github.com/windtf/wireproxy/pkgs/container/wireproxy)，由上游[容器工作流](https://github.com/windtf/wireproxy/blob/master/.github/workflows/container.yml)构建发布。官方镜像的 `latest` 同样跟随 `master` 开发分支。

| 项目 | 官方镜像 | 本镜像 |
| --- | --- | --- |
| 软件内容 | 上游源码及其声明的依赖 | 上游 `master` 加指定队列扩容和 Landlock 补丁，详见下文 |
| 运行镜像 | 上游 Dockerfile 使用 Distroless nonroot | 使用 Alpine，以 `65532:65532` 运行 |
| 镜像分发 | 上游工作流发布到 GHCR | 同时发布到 Docker Hub 和 GHCR |
| 更新方式 | 上游 `master` 推送触发构建发布 | 每天解析最新 `master` 并完整重建，刷新基础镜像和系统包 |

基础镜像和启动方式可对照[上游 Dockerfile](https://github.com/windtf/wireproxy/blob/master/Dockerfile)。非 root 和用户态代理是二者的共同点，纯用户态代理不需要 `/dev/net/tun`、`privileged` 或 `NET_ADMIN`。本镜像发布 `linux/amd64`、`linux/arm64` 两个平台。

需要这里列出的补丁或 Docker Hub 分发时，可选择本镜像；希望使用未经这些补丁修改的上游构建时，可直接使用官方镜像。

扩大队列会增加积压时的内存需求和排队延迟，不保证吞吐提升，也不代表支持同等数量的并发连接。详细差异见下方[补丁范围](#补丁范围)。

## 镜像地址与标签

| 镜像仓库 | 地址 |
| --- | --- |
| [Docker Hub](https://hub.docker.com/r/aethersailor/wireproxy) | `aethersailor/wireproxy:latest` |
| [GHCR](https://github.com/users/Aethersailor/packages/container/package/wireproxy) | `ghcr.io/aethersailor/wireproxy:latest` |

两个仓库发布相同内容。`latest` 跟随上游开发分支并包含本仓库补丁，不代表官方正式 Release。需要固定镜像内容时，使用对应镜像仓库中的 digest。

## 使用

以下 Compose 示例使用 Linux host 网络。开始前需要准备可用的 WireGuard 连接信息；镜像不包含配置、账户或密钥。

### 1. 准备配置

在部署目录创建 `wireproxy.conf`，按[上游配置说明](https://github.com/windtf/wireproxy#sample-config-file)填写 `[Interface]`、`[Peer]` 等部分，再根据需要配置代理。例如，添加以下内容可在本机提供 SOCKS5 代理：

```ini
[Socks5]
BindAddress = 127.0.0.1:25344
```

这个片段需要与自己的 WireGuard 连接配置一起使用。由于示例使用 host 网络，`BindAddress` 直接决定宿主机上的监听地址和端口；启动前确认端口可用。如需向其他设备开放代理，应同时设置认证和访问控制。

配置文件需允许容器的 UID/GID `65532:65532` 读取。可通过文件属主、组或 ACL 授予读取权限，并保护其中的私钥；配置还引用其他文件时，也需挂载这些文件并设置相应权限。

### 2. 创建并启动容器

在同一目录创建 `compose.yaml`：

```yaml
services:
  wireproxy:
    image: aethersailor/wireproxy:latest
    network_mode: host
    restart: unless-stopped
    volumes:
      - ./wireproxy.conf:/etc/wireproxy/config:ro
```

确认配置文件已存在并可读取，再在该目录执行：

```sh
docker compose up -d
docker compose logs --tail=50 wireproxy
```

启动后，将宿主机应用的 SOCKS5 代理设为 `127.0.0.1:25344`。使用 GHCR 时，将 `image` 改为 `ghcr.io/aethersailor/wireproxy:latest`。

镜像默认读取 `/etc/wireproxy/config` 并在前台运行，命令行参数沿用上游。需要健康接口时可通过 `--info` 指定监听地址；自定义 Compose 的 `command` 时，应一并保留 `--config /etc/wireproxy/config`，或明确指定自己的配置路径。镜像以 `SIGINT` 停止进程，不内置自动恢复脚本。

## 更新镜像与查看版本

在 `compose.yaml` 所在目录执行：

```sh
docker compose pull
docker compose up -d
```

每天北京时间 11:43 跟踪上游最新 `master` 提交并完整重建，刷新基础镜像和系统包。定时执行可能延迟，记录见[发布工作流](https://github.com/Aethersailor/container-forge/actions/workflows/wireproxy.yml)。镜像更新后，已运行的容器仍需自行更新。

查看镜像版本和构建来源：

```sh
docker run --rm aethersailor/wireproxy:latest --version
docker run --rm --entrypoint cat aethersailor/wireproxy:latest /usr/share/wireproxy/build-info.json
```

版本格式为 `master-<上游 SHA 前 12 位>-forge1`。`build-info.json` 记录上游和打包提交、Go 与 WireGuard 依赖版本、平台及补丁配置；镜像标签元数据也记录打包提交和上游完整 SHA，便于反馈时定位版本。

## 补丁范围

| 项目 | 补丁修改前的值 | 本镜像采用的值 |
| --- | --- | --- |
| WireGuard 待发送队列 | `IdealBatchSize` | `512 * IdealBatchSize`，当前构建记录为 `65536` |
| WireGuard 出站队列 | `1024` | `65536` |
| WireGuard 入站队列 | `1024` | `65536` |
| WireGuard 握手队列 | `1024` | `65536` |
| 用户态网络栈出口队列 | `1024` | `65536` |

WireGuard 队列值表示槽位数，部分槽位存放批次容器，不代表连接数。握手队列没有统一的最大值，本镜像采用与其他队列一致的 `65536`；Cookie 防护仍在积压达到 `128` 时触发。握手队列用于 WireGuard 握手消息，不对应 SOCKS 或订阅请求并发。

Landlock 补丁仅增加 `/proc/sys/net/core/somaxconn` 的只读权限，供 Go 获取 TCP 监听队列上限。宿主机 sysctl、网卡队列和 systemd 调优不包含在镜像中；不增加 `/capacity`、自定义丢包计数或诊断 API，上游原有的 `--info`、`/readyz` 等接口保留。

补丁文件：[WireGuard 队列](patches/wireguard-capacity.patch)、[Landlock 权限](patches/landlock-somaxconn.patch)。构建按上游声明的版本获取并校验 WireGuard 依赖，再在独立副本中应用补丁，不修改 gVisor 依赖本身。

## 反馈与许可

镜像启动、权限或本仓库补丁问题请在[本仓库 Issues](https://github.com/Aethersailor/container-forge/issues) 反馈，附上版本或构建信息、宿主机架构和错误日志；提交配置前移除私钥等敏感信息。上游功能与配置说明见 [wireproxy 项目](https://github.com/windtf/wireproxy)。

wireproxy 许可证：[ISC](LICENSE)。修改的 WireGuard 依赖遵循上游 MIT 许可证，镜像中保留其许可证文件。

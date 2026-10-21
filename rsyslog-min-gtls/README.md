# rsyslog-min-gtls

用于接收网络日志的精简 [rsyslog](https://github.com/rsyslog/rsyslog) 容器镜像，基于 Debian stable-slim，内置 GnuTLS。适合集中接收 TCP/UDP syslog 日志，或配合自备配置与证书使用 TLS/mTLS。

[返回镜像目录](../#镜像目录)

## 镜像特点

- 从 rsyslog v8 源码编译，运行镜像仅保留 rsyslogd、所需模块及运行库。
- 默认监听 TCP/UDP 1514，将收到的日志输出到 stdout，可通过容器日志查看。
- 内置 GnuTLS 网络流驱动，可配置 TLS 加密和双向证书认证。
- 提供 `linux/amd64` 镜像，同时发布到 Docker Hub 和 GHCR。

本镜像由社区独立维护，与 rsyslog 上游项目无隶属关系。精简镜像不包含 rsyslog 的全部可选模块，使用自定义配置前请核对下方模块清单。

## 镜像地址与标签

| 镜像仓库 | 地址 |
| --- | --- |
| [Docker Hub](https://hub.docker.com/r/aethersailor/rsyslog-min-gtls) | `aethersailor/rsyslog-min-gtls` |
| [GHCR](https://github.com/users/Aethersailor/packages/container/package/rsyslog-min-gtls) | `ghcr.io/aethersailor/rsyslog-min-gtls` |

- `latest`：最新构建的 rsyslog v8。
- `v8.x.y`：指定已发布的版本；将占位版本号替换为镜像仓库中实际存在的标签。

两个镜像仓库发布相同内容。版本标签也会随基础镜像刷新而更新；需要固定镜像内容时，使用对应镜像仓库中的 digest。

## 快速开始

先以默认配置在本机接收日志：

```sh
docker run --rm \
  -p 127.0.0.1:1514:1514/tcp \
  -p 127.0.0.1:1514:1514/udp \
  aethersailor/rsyslog-min-gtls:latest
```

将本机日志发送端的目标设为 `127.0.0.1:1514`，协议可选 TCP 或 UDP；收到的日志会显示在当前终端。按 Ctrl+C 停止并删除示例容器。

使用 GHCR 时，将镜像名改为 `ghcr.io/aethersailor/rsyslog-min-gtls:latest`。示例端口仅向宿主机本机开放；如需接收其他设备的日志，需将映射地址改为宿主机可达的地址，并配置防火墙。

默认配置是明文 syslog，未启用 TLS/mTLS；内置 GnuTLS 不会自动为监听端口启用加密。

## 使用 Docker Compose

创建 `compose.yaml`，使用默认配置在后台运行：

```yaml
services:
  rsyslog:
    image: aethersailor/rsyslog-min-gtls:latest
    restart: unless-stopped
    ports:
      - "127.0.0.1:1514:1514/tcp"
      - "127.0.0.1:1514:1514/udp"
```

在该目录启动并查看日志：

```sh
docker compose up -d
docker compose logs --tail=50 -f rsyslog
```

## 自定义配置与 TLS/mTLS

默认配置来自 [`config/rsyslog.conf`](config/rsyslog.conf)，容器内路径为 `/etc/rsyslog.conf`。挂载自定义配置会替换整个默认配置，监听端口和日志输出位置由自定义文件决定。

在部署目录准备 `rsyslog.conf`，需要 TLS 时同时准备 `certs` 目录及证书。在上方 Compose 服务中加入：

```yaml
    volumes:
      - ./rsyslog.conf:/etc/rsyslog.conf:ro
      - ./certs:/etc/rsyslog/tls:ro
```

配置中的证书路径须使用容器内的 `/etc/rsyslog/tls/…`。镜像也预建了 `/etc/rsyslog/mtls` 目录，可按需挂载。TLS/mTLS 的监听端口、CA、服务端证书、私钥和对端认证规则需在自己的配置中设置，配置方法见 [rsyslog 官方文档](https://www.rsyslog.com/doc/)。

启用 TLS 时需在配置中选择 `gtls` 驱动，并设置相应的加密与认证模式；仅挂载证书不会启用 TLS。若自定义监听端口不是 1514，还需同步调整 Compose 的端口映射。需要持久化日志文件或工作目录时，应按配置挂载对应存储。

镜像内的可加载模块：

```text
imudp, imtcp, lmtcpsrv, lmregexp, lmnet, lmnetstrms, lmnsd_ptcp, lmnsd_gtls
```

其中 `imudp` 和 `imtcp` 用于网络日志输入，`lmnsd_gtls` 提供 GnuTLS 网络流支持。模块路径为 `/usr/lib/rsyslog`。默认配置不会自动加载 `/etc/rsyslog.d/` 下的文件；使用配置片段时，需在自己的主配置中显式包含它们。

## 更新镜像

在 `compose.yaml` 所在目录执行：

```sh
docker compose pull
docker compose up -d
```

每天北京时间 10:23 跟踪上游最新 rsyslog v8 tag 并完整重建，刷新基础镜像和系统包；上游版本号不变时也会重新发布。定时执行可能延迟，记录见[发布工作流](https://github.com/Aethersailor/container-forge/actions/workflows/rsyslog-min-gtls.yml)。镜像更新后，已运行的容器仍需自行更新。

## 反馈与许可

镜像拉取、容器启动或内置模块问题请在[本仓库 Issues](https://github.com/Aethersailor/container-forge/issues) 反馈，并提供镜像标签、启动配置及错误日志；提交前移除私钥等敏感信息。rsyslog 配置和功能说明见[上游项目](https://github.com/rsyslog/rsyslog)及官方文档。

本目录许可证：[GPL-3.0](LICENSE)。

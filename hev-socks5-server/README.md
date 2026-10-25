# 🧦 HEV SOCKS5 Server

轻量 SOCKS5 服务端，支持 IPv4/IPv6、TCP CONNECT、UDP ASSOCIATE，以及用户名密码认证。适合独立部署 SOCKS5 代理服务。

## 与上游容器方案的区别

上游 [heiher/hev-socks5-server](https://github.com/heiher/hev-socks5-server) 提供 [Dockerfile 和自行构建说明](https://github.com/heiher/hev-socks5-server/tree/main/docker)。本次核对的上游构建流程主要发布各平台二进制，未见现成运行镜像的发布入口。

本工程直接打包未修改的[官方正式 Release 二进制](https://github.com/heiher/hev-socks5-server/releases)，核对上游提供的 SHA-256，提供 amd64、arm64 镜像、Docker Hub/GHCR 分发和每日基础镜像刷新。配置文件直接交给上游程序读取，不修改协议、认证或转发逻辑。

运行层采用 Alpine，以 `65532:65532` 运行。镜像保留上游 MIT 许可证及 `/usr/share/hev-socks5-server/upstream.json` 来源记录。

## 镜像地址和标签

| 镜像仓库 | 地址 |
| --- | --- |
| [Docker Hub](https://hub.docker.com/r/aethersailor/hev-socks5-server) | `aethersailor/hev-socks5-server` |
| [GHCR](https://github.com/Aethersailor/container-forge/pkgs/container/hev-socks5-server) | `ghcr.io/aethersailor/hev-socks5-server` |

- `latest`：最新打包的官方正式版。
- 上游版本号：例如 `2.13.1`，与上游标签一致，不额外添加 `v` 前缀。
- 支持 Linux amd64、arm64，由 Docker 自动选择对应架构。

## 使用

先创建 `config.yml`，修改示例中的账号和密码：

```yaml
main:
  workers: 2
  port: 1080
  listen-address: '0.0.0.0'

auth:
  username: proxy-user
  password: REPLACE_WITH_YOUR_PASSWORD

misc:
  log-file: stderr
  log-level: warn
```

然后创建 `compose.yaml`。以下示例面向 Linux Docker Engine，沿用上游推荐的 host 网络方式，便于 TCP 和 UDP 转发：

```yaml
services:
  hev-socks5-server:
    image: aethersailor/hev-socks5-server:latest
    restart: unless-stopped
    network_mode: host
    volumes:
      - ./config.yml:/etc/hev-socks5-server/config.yml:ro
```

```sh
docker compose up -d
docker compose logs -f
```

也可以把镜像地址改为 `ghcr.io/aethersailor/hev-socks5-server`。镜像不内置可直接启用的默认配置，启动前必须挂载自己的配置文件；配置及外部认证文件需允许 UID `65532` 读取。普通 SOCKS5 代理不需要特权模式、TUN 设备或 `NET_ADMIN`。

示例监听 IPv4 的 `1080/tcp`。需要 IPv6 接入时，可按上游文档修改监听地址。用户名密码认证用于限制访问，SOCKS5 协议本身不提供传输加密。

### UDP 与端口映射

上游默认动态分配 UDP 转发端口，host 网络可直接使用宿主机端口，防火墙仍需允许相应流量。需要限制范围时，在 `main` 中设置例如 `udp-port: 20000-20100`，并允许对应 UDP 端口。

如果改用 bridge 网络，TCP 可映射 `1080:1080/tcp`；UDP 还需要映射实际使用的 UDP 端口范围，并按环境配置 `udp-public-address-v4` 或 `udp-public-address-v6`，不能只映射 `1080/tcp` 就期望 UDP 自动可用。完整配置项见[上游说明](https://github.com/heiher/hev-socks5-server#how-to-use)。

### 多用户认证

上游支持 `auth.file` 认证文件，可挂载到容器中后在配置内指定绝对路径。文件格式和热更新方法见[上游认证说明](https://github.com/heiher/hev-socks5-server#authentication-file)。不设置使程序转入后台的 `pid-file`，以便 Docker 管理前台主进程。

## 更新与来源

每天北京时间 10:37 检查官方最新正式 Release，并完整重建；上游版本号不变时也会拉取最新基础镜像并刷新 Alpine 系统包。实际执行时间可能延迟。

```sh
docker compose pull
docker compose up -d
```

已发布的版本标签会保留，不回填全部历史版本。同一版本可能随上游产物重发或基础镜像刷新而改变内容；需要固定内容时使用 digest。

查看镜像打包来源：

```sh
docker run --rm --entrypoint cat aethersailor/hev-socks5-server:latest \
  /usr/share/hev-socks5-server/upstream.json
```

上游 MIT 许可证见 [LICENSE](LICENSE)。本工程由社区独立维护，与上游无隶属关系。

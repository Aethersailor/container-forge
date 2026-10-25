# 🔒 dnscrypt-proxy

加密 DNS 转发代理，支持 DNSCrypt、DoH、Anonymized DNSCrypt 和 ODoH。客户端通过普通 UDP/TCP DNS 接口查询，dnscrypt-proxy 选择配置的加密上游完成解析，并提供本地缓存。

## 与上游分发的区别

上游 [DNSCrypt/dnscrypt-proxy](https://github.com/DNSCrypt/dnscrypt-proxy) 提供源码及多平台正式二进制；本次核对的发布流程主要交付 Release 文件，未见公开运行镜像的发布入口。社区已有其他容器方案，本工程提供由 Container Forge 独立维护的打包。

镜像直接使用未修改的[官方 Linux Release 压缩包](https://github.com/DNSCrypt/dnscrypt-proxy/releases)，核对上游 SHA-256 后提取二进制，发布到 Docker Hub、GHCR。运行层采用 Alpine，配置与缓存路径分开，以 `65532:65532` 运行，并每日刷新基础镜像和系统包。

镜像保留 ISC 许可证、对应版本的完整上游配置示例，以及 `/usr/share/dnscrypt-proxy/upstream.json` 来源记录。不修改解析协议、解析器列表或上游签名校验逻辑。

## 镜像地址和标签

| 镜像仓库 | 地址 |
| --- | --- |
| [Docker Hub](https://hub.docker.com/r/aethersailor/dnscrypt-proxy) | `aethersailor/dnscrypt-proxy` |
| [GHCR](https://github.com/Aethersailor/container-forge/pkgs/container/dnscrypt-proxy) | `ghcr.io/aethersailor/dnscrypt-proxy` |

- `latest`：最新打包的官方正式版。
- 上游版本号：例如 `2.1.20`，与上游标签一致。
- 支持 Linux amd64、arm64，由 Docker 自动选择对应架构。

## 使用

创建 `dnscrypt-proxy.toml`，可以从本目录的 [dnscrypt-proxy.example.toml](dnscrypt-proxy.example.toml) 复制。示例启用 DNSCrypt、DoH 和上游签名解析器列表，监听容器内 `5353/tcp`、`5353/udp`；匿名 DNSCrypt 和 ODoH 需要按上游说明另外配置。

创建 `compose.yaml`：

```yaml
services:
  dnscrypt-proxy:
    image: aethersailor/dnscrypt-proxy:latest
    restart: unless-stopped
    ports:
      - '127.0.0.1:53:5353/tcp'
      - '127.0.0.1:53:5353/udp'
    volumes:
      - ./dnscrypt-proxy.toml:/etc/dnscrypt-proxy/dnscrypt-proxy.toml:ro
      - dnscrypt-data:/var/lib/dnscrypt-proxy

volumes:
  dnscrypt-data:
```

```sh
docker compose up -d
docker compose logs -f
```

也可以使用 `ghcr.io/aethersailor/dnscrypt-proxy`。示例仅向宿主机回环地址提供 DNS；需要供局域网使用时，按实际接口调整映射地址。宿主机 `53` 已被占用时，选择其他端口或地址，不需要修改宿主机现有 DNS 服务。

镜像不自动生成或覆盖用户配置。容器内使用非特权端口 `5353`，不需要特权模式、host 网络或额外 capability。

### 配置与持久化

| 路径 | 用途 |
| --- | --- |
| `/etc/dnscrypt-proxy/dnscrypt-proxy.toml` | 用户只读配置 |
| `/var/lib/dnscrypt-proxy` | 解析器列表及签名缓存，可写数据卷 |
| `/usr/share/dnscrypt-proxy/example-dnscrypt-proxy.toml` | 对应上游版本的完整配置示例 |

使用命名卷时，数据目录沿用镜像内 UID `65532` 的权限。改用宿主机目录时，需要允许该 UID 写入；配置文件及引用的其他文件也需允许该 UID 读取。

上游配置中的相对路径以配置文件所在目录为基准。使用只读配置挂载时，将列表缓存和需要写入的日志路径设到可写数据目录；本工程提供的示例已经使用绝对缓存路径。

首次启动需要下载签名解析器列表，并连通所选加密 DNS 上游。`bootstrap_resolvers` 用于解析列表下载地址及上游域名，不是正常查询的明文回退上游。可以按网络环境调整 bootstrap 地址或明确指定 `server_names`，不要删除解析器列表的 `minisign_key`。

配置项及解析器选择见[上游配置文档](https://github.com/DNSCrypt/dnscrypt-proxy/wiki/Configuration)。容器本身不会修改宿主机的 DNS 设置；需要由使用者决定哪些客户端向它查询。

### 查看版本与解析结果

```sh
docker run --rm aethersailor/dnscrypt-proxy:latest -version

docker compose exec dnscrypt-proxy dnscrypt-proxy \
  -config /etc/dnscrypt-proxy/dnscrypt-proxy.toml \
  -resolve example.com,127.0.0.1:5353
```

## 更新与来源

每天北京时间 10:53 检查官方最新正式 Release，并完整重建；即使软件版本未变，也会拉取最新基础镜像并刷新系统包。实际执行时间可能延迟。

```sh
docker compose pull
docker compose up -d
```

已发布的版本标签会保留，不回填全部历史版本。同一版本可能随上游重发或基础镜像刷新而更新内容，需要固定内容时使用 digest。升级时按上游更新日志核对配置兼容性，用户挂载的配置保持不变。

```sh
docker run --rm --entrypoint cat aethersailor/dnscrypt-proxy:latest \
  /usr/share/dnscrypt-proxy/upstream.json
```

上游 ISC 许可证见 [LICENSE](LICENSE)。本工程由社区独立维护，与上游无隶属关系。

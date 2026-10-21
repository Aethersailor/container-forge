# mihomo

[mihomo](https://github.com/MetaCubeX/mihomo) 是支持多种代理协议和规则路由的代理核心。本目录提供社区维护的容器镜像，适合通过 Docker 部署 mihomo，或需要 amd64 不同指令等级镜像的用户。

[返回镜像目录](../#镜像目录)

## 镜像特点

- 直接打包官方正式版和 Alpha 的未修改二进制，不修改或重新编译核心。
- 提供 amd64 v1/v2/v3，以及 386、arm64、arm/v7 的 Linux 镜像。
- 配置目录和启动参数沿用官方镜像，已有容器部署可替换镜像地址。
- Docker Hub 和 GHCR 发布相同内容，可任选其一。

本镜像由社区独立维护，与 MetaCubeX 无隶属关系。

## 镜像地址

| 镜像仓库 | 地址 |
| --- | --- |
| [Docker Hub](https://hub.docker.com/r/aethersailor/mihomo) | `aethersailor/mihomo` |
| [GHCR](https://github.com/users/Aethersailor/packages/container/package/mihomo) | `ghcr.io/aethersailor/mihomo` |

## 选择标签

| 标签 | 用途 |
| --- | --- |
| `latest` | 最新正式版，常规部署使用此标签 |
| `v1.x.x` | 指定已同步的正式版；将占位版本号替换为镜像仓库中实际存在的标签 |
| `Alpha` | 最新 Alpha 开发版本，注意大写 `A` |

支持自动匹配指令等级的 Docker 会选择 CPU 能运行的最高 amd64 等级。旧版 Docker 或需要固定等级时，可使用 `latest-amd64-v1`、`latest-amd64-v2`、`latest-amd64-v3`；`Alpha` 和版本标签也提供对应后缀，例如 `Alpha-amd64-v2`。所选等级须由 CPU 支持。

版本标签也可能随基础镜像刷新而更新；需要固定镜像内容时，使用对应镜像仓库中的 digest。

## 使用

以下示例需要 Docker Compose，向宿主机本机开放代理端口。

### 1. 准备配置

在部署目录中准备自己的 `config.yaml`，配置代理节点和规则。该文件需要包含以下设置，以接受容器端口转发的流量：

```yaml
mixed-port: 7890
allow-lan: true
```

配置格式、节点和规则说明见 [mihomo 文档](https://wiki.metacubex.one/)。上述两项设置不包含代理节点，不能替代完整的业务配置。

### 2. 创建并启动容器

在同一目录创建 `compose.yaml`：

```yaml
services:
  mihomo:
    image: aethersailor/mihomo:latest
    restart: unless-stopped
    ports:
      - "127.0.0.1:7890:7890"
    volumes:
      - ./config.yaml:/root/.config/mihomo/config.yaml:ro
```

确认 `config.yaml` 已存在，再在该目录执行：

```sh
docker compose up -d
docker compose logs --tail=50 mihomo
```

启动后，将宿主机应用的 HTTP 或 SOCKS5 代理设为 `127.0.0.1:7890`。示例仅允许宿主机本机访问；如需供局域网设备使用，需自行调整端口映射并配置访问控制。

使用 GHCR 时，将 `image` 改为 `ghcr.io/aethersailor/mihomo:latest`；使用 Alpha 时，将标签改为 `Alpha`。

TUN、透明代理及其他权限和网络配置请按 [mihomo 文档](https://wiki.metacubex.one/) 设置，以上示例仅用于普通代理端口。

## 更新镜像

在 `compose.yaml` 所在目录执行：

```sh
docker compose pull
docker compose up -d
```

每 30 分钟检查官方正式版和 Alpha；每天北京时间 11:23 额外完整重建两个通道，刷新基础镜像和系统包，即使核心版本未变也会重建。定时执行可能延迟，记录见 [发布工作流](https://github.com/Aethersailor/container-forge/actions/workflows/mihomo.yml)。更新已发布的镜像不会自动替换正在运行的容器。

官方撤回版本后，会移除对应标签，并让 `latest` 回退至官方当前正式版；已拉取到本地的镜像不受影响。首次同步从当前版本开始，不回填全部历史版本，使用指定版本前请确认标签存在。

## 反馈与许可

镜像拉取、架构或打包问题请在[本仓库 Issues](https://github.com/Aethersailor/container-forge/issues) 反馈，并提供镜像标签、宿主机架构、启动配置和错误日志；提交前移除凭据等敏感信息。核心功能和配置说明见 [mihomo 上游项目](https://github.com/MetaCubeX/mihomo)。

许可证：[GPL-3.0](LICENSE)。

# FRP · 内网穿透镜像

[FRP](https://github.com/fatedier/frp) 用于通过具有公网地址的服务端访问内网服务。本目录为官方 frpc、frps 容器镜像提供社区分发地址和 `latest` 标签，适合使用 Docker 部署客户端、服务端或更新已有部署。

[返回镜像目录](../#镜像目录)

## 镜像特点

- 从官方 GHCR 原样同步镜像，不重新构建或修改内容。
- 保留官方完整的多架构清单，具体平台以所选标签为准。
- 为 frpc 和 frps 提供跟随官方正式版的 `latest` 标签。
- 同时分发到 Docker Hub 和 GHCR，镜像内容与对应官方版本一致。

本镜像由社区独立维护，`latest` 标签由本仓库提供，与 FRP 上游项目无隶属关系。

## 镜像地址与标签

| 组件 | 用途 | Docker Hub | GHCR |
| --- | --- | --- | --- |
| frpc | 部署在可访问内网服务的设备上，连接 frps | [`aethersailor/frpc`](https://hub.docker.com/r/aethersailor/frpc) | [`ghcr.io/aethersailor/frpc`](https://github.com/users/Aethersailor/packages/container/package/frpc) |
| frps | 部署在具有公网地址的服务器上，接收 frpc 连接 | [`aethersailor/frps`](https://hub.docker.com/r/aethersailor/frps) | [`ghcr.io/aethersailor/frps`](https://github.com/users/Aethersailor/packages/container/package/frps) |

- `latest`：跟随当前可用的官方最新正式版。
- `vX.Y.Z`：指定已同步的版本；将占位版本号替换为镜像仓库中实际存在的标签。

镜像公开，无需登录即可拉取。版本标签会跟随官方同版本重发而更新；需要固定镜像内容时，使用对应镜像仓库中的 digest。客户端和服务端可选择相同的已发布版本，以减少版本差异。

## 使用

以下示例通过 Docker Compose，将内网 HTTP 服务 `192.168.1.10:8080` 映射到公网服务器的 TCP 6000 端口。请替换服务器地址、内网地址和认证 Token；frpc 容器必须能访问所填的内网地址。

### 1. 在公网服务器部署 frps

创建 `frps.toml`：

```toml
bindPort = 7000
auth.method = "token"
auth.token = "replace-with-a-long-random-token"
```

在同一目录创建 `compose.yaml`：

```yaml
services:
  frps:
    image: aethersailor/frps:latest
    restart: unless-stopped
    command: ["-c", "/etc/frp/frps.toml"]
    ports:
      - "7000:7000"
      - "6000:6000"
    volumes:
      - ./frps.toml:/etc/frp/frps.toml:ro
```

替换 Token 后启动：

```sh
docker compose up -d
docker compose logs --tail=50 frps
```

服务器防火墙和安全组需允许客户端连接 TCP 7000，并按实际访问需求放行 TCP 6000。示例会将内网 HTTP 服务发布到公网，服务自身仍需设置必要的认证与访问控制。

### 2. 在内网设备部署 frpc

创建 `frpc.toml`，将 `frp.example.com` 改为公网服务器地址，Token 与 frps 保持一致：

```toml
serverAddr = "frp.example.com"
serverPort = 7000
auth.method = "token"
auth.token = "replace-with-a-long-random-token"

[[proxies]]
name = "web"
type = "tcp"
localIP = "192.168.1.10"
localPort = 8080
remotePort = 6000
```

在该设备的同一目录创建 `compose.yaml`：

```yaml
services:
  frpc:
    image: aethersailor/frpc:latest
    restart: unless-stopped
    command: ["-c", "/etc/frp/frpc.toml"]
    volumes:
      - ./frpc.toml:/etc/frp/frpc.toml:ro
```

确认地址和 Token 已替换，再启动：

```sh
docker compose up -d
docker compose logs --tail=50 frpc
```

连接成功后，可通过 `http://frp.example.com:6000` 访问示例中的内网 HTTP 服务。容器内的 `127.0.0.1` 指向容器自身；访问宿主机或其他内网设备时，应填写 frpc 容器实际可达的地址。

使用 GHCR 时，将镜像名分别替换为 `ghcr.io/aethersailor/frpc:latest`、`ghcr.io/aethersailor/frps:latest`。已有 FRP 容器部署可保留原有配置和参数，仅替换对应镜像地址。

其他协议、鉴权和代理类型见 [FRP 官方文档](https://gofrp.org/zh-cn/docs/)。新增映射时，还需按所用协议调整 frps 的容器端口映射及服务器防火墙。

## 更新镜像

在客户端和服务端各自的 `compose.yaml` 所在目录执行：

```sh
docker compose pull
docker compose up -d
```

每 6 小时检查官方 Release 和镜像 digest，已同步的历史版本也会检查同版本更新。官方重新发布镜像时，跟随新的 digest 原样同步；官方撤回 Release 或移除版本镜像时，对应版本也会撤下，`latest` 回退至仍可用的官方正式版。已拉取到本地的镜像不受影响。

定时执行可能延迟，记录见[同步工作流](https://github.com/Aethersailor/container-forge/actions/workflows/frp.yml)。镜像更新后，已运行的容器仍需自行更新，也可按需使用 Watchtower 等工具。

## 问题反馈

镜像拉取、缺失标签或同步问题请在[本仓库 Issues](https://github.com/Aethersailor/container-forge/issues) 反馈，并提供镜像地址与标签、宿主机架构及错误日志；提交配置前移除 Token 等敏感信息。FRP 功能与配置问题可先查阅[上游项目](https://github.com/fatedier/frp)及官方文档。

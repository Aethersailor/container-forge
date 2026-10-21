# FRP Image Sync

为 [FRP](https://github.com/fatedier/frp) 官方的 `frpc`、`frps` Docker 镜像提供 `latest` 标签，方便使用 Watchtower 等工具自动更新。

镜像从官方 GHCR 原样同步至 Docker Hub 和 GHCR，保留完整多架构支持，不重新构建或修改内容。

## 镜像地址

| 镜像 | Docker Hub | GHCR |
| --- | --- | --- |
| 客户端 frpc | `aethersailor/frpc` | `ghcr.io/aethersailor/frpc` |
| 服务端 frps | `aethersailor/frps` | `ghcr.io/aethersailor/frps` |

支持以下标签：

- `latest`：跟随官方最新正式版，每 6 小时检查更新。
- `vX.Y.Z`：使用指定版本，例如 `v0.71.1`。保留本仓库已同步的版本。

官方重新发布同一版本时，镜像标签跟随更新。官方撤回 Release 或移除版本镜像时，已同步的对应版本也会撤下，`latest` 回退至仍可用的官方正式版。

## 使用

```sh
docker pull aethersailor/frpc:latest
docker pull aethersailor/frps:latest
```

也可使用上表中的 GHCR 地址。镜像公开，无需登录即可拉取。需要指定版本时，将 `latest` 替换为具体版本标签；如需锁定重新发布前的确切内容，请使用 digest。

本项目由社区维护，`latest` 标签由本仓库提供。FRP 的配置和使用方法请参考[官方文档](https://gofrp.org/zh-cn/docs/)。

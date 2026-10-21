# Container Forge · 容器镜像工坊

为上游项目补齐容器镜像的打包与分发能力。每个软件拥有独立的工程目录、发布工作流和镜像地址。

Independent container image packaging and distribution for upstream projects.

## 镜像目录

| 工程 | 用途 | Docker Hub | GHCR | 自动更新 |
| --- | --- | --- | --- | --- |
| [mihomo](mihomo/) | 打包官方正式版和 Alpha 二进制，补齐 amd64 v1/v2/v3 | [`aethersailor/mihomo`](https://hub.docker.com/r/aethersailor/mihomo) | [`ghcr.io/aethersailor/mihomo`](https://github.com/users/Aethersailor/packages/container/package/mihomo) | 每 30 分钟检查 |
| [FRP](frp/) | 原样同步官方 frpc、frps 镜像，维护 `latest` 标签 | [`aethersailor/frpc`](https://hub.docker.com/r/aethersailor/frpc)、[`aethersailor/frps`](https://hub.docker.com/r/aethersailor/frps) | [`ghcr.io/aethersailor/frpc`](https://github.com/users/Aethersailor/packages/container/package/frpc)、[`ghcr.io/aethersailor/frps`](https://github.com/users/Aethersailor/packages/container/package/frps) | 每 6 小时检查 |

具体标签、支持架构和使用方法见各工程的 README。定时任务的实际执行时间可能延迟。

## 工程组织

```text
.github/
  dependabot.yml
  workflows/
    mihomo.yml
    frp.yml
    dependabot-auto-merge.yml
mihomo/
  README.md
  Dockerfile
  LICENSE
  scripts/
frp/
  README.md
  scripts/
```

每个工程自行维护所需的 Dockerfile、脚本、配置和文档。FRP 使用镜像原样复制，不需要 Dockerfile。各工程不共用构建脚本、发布模板或版本号。

GitHub Actions 要求工作流入口放在 `.github/workflows/`。`mihomo.yml` 和 `frp.yml` 各自定义定时任务、目录触发条件、工作目录和并发组，可以单独手动执行；修改一个工程不会触发另一个工程的推送发布。mihomo 的重建判断只依据自身打包文件和上游版本。

首页、Dependabot 配置、Dependabot 自动合并和文本换行规则由仓库统一维护。Dependabot 自动合并不增加测试、审批或状态检查门槛。

## 添加工程

1. 在仓库根目录创建软件目录，放入独立的打包或同步文件及 README。
2. 在 `.github/workflows/` 添加对应工作流，只监听自身工程目录和该工作流文件。
3. 明确配置镜像地址、凭据名称及更新周期，为并发组、缓存和工作流产物使用工程前缀。
4. 按需在 `.github/dependabot.yml` 增加该工程的依赖更新配置，并更新首页镜像目录。

发布地址不从本仓库名称推导。迁入本仓库不改变现有镜像地址和标签。

## 维护配置

| 工程 | Actions Secrets |
| --- | --- |
| mihomo | `MIHOMO_DOCKERHUB_USERNAME`、`MIHOMO_DOCKERHUB_TOKEN` |
| FRP | `FRP_DOCKERHUB_TOKEN`；可选 `FRP_DOCKERHUB_USERNAME`，默认 `aethersailor` |
| Dependabot 自动合并 | `DEPENDABOT_MERGE_TOKEN`，同时配置到 Actions 和 Dependabot Secrets |

GHCR 发布使用 `GITHUB_TOKEN`，现有镜像包需要允许本仓库的 Actions 写入。FRP 的 Docker Hub 命名空间固定为 `aethersailor`；mihomo 的两个镜像地址在自身工作流中明确指定。

各工程保留各自的许可证及上游声明；`mihomo/LICENSE` 适用于 mihomo 工程。迁移来源为 [m-core-docker](https://github.com/Aethersailor/m-core-docker) 和 [frp-image-sync](https://github.com/Aethersailor/frp-image-sync)。

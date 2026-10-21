# Container Forge · 容器镜像工坊

为上游项目补齐容器镜像的打包与分发能力。每个软件拥有独立的工程目录、发布工作流和镜像地址。

Independent container image packaging and distribution for upstream projects.

维护和新增工程的约定见 [AGENTS.md](AGENTS.md)。

## 镜像目录

| 工程 | 用途 | Docker Hub | GHCR | 自动更新 |
| --- | --- | --- | --- | --- |
| [mihomo](mihomo/) | 打包官方正式版和 Alpha 二进制，补齐 amd64 v1/v2/v3 | [`aethersailor/mihomo`](https://hub.docker.com/r/aethersailor/mihomo) | [`ghcr.io/aethersailor/mihomo`](https://github.com/users/Aethersailor/packages/container/package/mihomo) | 每 30 分钟检查 |
| [FRP](frp/) | 原样同步官方 frpc、frps 镜像，维护 `latest` 标签 | [`aethersailor/frpc`](https://hub.docker.com/r/aethersailor/frpc)、[`aethersailor/frps`](https://hub.docker.com/r/aethersailor/frps) | [`ghcr.io/aethersailor/frpc`](https://github.com/users/Aethersailor/packages/container/package/frpc)、[`ghcr.io/aethersailor/frps`](https://github.com/users/Aethersailor/packages/container/package/frps) | 每 6 小时检查 |
| [rsyslog-min-gtls](rsyslog-min-gtls/) | 编译精简 rsyslog，保留 GnuTLS 和 TLS/mTLS 支持 | [`aethersailor/rsyslog-min-gtls`](https://hub.docker.com/r/aethersailor/rsyslog-min-gtls) | [`ghcr.io/aethersailor/rsyslog-min-gtls`](https://github.com/users/Aethersailor/packages/container/package/rsyslog-min-gtls) | 每天检查 |

具体标签、支持架构和使用方法见各工程的 README。定时任务的实际执行时间可能延迟。

## 工程组织

```text
.github/
  dependabot.yml
  workflows/
    mihomo.yml
    frp.yml
    rsyslog-min-gtls.yml
    dependabot-auto-merge.yml
mihomo/
  README.md
  Dockerfile
  LICENSE
  scripts/
frp/
  README.md
  scripts/
rsyslog-min-gtls/
  README.md
  Dockerfile
  LICENSE
  UPSTREAM_VERSION
  config/
  scripts/
```

每个工程自行维护所需的 Dockerfile、脚本、配置和文档。FRP 使用镜像原样复制，不需要 Dockerfile。各工程不共用构建脚本、发布模板或版本号。

GitHub Actions 要求工作流入口放在 `.github/workflows/`。各工程的工作流各自定义定时任务、目录触发条件、工作目录和并发组，可以单独手动执行；修改一个工程不会触发另一个工程的推送发布。mihomo 的重建判断只依据自身打包文件和上游版本。

首页、Dependabot 配置、Dependabot 自动合并和文本换行规则由仓库统一维护。Dependabot 自动合并不增加测试、审批或状态检查门槛。

## 添加工程

1. 在仓库根目录创建软件目录，放入独立的打包或同步文件及 README。
2. 在 `.github/workflows/` 添加对应工作流，只监听自身工程目录和该工作流文件。
3. 明确配置镜像地址及更新周期，为并发组、缓存和工作流产物使用工程前缀；发布凭据使用仓库统一配置。
4. 按需在 `.github/dependabot.yml` 增加该工程的依赖更新配置，并更新首页镜像目录。

发布地址不从本仓库名称推导。迁入本仓库不改变现有镜像地址和标签。

## 维护配置

| 用途 | Actions Secrets |
| --- | --- |
| 所有工程的 Docker Hub 发布 | `DOCKERHUB_USERNAME`、`DOCKERHUB_TOKEN` |
| Dependabot 自动合并 | `DEPENDABOT_MERGE_TOKEN`，同时配置到 Actions 和 Dependabot Secrets |

Docker Hub 使用账号级个人访问令牌，授予 Read、Write、Delete 权限，覆盖该账号可访问的镜像仓库。所有工程共用这一份凭据，新增工程无需单独创建 Token。

GHCR 发布使用 GitHub 自动生成的 `GITHUB_TOKEN` 和 `packages: write` 权限。新镜像包由对应工作流创建；接管已有镜像包时，为本仓库授予包管理权限，以支持发布及撤回版本。Dependabot 自动合并 Token 覆盖本仓库内所有工程。

各工程自行指定镜像地址。FRP 的 Docker Hub 命名空间固定为 `aethersailor`；mihomo 的两个镜像地址在自身工作流中明确指定。

各工程保留各自的许可证及上游声明；`mihomo/LICENSE` 和 `rsyslog-min-gtls/LICENSE` 分别适用于对应工程。迁移来源为 [m-core-docker](https://github.com/Aethersailor/m-core-docker)、[frp-image-sync](https://github.com/Aethersailor/frp-image-sync) 和 [rsyslog-min-gtls](https://github.com/Aethersailor/rsyslog-min-gtls)。

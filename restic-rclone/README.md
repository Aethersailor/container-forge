# 🗄️ restic-rclone

将 restic 和 rclone 的官方正式版二进制放入同一镜像，供 restic 原生 `rclone:` 后端调用。restic 负责加密、去重、快照和恢复，rclone 负责访问配置的远程存储；使用方式见 [restic 上游文档](https://restic.readthedocs.io/en/stable/030_preparing_a_new_repo.html#other-services-via-rclone)。

## 与官方镜像的区别

restic 已有 [`restic/restic`](https://hub.docker.com/r/restic/restic) 和 [`ghcr.io/restic/restic`](https://github.com/restic/restic/pkgs/container/restic) 官方镜像，但当前[官方 Dockerfile](https://github.com/restic/restic/blob/master/docker/Dockerfile) 未包含 rclone。rclone 也有[独立官方镜像](https://rclone.org/install/#docker-installation)。

本工程补充同一容器中的组合，直接使用未修改的官方 Release 二进制，核对上游 SHA-256 后打包。不修改备份格式和传输协议，不预设远程凭据。restic 自行启动、停止 rclone，无需单独运行 `rclone serve restic` 服务或映射端口。

运行层采用 Alpine，包含 CA 证书、OpenSSH 客户端和时区数据。入口直接执行 restic，不提供官方镜像的 `NICE`、`IONICE_CLASS` 等包装脚本变量，也不预装定时备份脚本、保留策略或 FUSE 挂载配置。

## 镜像地址、标签与架构

| 镜像仓库 | 地址 |
| --- | --- |
| [Docker Hub](https://hub.docker.com/r/aethersailor/restic-rclone) | `aethersailor/restic-rclone` |
| [GHCR](https://github.com/Aethersailor/container-forge/pkgs/container/restic-rclone) | `ghcr.io/aethersailor/restic-rclone` |

- `latest`：最新打包的两者正式版组合。
- 组合版本标签：例如 `restic-0.19.1-rclone-1.75.2`，同时标明两者版本。
- 支持 Linux amd64、arm64，由 Docker 自动选择对应架构。

两者独立跟踪各自最新正式 Release，任一软件更新都会产生新的组合标签。旧组合标签保留，不回填全部历史组合。同一组合也会因每日基础镜像刷新而更新内容，需要固定内容时使用 digest。

## 使用

这是按命令运行的工具镜像，默认显示 restic 帮助。通过宿主机 cron、systemd timer 或现有调度工具安排备份；镜像不会自动初始化仓库或执行删除、保留策略。

### 准备配置

保存本目录的 [compose.yaml](compose.yaml)，创建 `data/`、`rclone/` 目录和 `restic-password` 文件。密码文件仅保存自己的仓库密码，限制其宿主机访问权限，并妥善保管；丢失密码将无法恢复备份。

```sh
mkdir -p data rclone
```

`data/` 是要备份的目录，示例只读挂载到 `/data`；也可把挂载源改成实际业务目录。备份运行中的数据库时，先按应用要求生成一致的导出文件或快照，再交给 restic。

配置名为 `backup` 的 rclone remote：

```sh
docker compose run --rm --entrypoint rclone restic config
docker compose run --rm --entrypoint rclone restic lsd backup:
```

配置保存到 `./rclone/rclone.conf`。已有配置也可复制到该目录，并按实际 remote 名称和目标路径修改 `RESTIC_REPOSITORY`；示例 `rclone:backup:restic` 表示 remote `backup` 中的 `restic` 路径。

rclone 配置目录需要可写，以支持 OAuth Token 刷新及配置文件替换；仅只读挂载单个配置文件可能导致这类更新失败。也可按 [rclone 文档](https://rclone.org/docs/#environment-variables) 通过 `RCLONE_CONFIG_*` 环境变量配置 remote。

### 初始化、备份与查看快照

确认目标是新仓库后，手动初始化一次；已有仓库直接使用：

```sh
docker compose run --rm restic init
docker compose run --rm restic backup /data
docker compose run --rm restic snapshots
```

示例使用固定 hostname `restic-backup`，避免每次创建临时容器时产生不同的快照主机名。多台机器共用仓库时，为每台设置自己的固定 hostname。

### 恢复

将快照恢复到独立的可写目录，不覆盖只读备份源：

```sh
mkdir -p restore
docker compose run --rm -v "$PWD/restore:/restore" restic restore latest --target /restore
```

快照中的 `/data` 恢复到 `restore/data/`。恢复其他快照时，将 `latest` 换成对应 ID；多台主机共用仓库时，按需求增加 `--host` 等筛选条件。

### 路径与权限

| 容器路径 | 用途 |
| --- | --- |
| `/data` | 要备份的只读源目录 |
| `/config/rclone/rclone.conf` | rclone remote 配置，由 `RCLONE_CONFIG` 指定 |
| `/cache/restic` | restic 缓存，由 `RESTIC_CACHE_DIR` 指定 |
| `/cache/rclone` | rclone 缓存，由 `RCLONE_CACHE_DIR` 指定 |
| `/run/secrets/restic_password` | 示例中只读挂载的仓库密码 |
| `/usr/share/restic-rclone/upstream.json` | 两者版本、源码提交及二进制摘要 |

镜像默认以 root 运行，以支持读取挂载源文件及恢复文件属主。可在 Compose 中添加 `user: "UID:GID"`，但需要该用户能读取备份源和密码、写入配置及缓存；恢复文件属主的能力也取决于实际权限。rclone 后端不需要特权模式、host 网络或 `/dev/fuse`。

## 更新与来源

每天北京时间 12:07 检查 restic、rclone 最新正式 Release 并完整重建。即使两者版本都未变，也会拉取最新基础镜像并刷新系统包；实际执行时间可能延迟。

```sh
docker compose pull
docker run --rm aethersailor/restic-rclone:latest version
docker run --rm --entrypoint rclone aethersailor/restic-rclone:latest version
docker run --rm --entrypoint cat aethersailor/restic-rclone:latest /usr/share/restic-rclone/upstream.json
```

也可改用 GHCR 地址。通过更新镜像升级程序，不在临时容器内执行自更新命令。升级前按两者上游更新日志核对仓库格式、后端和配置兼容性。

restic 遵循 [BSD 2-Clause](LICENSE.restic)，rclone 遵循 [MIT](LICENSE.rclone)。镜像内保留与所选版本对应的许可证；本工程由社区独立维护，与两个上游均无隶属关系。

# rsyslog-min-gtls

最小化 rsyslog 镜像（基于 Debian stable-slim），内置 GnuTLS，用于 TLS/mTLS 场景。
Minimal rsyslog image (based on Debian stable-slim) with GnuTLS for TLS/mTLS.

## 中文

### 概览
- 上游：rsyslog 官方仓库
- 运行时仅复制 rsyslogd 与所需模块，尽量缩小镜像体积
- 默认配置：监听 TCP/UDP 1514，输出到 stdout

### 内置模块
imudp, imtcp, lmtcpsrv, lmregexp, lmnet, lmnetstrms, lmnsd_ptcp, lmnsd_gtls

### 快速开始
从 GHCR 拉取并运行：
```bash
docker pull ghcr.io/aethersailor/rsyslog-min-gtls:latest
docker run --rm -p 1514:1514/tcp -p 1514:1514/udp ghcr.io/aethersailor/rsyslog-min-gtls:latest
```

也可以从 Docker Hub 拉取同一镜像：
```bash
docker pull aethersailor/rsyslog-min-gtls:latest
docker run --rm -p 1514:1514/tcp -p 1514:1514/udp aethersailor/rsyslog-min-gtls:latest
```

本地构建（可选指定上游 tag）：
```bash
docker build --build-arg RSYSLOG_REF=v8.2512.0 -t rsyslog-min-gtls .
```

### 配置
- 默认配置来自 `config/rsyslog.conf`，在镜像内路径为 `/etc/rsyslog.conf`。
- 要启用 TLS/mTLS，请挂载你自己的配置与证书（镜像内预建了 `/etc/rsyslog/tls` 与 `/etc/rsyslog/mtls` 目录）。
- 示例挂载：
```bash
docker run --rm \
  -p 1514:1514/tcp -p 1514:1514/udp \
  -v /path/to/rsyslog.conf:/etc/rsyslog.conf:ro \
  -v /path/to/certs:/etc/rsyslog/tls:ro \
  ghcr.io/aethersailor/rsyslog-min-gtls:latest
```

### 上游跟踪与 CI
- 工作流始终解析 rsyslog 最新 v8 tag。
- 定时任务每天检测一次：如无更新则跳过编译；如有更新则编译并推送 GHCR 和 Docker Hub。
- 两个镜像仓库都保留 `v8.x.y` 版本标签；`latest` 始终指向最高版本号。发布流程不会生成 SHA、分支名或无标签的附加镜像。
- Dependabot 由仓库统一配置，自动合并依赖更新，不增加测试、扫描或人工审批。
- 成功发布新上游版本后，工作流只写回本工程的 `UPSTREAM_VERSION`。
- 发布工作流：[rsyslog-min-gtls.yml](../.github/workflows/rsyslog-min-gtls.yml)。镜像路径保持不变，发布凭据使用仓库统一配置。

### 目录速览
- `Dockerfile`: 多阶段构建，运行时只复制必要产物
- `scripts/build-rsyslog.sh`: 编译配置与裁剪选项
- `config/rsyslog.conf`: 默认最小配置
- `UPSTREAM_VERSION`: 记录最新上游 tag

## English

### Overview
- Upstream: official rsyslog repository
- Runtime stage copies only rsyslogd and required modules for a smaller image
- Default config: listens on TCP/UDP 1514 and logs to stdout

### Included modules
imudp, imtcp, lmtcpsrv, lmregexp, lmnet, lmnetstrms, lmnsd_ptcp, lmnsd_gtls

### Quick start
Pull and run from GHCR:
```bash
docker pull ghcr.io/aethersailor/rsyslog-min-gtls:latest
docker run --rm -p 1514:1514/tcp -p 1514:1514/udp ghcr.io/aethersailor/rsyslog-min-gtls:latest
```

The same image is also available from Docker Hub:
```bash
docker pull aethersailor/rsyslog-min-gtls:latest
docker run --rm -p 1514:1514/tcp -p 1514:1514/udp aethersailor/rsyslog-min-gtls:latest
```

Build locally (optional upstream tag):
```bash
docker build --build-arg RSYSLOG_REF=v8.2512.0 -t rsyslog-min-gtls .
```

### Configuration
- Default config is `config/rsyslog.conf`, copied to `/etc/rsyslog.conf` in the image.
- To enable TLS/mTLS, mount your own config and certificates (the image has `/etc/rsyslog/tls` and `/etc/rsyslog/mtls`).
- Example mount:
```bash
docker run --rm \
  -p 1514:1514/tcp -p 1514:1514/udp \
  -v /path/to/rsyslog.conf:/etc/rsyslog.conf:ro \
  -v /path/to/certs:/etc/rsyslog/tls:ro \
  ghcr.io/aethersailor/rsyslog-min-gtls:latest
```

### Upstream tracking & CI
- Workflow always resolves the latest rsyslog v8 tag.
- Scheduled runs check daily: skip if unchanged; build and push to GHCR and Docker Hub if updated.
- Both registries retain `v8.x.y` version tags, while `latest` always points to the highest version. The publication workflow does not create SHA, branch, or untagged auxiliary images.
- Dependabot is configured at repository level and merges dependency updates automatically, without tests, scans, or manual approval.
- After a new upstream version is published successfully, the workflow updates this project's `UPSTREAM_VERSION`.
- Publication workflow: [rsyslog-min-gtls.yml](../.github/workflows/rsyslog-min-gtls.yml). Image paths stay unchanged and publication uses repository-level credentials.

### Layout
- `Dockerfile`: multi-stage build; runtime copies only required artifacts
- `scripts/build-rsyslog.sh`: configure/build with trimmed options
- `config/rsyslog.conf`: default minimal config
- `UPSTREAM_VERSION`: records the latest upstream tag

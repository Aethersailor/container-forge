# wireproxy

本工程独立打包 [windtf/wireproxy](https://github.com/windtf/wireproxy) 最新 `master`，保留指定容量和 Landlock 补丁，与上游项目无隶属关系。

## 镜像

```text
aethersailor/wireproxy:latest
ghcr.io/aethersailor/wireproxy:latest
```

两个仓库发布相同的多架构镜像，支持 `linux/amd64`、`linux/arm64`。`latest` 跟随上游开发分支，不代表官方正式 Release。

每天北京时间 11:43 解析最新 `master` 提交并完整重建，推送相关工程文件和手动执行也会触发。每次构建都固定本次解析到的上游 SHA，拉取最新基础镜像并禁用构建缓存，以获取基础镜像和系统包更新。定时执行可能延迟。

## 补丁范围

| 项目 | 上游当前值 | 本工程值 |
| --- | --- | --- |
| WireGuard 待发送队列 | `128` | `65536`（`512 * IdealBatchSize`） |
| WireGuard 出站队列 | `1024` | `65536` |
| WireGuard 入站队列 | `1024` | `65536` |
| WireGuard 握手队列 | `1024` | `65536` |
| 用户态网络栈出口队列 | `1024` | `65536` |

WireGuard 队列值表示槽位数，部分槽位存放批次容器，不代表连接数。握手队列没有统一的最大值，本工程采用与其他队列一致的 `65536`；Cookie 防护仍在积压达到上游原有的 `128` 时触发，避免随队列扩容一起放宽。

Landlock 仅增加 `/proc/sys/net/core/somaxconn` 的只读权限，供 Go 获取 TCP 监听队列上限；其他沙箱规则沿用上游。不增加 `/capacity`、自定义丢包计数或诊断 API；上游原有的 `--info`、`/readyz` 等接口保留。

扩大队列会增加积压时的内存需求和排队延迟，不保证吞吐提升。握手队列用于 WireGuard 握手消息，不对应 SOCKS 或订阅请求并发。宿主机 sysctl、网卡队列和 systemd 调优不包含在镜像中。

补丁分别保存在 `patches/landlock-somaxconn.patch` 和 `patches/wireguard-capacity.patch`。构建时依据上游 `go.mod` 获取并校验 WireGuard 依赖，再复制到临时构建目录应用补丁；不修改 gVisor 依赖本身。

## 使用

沿用上游命令行参数和默认容器配置路径 `/etc/wireproxy/config`。先准备自己的 WireGuard/wireproxy 配置，再挂载到镜像中。配置和密钥不包含在镜像内。

```yaml
services:
  wireproxy:
    image: aethersailor/wireproxy:latest
    network_mode: host
    restart: unless-stopped
    volumes:
      - ./wireproxy.conf:/etc/wireproxy/config:ro
```

镜像以 `65532:65532` 运行，挂载的配置需要允许该用户或组读取。纯用户态代理不需要 `/dev/net/tun`、`privileged` 或 `NET_ADMIN`。示例使用 Linux host 网络，实际监听地址由配置中的 `BindAddress` 决定；启动前确认该地址和端口可用。

默认进程前台运行。镜像以 `SIGINT` 停止进程，匹配上游处理的退出信号。需要健康接口时自行追加 `--info`，镜像不内置自动恢复脚本。

查看版本和构建来源：

```sh
docker run --rm aethersailor/wireproxy:latest --version
docker run --rm --entrypoint cat aethersailor/wireproxy:latest /usr/share/wireproxy/build-info.json
```

版本格式为 `master-<上游 SHA 前 12 位>-forge1`。镜像标签记录打包提交和上游完整 SHA，`build-info.json` 额外记录 Go、WireGuard 依赖版本、平台和补丁配置。

wireproxy 许可证：[ISC](LICENSE)。修改的 WireGuard 依赖遵循上游 MIT 许可证，镜像中保留其许可证文件。

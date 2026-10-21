# ===== Builder =====
FROM debian:stable-slim AS builder

ARG RSYSLOG_REF=v8.2510.0

RUN apt-get update && apt-get install -y --no-install-recommends \
  ca-certificates git build-essential autoconf autoconf-archive automake libtool pkg-config \
  flex bison \
  libgnutls28-dev libgcrypt20-dev zlib1g-dev \
  libestr-dev libfastjson-dev \
  libcurl4-openssl-dev \
  uuid-dev \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /src
RUN git clone --depth 1 --branch "${RSYSLOG_REF}" https://github.com/rsyslog/rsyslog.git .

COPY scripts/build-rsyslog.sh /build-rsyslog.sh
RUN chmod +x /build-rsyslog.sh && /build-rsyslog.sh

# ===== Runtime =====
FROM debian:stable-slim AS runtime

# 安装运行时必需的包：
# - rsyslog 运行时依赖库（通过 apt 确保版本一致）
RUN apt-get update && apt-get install -y --no-install-recommends \
  ca-certificates \
  libfastjson4 \
  libestr0 \
  libgnutls30 \
  libuuid1 \
  zlib1g \
  && rm -rf /var/lib/apt/lists/*

# 运行时目录
RUN mkdir -p /var/log /var/lib/rsyslog /etc/rsyslog.d /etc/rsyslog/tls /etc/rsyslog/mtls /usr/lib/rsyslog

# 只从 builder 复制 rsyslogd 和模块（不复制依赖库）
COPY --from=builder /usr/local/sbin/rsyslogd /usr/sbin/rsyslogd
COPY --from=builder /usr/local/lib/rsyslog/imudp.so /usr/lib/rsyslog/
COPY --from=builder /usr/local/lib/rsyslog/imtcp.so /usr/lib/rsyslog/
COPY --from=builder /usr/local/lib/rsyslog/lmtcpsrv.so /usr/lib/rsyslog/
COPY --from=builder /usr/local/lib/rsyslog/lmregexp.so /usr/lib/rsyslog/
COPY --from=builder /usr/local/lib/rsyslog/lmnet.so /usr/lib/rsyslog/
COPY --from=builder /usr/local/lib/rsyslog/lmnetstrms.so /usr/lib/rsyslog/
COPY --from=builder /usr/local/lib/rsyslog/lmnsd_ptcp.so /usr/lib/rsyslog/
COPY --from=builder /usr/local/lib/rsyslog/lmnsd_gtls.so /usr/lib/rsyslog/

# 默认配置，避免无 action 退出
COPY config/rsyslog.conf /etc/rsyslog.conf

# rsyslog 默认模块路径
ENV RSYSLOG_MODDIR=/usr/lib/rsyslog

# 前台运行
CMD ["/usr/sbin/rsyslogd","-n","-iNONE","-M/usr/lib/rsyslog"]

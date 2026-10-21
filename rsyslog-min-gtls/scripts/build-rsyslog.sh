#!/usr/bin/env bash
set -euo pipefail

# 生成 configure
autoreconf -fvi

# 尽量裁剪：只留网络输入 + TLS
# 注意：rsyslog 的可选项很多，不同版本参数名可能略有差异；
# 我们先用“保守但能工作”的子集，后续再继续裁剪到更极限。
./configure \
  --prefix=/usr/local \
  --disable-Werror \
  --enable-imudp \
  --enable-imtcp \
  --enable-gnutls \
  --disable-generate-man-pages \
  --disable-ommail \
  --disable-ommongodb \
  --disable-ompgsql \
  --disable-ommysql \
  --disable-omrabbitmq \
  --disable-omhttp \
  --disable-omkafka \
  --disable-imkafka \
  --disable-imjournal \
  --disable-imfile \
  --disable-imzmq \
  --disable-libdbi \
  --disable-libyaml \
  --disable-impstats-push \
  --disable-clickhouse \
  --disable-elasticsearch \
  --disable-gssapi \
  --disable-relp \
  --disable-snmp

make -j"$(nproc)"
make install

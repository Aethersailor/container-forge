#!/bin/sh
set -eu

patch -p1 --fuzz=0 < /patches/landlock-somaxconn.patch
go mod download golang.zx2c4.com/wireguard
module_dir="$(go list -m -f '{{.Dir}}' golang.zx2c4.com/wireguard)"
mkdir -p localdeps
cp -a "$module_dir" localdeps/wireguard
chmod -R u+w localdeps/wireguard
patch -d localdeps/wireguard -p1 --fuzz=0 < /patches/wireguard-capacity.patch
go mod edit -replace=golang.zx2c4.com/wireguard=./localdeps/wireguard

version="master-$(printf '%s' "$UPSTREAM_REVISION" | cut -c1-12)-forge1"
mkdir -p /out
CGO_ENABLED=0 GOOS="$TARGETOS" GOARCH="$TARGETARCH" \
    go build -buildvcs=false -trimpath -ldflags "-s -w -X main.version=$version" \
    -o /out/wireproxy ./cmd/wireproxy

cat > /out/build-info.json <<EOF
{
  "upstream_repository": "https://github.com/windtf/wireproxy",
  "upstream_revision": "$UPSTREAM_REVISION",
  "packaging_revision": "$PACKAGING_REVISION",
  "wireguard_version": "$(go list -m -f '{{.Version}}' golang.zx2c4.com/wireguard)",
  "go_version": "$(go env GOVERSION)",
  "platform": "$TARGETOS/$TARGETARCH",
  "version": "$version",
  "patches": ["landlock-somaxconn", "wireguard-capacity"],
  "queue_staged": 65536,
  "queue_outbound": 65536,
  "queue_inbound": 65536,
  "queue_handshake": 65536,
  "queue_netstack": 65536,
  "handshake_cookie_threshold": 128
}
EOF

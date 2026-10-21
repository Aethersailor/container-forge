# syntax=docker/dockerfile:1
FROM alpine:3.24

RUN apk add --no-cache ca-certificates tzdata iptables

ARG TARGETARCH
ARG TARGETVARIANT
COPY --chmod=755 dist/${TARGETARCH}${TARGETVARIANT}/mihomo /mihomo
COPY dist/config/ /root/.config/mihomo/
COPY dist/upstream.json /usr/share/mihomo/upstream.json
COPY LICENSE /usr/share/licenses/mihomo/LICENSE

VOLUME ["/root/.config/mihomo/"]
ENTRYPOINT ["/mihomo"]

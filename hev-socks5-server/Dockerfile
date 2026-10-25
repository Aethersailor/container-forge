FROM alpine:3.24

RUN apk upgrade --no-cache

ARG TARGETARCH
COPY --chmod=755 dist/${TARGETARCH}/hev-socks5-server /usr/local/bin/hev-socks5-server
COPY dist/LICENSE /usr/share/licenses/hev-socks5-server/LICENSE
COPY dist/upstream.json /usr/share/hev-socks5-server/upstream.json

WORKDIR /etc/hev-socks5-server
USER 65532:65532

ENTRYPOINT ["/usr/local/bin/hev-socks5-server"]
CMD ["/etc/hev-socks5-server/config.yml"]

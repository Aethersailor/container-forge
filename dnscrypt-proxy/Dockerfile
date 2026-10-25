FROM alpine:3.24

RUN apk upgrade --no-cache \
    && apk add --no-cache ca-certificates \
    && mkdir -p /etc/dnscrypt-proxy /var/lib/dnscrypt-proxy \
    && chown 65532:65532 /var/lib/dnscrypt-proxy

ARG TARGETARCH
COPY --chmod=755 dist/${TARGETARCH}/dnscrypt-proxy /usr/local/bin/dnscrypt-proxy
COPY dist/${TARGETARCH}/example-dnscrypt-proxy.toml /usr/share/dnscrypt-proxy/example-dnscrypt-proxy.toml
COPY dist/LICENSE /usr/share/licenses/dnscrypt-proxy/LICENSE
COPY dist/upstream.json /usr/share/dnscrypt-proxy/upstream.json

WORKDIR /etc/dnscrypt-proxy
USER 65532:65532
EXPOSE 5353/tcp 5353/udp

ENTRYPOINT ["/usr/local/bin/dnscrypt-proxy"]
CMD ["-config", "/etc/dnscrypt-proxy/dnscrypt-proxy.toml"]

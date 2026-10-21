# syntax=docker/dockerfile:1
FROM --platform=$BUILDPLATFORM golang:1.26-alpine AS build

RUN apk add --no-cache ca-certificates curl git patch

ARG UPSTREAM_REVISION
ARG PACKAGING_REVISION
ARG TARGETOS
ARG TARGETARCH
WORKDIR /src
RUN test "${#UPSTREAM_REVISION}" -eq 40 \
    && curl --fail --show-error --location --retry 3 \
       "https://codeload.github.com/windtf/wireproxy/tar.gz/${UPSTREAM_REVISION}" \
       | tar -xz --strip-components=1

COPY patches/ /patches/
COPY scripts/build-wireproxy.sh /build-wireproxy.sh
RUN sh /build-wireproxy.sh

FROM alpine:3.24
RUN apk add --no-cache ca-certificates tzdata \
    && mkdir -p /etc/wireproxy /usr/share/wireproxy /usr/share/licenses/wireproxy /usr/share/licenses/wireguard-go
COPY --from=build /out/wireproxy /usr/bin/wireproxy
COPY --from=build /out/build-info.json /usr/share/wireproxy/build-info.json
COPY LICENSE /usr/share/licenses/wireproxy/LICENSE
COPY --from=build /src/localdeps/wireguard/LICENSE /usr/share/licenses/wireguard-go/LICENSE

USER 65532:65532
STOPSIGNAL SIGINT
ENTRYPOINT ["/usr/bin/wireproxy"]
CMD ["--config", "/etc/wireproxy/config"]

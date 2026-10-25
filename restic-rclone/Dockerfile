FROM alpine:3.24

RUN apk upgrade --no-cache \
    && apk add --no-cache ca-certificates openssh-client tzdata \
    && mkdir -p /config/rclone /cache/restic /cache/rclone

ARG TARGETARCH
COPY --chmod=755 dist/${TARGETARCH}/restic /usr/local/bin/restic
COPY --chmod=755 dist/${TARGETARCH}/rclone /usr/local/bin/rclone
COPY dist/licenses/ /usr/share/licenses/restic-rclone/
COPY dist/upstream.json /usr/share/restic-rclone/upstream.json

ENV RESTIC_CACHE_DIR=/cache/restic \
    RCLONE_CONFIG=/config/rclone/rclone.conf \
    RCLONE_CACHE_DIR=/cache/rclone

WORKDIR /data
ENTRYPOINT ["/usr/local/bin/restic"]
CMD ["--help"]

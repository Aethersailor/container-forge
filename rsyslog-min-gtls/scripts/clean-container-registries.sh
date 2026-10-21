#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "Usage: $0 <ghcr-image> <dockerhub-username> <package-name>" >&2
  exit 2
fi

: "${GH_TOKEN:?GH_TOKEN is required}"
: "${DOCKERHUB_TOKEN:?DOCKERHUB_TOKEN is required}"

ghcr_image="${1%/}"
dockerhub_username="$2"
package_name="$3"
dockerhub_image="${dockerhub_username}/${package_name}"
ghcr_versions_endpoint="/users/${GITHUB_REPOSITORY_OWNER}/packages/container/${package_name}/versions"

is_release_tag() {
  [[ "$1" == "latest" || "$1" =~ ^v8\.[0-9]+\.[0-9]+$ ]]
}

inspect_digest() {
  docker buildx imagetools inspect "$1" \
    | awk '$1 == "Digest:" { print $2; exit }'
}

normalize_direct_manifests() {
  local image="$1"
  shift
  local tag raw media_type child_count child_digest normalized_type

  for tag in "$@"; do
    raw="$(docker buildx imagetools inspect --raw "${image}:${tag}")"
    media_type="$(jq -r '.mediaType // empty' <<<"$raw")"

    case "$media_type" in
      application/vnd.oci.image.manifest.v1+json|application/vnd.docker.distribution.manifest.v2+json)
        continue
        ;;
      application/vnd.oci.image.index.v1+json|application/vnd.docker.distribution.manifest.list.v2+json)
        child_count="$(jq '[
          .manifests[]
          | select(
              .platform.os == "linux"
              and .platform.architecture == "amd64"
              and (.annotations["vnd.docker.reference.type"] // "") != "attestation-manifest"
            )
        ] | length' <<<"$raw")"
        if [[ "$child_count" != "1" ]]; then
          echo "Expected exactly one linux/amd64 image in ${image}:${tag}; found ${child_count}." >&2
          exit 1
        fi
        child_digest="$(jq -r '[
          .manifests[]
          | select(
              .platform.os == "linux"
              and .platform.architecture == "amd64"
              and (.annotations["vnd.docker.reference.type"] // "") != "attestation-manifest"
            )
        ][0].digest' <<<"$raw")"
        docker buildx imagetools create \
          --prefer-index=false \
          --tag "${image}:${tag}" \
          "${image}@${child_digest}"
        normalized_type="$(
          docker buildx imagetools inspect --raw "${image}:${tag}" \
            | jq -r '.mediaType // empty'
        )"
        if [[ "$normalized_type" != "application/vnd.oci.image.manifest.v1+json" \
          && "$normalized_type" != "application/vnd.docker.distribution.manifest.v2+json" ]]; then
          echo "${image}:${tag} is still an image index after normalization." >&2
          exit 1
        fi
        ;;
      *)
        echo "Unsupported manifest type for ${image}:${tag}: ${media_type:-missing}" >&2
        exit 1
        ;;
    esac
  done
}

verify_latest_tag() {
  local image="$1"
  shift
  local -a version_tags=()
  local tag newest_version latest_digest version_digest

  for tag in "$@"; do
    if [[ "$tag" =~ ^v8\.[0-9]+\.[0-9]+$ ]]; then
      version_tags+=("$tag")
    fi
  done
  if [[ ${#version_tags[@]} -eq 0 ]]; then
    echo "No version tags found for ${image}." >&2
    exit 1
  fi

  newest_version="$(printf '%s\n' "${version_tags[@]}" | sort -V | tail -n 1)"
  latest_digest="$(inspect_digest "${image}:latest")"
  version_digest="$(inspect_digest "${image}:${newest_version}")"
  if [[ -z "$latest_digest" || "$latest_digest" != "$version_digest" ]]; then
    echo "${image}:latest does not match ${image}:${newest_version}." >&2
    exit 1
  fi
  echo "Verified ${image}:latest -> ${newest_version} (${latest_digest})."
}

ghcr_versions_json="$(gh api --paginate --slurp "${ghcr_versions_endpoint}?per_page=100" | jq '[.[][]]')"
mapfile -t ghcr_tags < <(
  jq -r '.[].metadata.container.tags[]?' <<<"$ghcr_versions_json" | sort -u
)
if [[ ${#ghcr_tags[@]} -eq 0 ]]; then
  echo "No GHCR tags found for ${ghcr_image}." >&2
  exit 1
fi
for tag in "${ghcr_tags[@]}"; do
  if ! is_release_tag "$tag"; then
    echo "Unexpected GHCR tag: ${tag}" >&2
    exit 1
  fi
done

normalize_direct_manifests "$ghcr_image" "${ghcr_tags[@]}"
verify_latest_tag "$ghcr_image" "${ghcr_tags[@]}"

declare -A ghcr_tag_digests=()
for tag in "${ghcr_tags[@]}"; do
  ghcr_tag_digests["$tag"]="$(inspect_digest "${ghcr_image}:${tag}")"
done

package_state_ready=false
for _ in {1..12}; do
  ghcr_versions_json="$(gh api --paginate --slurp "${ghcr_versions_endpoint}?per_page=100" | jq '[.[][]]')"
  package_state_ready=true
  for tag in "${ghcr_tags[@]}"; do
    if ! jq -e \
      --arg digest "${ghcr_tag_digests[$tag]}" \
      --arg tag "$tag" \
      'any(.[];
        .name == $digest
        and any(.metadata.container.tags[]?; . == $tag)
      )' <<<"$ghcr_versions_json" >/dev/null; then
      package_state_ready=false
      break
    fi
  done
  if [[ "$package_state_ready" == "true" ]]; then
    break
  fi
  sleep 5
done
if [[ "$package_state_ready" != "true" ]]; then
  echo "GHCR package metadata did not converge to the normalized manifests." >&2
  exit 1
fi

mapfile -t untagged_version_ids < <(
  jq -r '.[] | select((.metadata.container.tags | length) == 0) | .id' \
    <<<"$ghcr_versions_json"
)
for version_id in "${untagged_version_ids[@]}"; do
  gh api --method DELETE "${ghcr_versions_endpoint}/${version_id}"
done

ghcr_versions_json="$(gh api --paginate --slurp "${ghcr_versions_endpoint}?per_page=100" | jq '[.[][]]')"
if jq -e 'any(.[]; (.metadata.container.tags | length) == 0)' \
  <<<"$ghcr_versions_json" >/dev/null; then
  echo "GHCR still contains untagged package versions after cleanup." >&2
  exit 1
fi
echo "Removed ${#untagged_version_ids[@]} untagged GHCR package version(s)."

dockerhub_login_payload="$(
  jq -nc \
    --arg username "$dockerhub_username" \
    --arg password "$DOCKERHUB_TOKEN" \
    '{username: $username, password: $password}'
)"
dockerhub_jwt="$(
  curl --fail --silent --show-error \
    --request POST \
    --header 'Content-Type: application/json' \
    --data "$dockerhub_login_payload" \
    'https://hub.docker.com/v2/users/login' \
    | jq -er '.token'
)"
dockerhub_tags_url="https://hub.docker.com/v2/repositories/${dockerhub_username}/${package_name}/tags?page_size=100"

fetch_dockerhub_tags() {
  local url="$dockerhub_tags_url"
  local page
  while [[ -n "$url" ]]; do
    page="$(
      curl --fail --silent --show-error \
        --header "Authorization: JWT ${dockerhub_jwt}" \
        "$url"
    )"
    jq -r '.results[].name' <<<"$page"
    url="$(jq -r '.next // empty' <<<"$page")"
  done
}

mapfile -t dockerhub_tags < <(fetch_dockerhub_tags | sort -u)
for tag in "${dockerhub_tags[@]}"; do
  if ! is_release_tag "$tag"; then
    curl --fail --silent --show-error \
      --output /dev/null \
      --request DELETE \
      --header "Authorization: JWT ${dockerhub_jwt}" \
      "https://hub.docker.com/v2/repositories/${dockerhub_username}/${package_name}/tags/${tag}"
    echo "Removed unexpected Docker Hub tag: ${tag}"
  fi
done

mapfile -t dockerhub_tags < <(fetch_dockerhub_tags | sort -u)
if [[ ${#dockerhub_tags[@]} -eq 0 ]]; then
  echo "No Docker Hub tags found for ${dockerhub_image}." >&2
  exit 1
fi
for tag in "${dockerhub_tags[@]}"; do
  if ! is_release_tag "$tag"; then
    echo "Unexpected Docker Hub tag remains after cleanup: ${tag}" >&2
    exit 1
  fi
done

normalize_direct_manifests "$dockerhub_image" "${dockerhub_tags[@]}"
verify_latest_tag "$dockerhub_image" "${dockerhub_tags[@]}"

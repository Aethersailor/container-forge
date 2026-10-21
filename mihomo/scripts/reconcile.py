#!/usr/bin/env python3
"""Remove withdrawn upstream releases, after successful latest-tag reconciliation."""

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

import sync

VERSION = re.compile(r"(v\d+\.\d+\.\d+)(?:-amd64-v[123])?$")


def request(url, *, method="GET", token=None, data=None):
    if urllib.parse.urlsplit(url).netloc not in ("api.github.com", "hub.docker.com"):
        raise ValueError("Unexpected API host")
    headers = {"User-Agent": "mihomo-docker", "Accept": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    if data is not None:
        data = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, method=method, headers=headers, data=data)
    # Do not blindly retry mutations after ambiguous failures.
    with urllib.request.urlopen(req, timeout=60) as response:
        payload = response.read()
    return json.loads(payload) if payload else None


def gh_versions(owner, package):
    versions = []
    for page in range(1, 1001):
        result = sync.api(f"users/{owner}/packages/container/{package}/versions?per_page=100&page={page}")
        versions.extend(result)
        if len(result) < 100:
            return versions
    raise ValueError("GHCR pagination exceeded safety limit")


def hub_tags(repository):
    url = f"https://hub.docker.com/v2/repositories/{repository}/tags/?page_size=100"
    tags = set()
    for _ in range(1000):
        page = request(url)
        tags.update(item["name"] for item in page["results"])
        url = page.get("next")
        if not url:
            return tags
    raise ValueError("Docker Hub pagination exceeded safety limit")


def upstream_release(tag):
    try:
        release = sync.api(f"repos/{sync.UPSTREAM}/releases/tags/{tag}")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    # A stable release moved back to draft/prerelease is also withdrawn from stable.
    if release["draft"] or (tag != "Prerelease-Alpha" and release["prerelease"]):
        return None
    return release


def current_stable():
    try:
        release = sync.api(f"repos/{sync.UPSTREAM}/releases/latest")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    tag = release["tag_name"]
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag) or release["draft"] or release["prerelease"]:
        raise ValueError("Invalid upstream latest release")
    return tag


def deletion_tags(published, channel, stable):
    remove = set()
    if channel == "alpha":
        if upstream_release("Prerelease-Alpha") is None:
            remove.update(t for t in published if t == "Alpha" or re.fullmatch(r"Alpha-amd64-v[123]", t))
        return remove
    versions = {VERSION.fullmatch(t)[1] for t in published if VERSION.fullmatch(t)}
    for version in sorted(versions):
        if version != stable and upstream_release(version) is None:
            remove.update(t for t in published if (m := VERSION.fullmatch(t)) and m[1] == version)
    if stable is None:
        remove.update(t for t in published if t == "latest" or re.fullmatch(r"latest-amd64-v[123]", t))
    return remove


def safe_ghcr_deletions(versions, remove):
    result = []
    for version in versions:
        tags = set(version["metadata"]["container"]["tags"])
        if tags & remove:
            if not tags <= remove:
                raise ValueError(f"Refusing to delete a GHCR digest shared with surviving tags: {sorted(tags - remove)}")
            result.append(version["id"])
    return result


def assert_latest(images, stable):
    if stable is None:
        return
    for image in images:
        index = sync.inspect(f"{image}:latest")
        if index.get("annotations", {}).get("org.opencontainers.image.version") != stable:
            raise ValueError("Latest must be rolled back successfully in both registries before deleting withdrawn versions")
        sync.manifests(index)


def hub_login():
    return request("https://hub.docker.com/v2/auth/token", method="POST", data={
        "identifier": os.environ["DOCKERHUB_USERNAME"], "secret": os.environ["DOCKERHUB_TOKEN"]})["access_token"]


def delete_tags(owner, package, repository, versions, published_hub, remove):
    ids = safe_ghcr_deletions(versions, remove)
    token = hub_login()
    for tag in sorted(remove & published_hub):
        print(f"Removing Docker Hub tag: {repository}:{tag}", flush=True)
        try:
            request(f"https://hub.docker.com/v2/repositories/{repository}/tags/{tag}/", method="DELETE", token=token)
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
    for version_id in ids:
        print(f"Removing GHCR package version: {version_id}", flush=True)
        try:
            request(f"https://api.github.com/users/{owner}/packages/container/{package}/versions/{version_id}",
                    method="DELETE", token=os.environ["GH_TOKEN"])
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
    # Read both services again; a partial failure is retried by the next scheduled run.
    remaining = hub_tags(repository) | {t for v in gh_versions(owner, package) for t in v["metadata"]["container"]["tags"]}
    if remaining & remove:
        raise ValueError(f"Withdrawal cleanup incomplete: {sorted(remaining & remove)}")


def reconcile(channel):
    owner, package = "aethersailor", "mihomo"
    repository = os.environ["DOCKERHUB_IMAGE"].removeprefix("docker.io/")
    images = [os.environ["GHCR_IMAGE"], os.environ["DOCKERHUB_IMAGE"]]
    if images != [f"ghcr.io/{owner}/{package}", f"docker.io/{owner}/{package}"]:
        raise ValueError("Cleanup must stay within the aethersailor/mihomo image packages")
    upstream = sync.api(f"repos/{sync.UPSTREAM}")
    if upstream["private"]:
        raise ValueError("Cannot verify public upstream availability")
    stable = current_stable() if channel == "release" else None
    versions = gh_versions(owner, package)
    published_hub = hub_tags(repository)
    published = published_hub | {t for v in versions for t in v["metadata"]["container"]["tags"]}
    remove = deletion_tags(published, channel, stable)
    if not remove:
        print("No withdrawn upstream tags found.")
        return
    print(f"Possible withdrawal: {sorted(remove)}; rechecking upstream in 30 seconds.", flush=True)
    time.sleep(30)
    if sync.api(f"repos/{sync.UPSTREAM}")["id"] != upstream["id"]:
        raise ValueError("Upstream repository identity changed")
    if channel == "release" and current_stable() != stable:
        raise ValueError("Upstream latest changed during withdrawal checks; retry next run")
    if deletion_tags(published, channel, stable) != remove:
        raise ValueError("Upstream release returned during withdrawal checks; keep existing tags")
    assert_latest(images, stable)
    # Refresh tags before mutation to protect newly shared digests.
    versions = gh_versions(owner, package)
    published_hub = hub_tags(repository)
    delete_tags(owner, package, repository, versions, published_hub, remove)
    message = "Removed withdrawn upstream tags: " + ", ".join(sorted(remove))
    print(message)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as file:
            file.write("\n" + message + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", choices=("release", "alpha"), required=True)
    reconcile(parser.parse_args().channel)

#!/usr/bin/env python3
"""Mirror official images and reconcile republished or withdrawn releases."""

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen


COMPONENTS = ("frpc", "frps")
VERSION = re.compile(r"v[0-9]+\.[0-9]+\.[0-9]+\Z")
DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
ACCEPT = ", ".join(("application/vnd.oci.image.index.v1+json",
                    "application/vnd.docker.distribution.manifest.list.v2+json",
                    "application/vnd.oci.image.manifest.v1+json",
                    "application/vnd.docker.distribution.manifest.v2+json"))


def http(method, url, token=None, payload=None, missing=False, accept="application/json"):
    headers = {"Accept": accept, "User-Agent": "frp-image-sync"}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode()
    for attempt in range(3):
        try:
            with urlopen(Request(url, data=data, headers=headers, method=method), timeout=60) as response:
                raw = response.read()
                return (json.loads(raw) if raw else None), response.headers
        except HTTPError as error:
            if missing and error.code == 404:
                return None, {}
            if method in ("GET", "HEAD") and error.code in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(attempt + 1)
                continue
            # Do not print authentication response bodies or request payloads.
            raise RuntimeError(f"{method} {url}: HTTP {error.code}") from None
        except (URLError, TimeoutError):
            if method in ("GET", "HEAD") and attempt < 2:
                time.sleep(attempt + 1)
                continue
            raise RuntimeError(f"{method} {url}: network request failed") from None


def github_pages(url, token, missing=False):
    result = []
    while url:
        if urlsplit(url).netloc != "api.github.com":
            raise RuntimeError("Unexpected GitHub pagination host")
        data, headers = http("GET", url, token, missing=missing)
        if data is None:
            return result
        result.extend(data)
        match = re.search(r'<([^>]+)>; rel="next"', headers.get("Link", ""))
        url = match[1] if match else None
    return result


def official_releases(token):
    releases = github_pages("https://api.github.com/repos/fatedier/frp/releases?per_page=100", token)
    stable = {r["tag_name"]: r["id"] for r in releases
              if not r["draft"] and not r["prerelease"] and VERSION.fullmatch(r["tag_name"])}
    latest, _ = http("GET", "https://api.github.com/repos/fatedier/frp/releases/latest", token, missing=True)
    if latest is None:
        if stable:
            raise RuntimeError("Release list and latest endpoint disagree; no changes made")
        return stable, None
    tag = latest["tag_name"]
    if stable.get(tag) != latest["id"]:
        raise RuntimeError("Official release changed during discovery; retry next run")
    return stable, tag


def source_pair(version, tokens):
    pair = {}
    for component in COMPONENTS:
        _, headers = http("HEAD", f"https://ghcr.io/v2/fatedier/{component}/manifests/{version}",
                          tokens[component], missing=True, accept=ACCEPT)
        digest = headers.get("Docker-Content-Digest")
        if digest is None:
            if not headers:  # Only a confirmed HTTP 404 is treated as absence.
                return None
            raise RuntimeError(f"Official {component}:{version} did not return a digest")
        if not DIGEST.fullmatch(digest):
            raise RuntimeError(f"Invalid official digest for {component}:{version}")
        pair[component] = digest
    return pair


def ghcr_versions(owner, component, token):
    return github_pages(f"https://api.github.com/users/{owner}/packages/container/{component}/versions?per_page=100",
                        token, missing=True)


def hub_tags(namespace, component, token):
    url = f"https://hub.docker.com/v2/repositories/{namespace}/{component}/tags/?page_size=100"
    tags = {}
    while url:
        if urlsplit(url).netloc != "hub.docker.com":
            raise RuntimeError("Unexpected Docker Hub pagination host")
        data, _ = http("GET", url, token, missing=True)
        if data is None:
            return tags
        tags.update({tag["name"]: tag.get("digest") for tag in data["results"]})
        url = data.get("next")
    return tags


def regctl(*args):
    return subprocess.check_output(["regctl", *args], text=True).strip()


def copy_image(source, target, digest, existing=None):
    if existing != digest:
        subprocess.run(["regctl", "image", "copy", "--force-recursive", source, target], check=True)
    actual = regctl("image", "digest", target)
    if actual != digest:
        raise RuntimeError(f"Copy digest mismatch: {target}: {actual} != {digest}")
    print(f"MATCH {target} = {digest}", flush=True)


def withdraw(owner, namespace, tags, gh_token, hub_token):
    if not tags:
        return
    for component in COMPONENTS:
        # GHCR deletes by package version (digest), not by tag. Never delete a
        # digest that still has a tag outside the withdrawal set.
        for version in ghcr_versions(owner, component, gh_token):
            attached = set(version["metadata"]["container"]["tags"])
            if not attached.intersection(tags):
                continue
            if attached - tags:
                raise RuntimeError(f"Cannot withdraw shared GHCR digest {version['name']}; retained tags: {sorted(attached - tags)}")
            http("DELETE", f"https://api.github.com/users/{owner}/packages/container/{component}/versions/{version['id']}", gh_token)
            print(f"WITHDRAW ghcr.io/{owner}/{component}: {sorted(attached)}", flush=True)
        present = hub_tags(namespace, component, hub_token)
        for tag in sorted(tags.intersection(present)):
            http("DELETE", f"https://hub.docker.com/v2/repositories/{namespace}/{component}/tags/{tag}/", hub_token)
            print(f"WITHDRAW docker.io/{namespace}/{component}:{tag}", flush=True)
        for attempt in range(3):
            remaining = {tag for version in ghcr_versions(owner, component, gh_token)
                         for tag in version["metadata"]["container"]["tags"]}
            remaining.update(hub_tags(namespace, component, hub_token))
            if not remaining.intersection(tags):
                break
            if attempt == 2:
                raise RuntimeError(f"Withdrawal not confirmed for {component}: {sorted(remaining.intersection(tags))}")
            time.sleep(2)


def main():
    owner = os.environ["GHCR_NAMESPACE"].lower()
    namespace = os.environ["DOCKERHUB_NAMESPACE"].lower()
    gh_token = os.environ["GH_TOKEN"]
    evidence = Path(os.environ["EVIDENCE_DIR"])
    evidence.mkdir(parents=True, exist_ok=True)
    hub_auth, _ = http("POST", "https://hub.docker.com/v2/auth/token", payload={
        "identifier": os.environ["DOCKERHUB_USERNAME"].lower(), "secret": os.environ["DOCKERHUB_TOKEN"]})
    hub_token = hub_auth["access_token"]
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print("::add-mask::" + hub_token, flush=True)

    releases, official_latest = official_releases(gh_token)
    source_tokens = {}
    for component in COMPONENTS:
        auth, _ = http("GET", "https://ghcr.io/token?" + urlencode({"scope": f"repository:fatedier/{component}:pull"}))
        source_tokens[component] = auth["token"]

    existing = {}
    for component in COMPONENTS:
        existing[f"ghcr.io/{owner}/{component}"] = {
            tag: version["name"] for version in ghcr_versions(owner, component, gh_token)
            for tag in version["metadata"]["container"]["tags"]}
        existing[f"docker.io/{namespace}/{component}"] = hub_tags(namespace, component, hub_token)
    tracked = {tag for tags in existing.values() for tag in tags if VERSION.fullmatch(tag)}
    resolved = {}

    def discover_pair(tag):
        if tag not in resolved:
            resolved[tag] = source_pair(tag, source_tokens)
        return resolved[tag]

    pairs = {}
    withdrawn = tracked - releases.keys()
    for tag in sorted(tracked.intersection(releases)):
        pair = discover_pair(tag)
        if pair is None:
            withdrawn.add(tag)
        else:
            pairs[tag] = pair

    # Follow GitHub's designated latest, including deliberate downgrades. If its
    # images are not available, use the newest older official release with both
    # images. Do not resurrect a higher version after an upstream downgrade.
    latest = None
    if official_latest:
        key = lambda tag: tuple(map(int, tag[1:].split(".")))
        candidates = [official_latest] + sorted((tag for tag in releases if key(tag) < key(official_latest)), key=key, reverse=True)
        for tag in candidates:
            pair = discover_pair(tag)
            if pair is not None:
                pairs[tag] = pair
                latest = tag
                break

    plan = {"status": "planned", "official_latest": official_latest, "latest": latest,
            "withdrawn_versions": sorted(withdrawn), "versions": pairs}
    (evidence / "sync.json").write_text(json.dumps(plan, indent=2) + "\n")
    print(json.dumps(plan, indent=2), flush=True)

    # Copy all tracked releases so republishing an older version also propagates.
    # Every target version must match before any latest alias is changed.
    for tag, pair in sorted(pairs.items()):
        for component, digest in pair.items():
            source = f"ghcr.io/fatedier/{component}@{digest}"
            for target in (f"ghcr.io/{owner}/{component}", f"docker.io/{namespace}/{component}"):
                copy_image(source, f"{target}:{tag}", digest, existing[target].get(tag))

    if official_releases(gh_token) != (releases, official_latest):
        raise RuntimeError("Official release state changed during copying; latest was not updated")
    for tag, pair in resolved.items():
        if source_pair(tag, source_tokens) != pair:
            raise RuntimeError(f"Official {tag} changed during copying; latest was not updated")

    if latest:
        for component, digest in pairs[latest].items():
            for target in (f"ghcr.io/{owner}/{component}", f"docker.io/{namespace}/{component}"):
                copy_image(f"{target}@{digest}", f"{target}:latest", digest, existing[target].get("latest"))
    else:
        # If no complete official release remains, do not keep a withdrawn latest.
        withdrawn.add("latest")
    withdraw(owner, namespace, withdrawn, gh_token, hub_token)
    plan["status"] = "published"
    (evidence / "sync.json").write_text(json.dumps(plan, indent=2) + "\n")

    with open(os.environ.get("GITHUB_STEP_SUMMARY", os.devnull), "a") as summary:
        summary.write(f"## FRP mirrors: {latest or 'no available official release'}\n\n")
        summary.write("| Version | Image | Official / GHCR / Docker Hub digest |\n| --- | --- | --- |\n")
        for tag, pair in sorted(pairs.items()):
            for component, digest in pair.items():
                summary.write(f"| {tag} | {component} | {digest} |\n")
        summary.write(f"\nWithdrawn tags: {', '.join(sorted(withdrawn)) or 'none'}\n")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, KeyError, ValueError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)

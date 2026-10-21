#!/usr/bin/env python3
"""Repack official mihomo release assets; publish aliases only after verification."""

import argparse
import concurrent.futures
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.request

UPSTREAM = "MetaCubeX/mihomo"
FINGERPRINT = "io.github.mihomo-docker.fingerprint"
PLATFORMS = {
    "linux/amd64": ("amd64-v1", "amd64"),
    "linux/amd64/v2": ("amd64-v2", "amd64v2"),
    "linux/amd64/v3": ("amd64-v3", "amd64v3"),
    "linux/386": ("386", "386"),
    "linux/arm64": ("arm64", "arm64"),
    "linux/arm/v7": ("armv7", "armv7"),
}


def fetch(url, *, api=False):
    headers = {"User-Agent": "mihomo-docker"}
    # Never send the GitHub token to release downloads or another host.
    if api:
        if not url.startswith("https://api.github.com/"):
            raise ValueError("Authenticated requests must use api.github.com")
        headers["Accept"] = "application/vnd.github+json"
        if os.environ.get("GH_TOKEN"):
            headers["Authorization"] = "Bearer " + os.environ["GH_TOKEN"]
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=90) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise
        except (TimeoutError, urllib.error.URLError):
            if attempt == 2:
                raise
        time.sleep(2 ** attempt)
    raise RuntimeError("Download retries exhausted")


def api(path):
    return json.loads(fetch("https://api.github.com/" + path, api=True))


def checked_asset(asset):
    digest = asset.get("digest", "")
    if not isinstance(digest, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise ValueError(f"Missing upstream SHA-256: {asset['name']}")
    return asset


def download(asset):
    checked_asset(asset)
    data = fetch(asset["browser_download_url"])
    actual = "sha256:" + hashlib.sha256(data).hexdigest()
    if actual != asset["digest"] or len(data) != asset["size"]:
        raise ValueError(f"Upstream asset changed or failed verification: {asset['name']}")
    return data


def select_assets(release, version):
    result = {}
    for platform, (arch, _) in PLATFORMS.items():
        name = f"mihomo-linux-{arch}-{version}.gz"
        matches = [asset for asset in release["assets"] if asset["name"] == name]
        if len(matches) != 1:
            raise ValueError(f"Expected one complete upstream asset: {name}")
        result[platform] = checked_asset(matches[0])
    return result


def resolve(channel):
    endpoint = "latest" if channel == "release" else "tags/Prerelease-Alpha"
    release = api(f"repos/{UPSTREAM}/releases/{endpoint}")
    versions = [a for a in release["assets"] if a["name"] == "version.txt"]
    if len(versions) != 1 or release["draft"]:
        raise ValueError("Upstream release is incomplete")
    version = download(versions[0]).decode("ascii").strip()
    if channel == "release":
        if not re.fullmatch(r"v\d+\.\d+\.\d+", version) or version != release["tag_name"] or release["prerelease"]:
            raise ValueError("Invalid stable release version")
        ref = version
    else:
        match = re.fullmatch(r"alpha-([0-9a-f]{7,40})", version)
        if not match:
            raise ValueError("Invalid Alpha version")
        ref = match[1]
    revision = api(f"repos/{UPSTREAM}/commits/{ref}")["sha"]
    assets = select_assets(release, version)
    return {"channel": channel, "version": version, "revision": revision,
            "release_url": release["html_url"], "assets": assets}


def recipe_revision():
    project = Path(__file__).resolve().parents[1]
    recipe = hashlib.sha256()
    for name in ("Dockerfile", "LICENSE", ".dockerignore", "scripts/sync.py"):
        recipe.update(name.encode() + b"\0" + (project / name).read_bytes())
    recipe.update((project.parent / ".github/workflows/mihomo.yml").read_bytes())
    return recipe.hexdigest()


def fingerprint(plan, builder_revision):
    identity = {"version": plan["version"], "revision": plan["revision"],
                "builder": builder_revision,
                "assets": {p: a["digest"] for p, a in plan["assets"].items()}}
    return hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()


def run(*args):
    print("+ " + " ".join(str(a) for a in args), flush=True)
    subprocess.run(args, check=True)


def inspect(reference, *, optional=False):
    result = subprocess.run(["docker", "buildx", "imagetools", "inspect", reference, "--raw"],
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        if optional and any(s in result.stderr.lower() for s in ("not found", "manifest unknown", "404")):
            return None
        raise RuntimeError(f"Cannot inspect {reference}: {result.stderr}")
    return json.loads(result.stdout)


def platform_name(platform):
    name = f"{platform['os']}/{platform['architecture']}"
    variant = platform.get("variant", "")
    if variant and (name, variant) not in (("linux/amd64", "v1"), ("linux/arm64", "v8")):
        name += "/" + variant
    return name


def manifests(index):
    result = {}
    for item in index.get("manifests", []):
        key = platform_name(item["platform"])
        if key in result:
            raise ValueError(f"Duplicate platform: {key}")
        result[key] = item["digest"]
    if set(result) != set(PLATFORMS):
        raise ValueError(f"Unexpected platform list: {sorted(result)}")
    return result


def aliases(plan):
    return ["Alpha"] if plan["channel"] == "alpha" else [plan["version"], "latest"]


def up_to_date(images, plan, identity):
    for image in images:
        for tag in aliases(plan):
            index = inspect(f"{image}:{tag}", optional=True)
            if not index or index.get("annotations", {}).get(FINGERPRINT) != identity:
                return False
            descriptors = manifests(index)
            for level in (1, 2, 3):
                platform = "linux/amd64" + (f"/v{level}" if level > 1 else "")
                single = inspect(f"{image}:{tag}-amd64-v{level}", optional=True)
                # Helper tags are one-entry indexes, retaining their platform metadata.
                if not single or [m["digest"] for m in single.get("manifests", [])] != [descriptors[platform]]:
                    return False
    return True


def prepare(context, plan):
    dist = context / "dist"
    dist.mkdir()
    hashes = {}

    def core(item):
        platform, asset = item
        binary = gzip.decompress(download(asset))
        if binary[:4] != b"\x7fELF":
            raise ValueError(f"Not a Linux ELF executable: {asset['name']}")
        target = dist / PLATFORMS[platform][1] / "mihomo"
        target.parent.mkdir()
        target.write_bytes(binary)
        target.chmod(0o755)
        return platform, hashlib.sha256(binary).hexdigest()

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        hashes.update(pool.map(core, plan["assets"].items()))

    data_release = api("repos/MetaCubeX/meta-rules-dat/releases/tags/latest")
    config = dist / "config"
    config.mkdir()
    data_assets = {}
    for name in ("geoip.metadb", "geoip.dat", "geosite.dat"):
        matches = [a for a in data_release["assets"] if a["name"] == name]
        if len(matches) != 1:
            raise ValueError(f"Missing geodata: {name}")
        (config / name).write_bytes(download(matches[0]))
        data_assets[name] = matches[0]["digest"]
    metadata = {**plan, "binary_sha256": hashes, "geodata_sha256": data_assets,
                "source_url": f"https://github.com/{UPSTREAM}/tree/{plan['revision']}",
                "source_archive": f"https://github.com/{UPSTREAM}/archive/{plan['revision']}.tar.gz"}
    (dist / "upstream.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    for name in ("Dockerfile", "LICENSE", ".dockerignore"):
        shutil.copyfile(Path(__file__).resolve().parents[1] / name, context / name)


def build(context, images, plan, identity, builder_revision):
    source = "https://github.com/" + os.environ["GITHUB_REPOSITORY"]
    labels = {"org.opencontainers.image.source": source,
              "org.opencontainers.image.revision": builder_revision,
              "org.opencontainers.image.version": plan["version"],
              "org.opencontainers.image.licenses": "GPL-3.0-only",
              "org.opencontainers.image.description": "Official mihomo binaries repacked with amd64 v1/v2/v3",
              "io.github.mihomo-docker.upstream-revision": plan["revision"]}
    command = ["docker", "buildx", "build", "--pull", "--no-cache", "--platform", ",".join(PLATFORMS),
               "--provenance=false", "--metadata-file", str(context / "build.json"),
               "--annotation", f"index:{FINGERPRINT}={identity}",
               "--annotation", f"index:org.opencontainers.image.version={plan['version']}"]
    for name, value in labels.items():
        command += ["--label", f"{name}={value}"]
    # Both registries receive the same content-addressed index before any public alias changes.
    output = 'type=image,"name=' + ",".join(images) + '",push-by-digest=true,name-canonical=true,push=true,oci-mediatypes=true'
    run(*command, "--output", output, str(context))
    digest = json.loads((context / "build.json").read_text())["containerimage.digest"]
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise ValueError("Invalid build output digest")
    return digest


def promote(images, digest, plan, descriptors, identity):
    for image in images:
        for tag in aliases(plan):
            # Explicit helper tags also work with older Docker installations.
            for level in (1, 2, 3):
                platform = "linux/amd64" + (f"/v{level}" if level > 1 else "")
                run("docker", "buildx", "imagetools", "create", "--tag", f"{image}:{tag}-amd64-v{level}",
                    f"{image}@{descriptors[platform]}")
            run("docker", "buildx", "imagetools", "create", "--tag", f"{image}:{tag}", f"{image}@{digest}")
    if not up_to_date(images, plan, identity):
        raise ValueError("Published aliases failed verification")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", choices=("release", "alpha"), required=True)
    parser.add_argument("--plan", action="store_true", help="Read upstream metadata without building or publishing")
    args = parser.parse_args()
    try:
        plan = resolve(args.channel)
    except urllib.error.HTTPError as exc:
        endpoint = "latest" if args.channel == "release" else "tags/Prerelease-Alpha"
        if exc.code != 404 or exc.url != f"https://api.github.com/repos/{UPSTREAM}/releases/{endpoint}":
            raise
        print("No upstream release is published for this channel; withdrawal reconciliation will check existing tags.")
        return
    print(json.dumps({k: v for k, v in plan.items() if k != "assets"}, indent=2), flush=True)
    if args.plan:
        return
    builder_revision = os.environ["GITHUB_SHA"]
    identity = fingerprint(plan, recipe_revision())
    images = [os.environ["GHCR_IMAGE"], os.environ["DOCKERHUB_IMAGE"]]
    if os.environ.get("FORCE_SYNC") != "true" and up_to_date(images, plan, identity):
        print("All registries and aliases are already current.")
        return
    # tempfile removes all task-created downloads and build contexts even after failures.
    with tempfile.TemporaryDirectory(prefix="mihomo-docker-") as tmp:
        context = Path(tmp)
        prepare(context, plan)
        digest = build(context, images, plan, identity, builder_revision)
        descriptors = None
        for image in images:
            current = manifests(inspect(f"{image}@{digest}"))
            if descriptors is not None and descriptors != current:
                raise ValueError("Registry manifests differ")
            descriptors = current
        promote(images, digest, plan, descriptors, identity)
        summary = f"### {plan['version']}\n\nUpstream: `{plan['revision']}`\n\nIndex: `{digest}`\n\n"
        summary += "\n".join(f"- `{image}:{tag}`" for image in images for tag in aliases(plan)) + "\n"
        print(summary)
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as file:
                file.write(summary)


if __name__ == "__main__":
    main()

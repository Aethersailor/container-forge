#!/usr/bin/env python3
"""Prepare unchanged official dnscrypt-proxy Release binaries."""

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tarfile

UPSTREAM = "DNSCrypt/dnscrypt-proxy"
ARCHES = {"amd64": "x86_64", "arm64": "arm64"}


def api(path):
    return json.loads(subprocess.check_output(["gh", "api", path], text=True))


def main():
    dist = Path(__file__).resolve().parents[1] / "dist"
    dist.mkdir(exist_ok=True)
    release = api(f"repos/{UPSTREAM}/releases/latest")
    version = release["tag_name"]
    revision = api(f"repos/{UPSTREAM}/commits/{version}")["sha"]
    binaries = {}
    for arch, platform in ARCHES.items():
        name = f"dnscrypt-proxy-linux_{platform}-{version}.tar.gz"
        asset = next(item for item in release["assets"] if item["name"] == name)
        archive_path = dist / name
        subprocess.run(["curl", "--fail", "--location", "--silent", "--show-error", "--retry", "3", asset["browser_download_url"], "--output", str(archive_path)], check=True)
        archive_digest = "sha256:" + hashlib.sha256(archive_path.read_bytes()).hexdigest()
        if archive_digest != asset["digest"]:
            raise RuntimeError(f"Official archive digest mismatch: {name}")
        output = dist / arch
        output.mkdir(exist_ok=True)
        with tarfile.open(archive_path, "r:gz") as archive:
            members = {PurePosixPath(item.name).name: item for item in archive if item.isfile()}
            for filename in ("dnscrypt-proxy", "example-dnscrypt-proxy.toml", "LICENSE"):
                target = dist / filename if filename == "LICENSE" else output / filename
                target.write_bytes(archive.extractfile(members[filename]).read())
        archive_path.unlink()
        binary = output / "dnscrypt-proxy"
        binary.chmod(0o755)
        binaries[arch] = {"archive": name, "archive_sha256": archive_digest, "binary_sha256": "sha256:" + hashlib.sha256(binary.read_bytes()).hexdigest(), "url": asset["browser_download_url"]}
        print(f"MATCH {name} = {archive_digest}", flush=True)
    metadata = {"version": version, "revision": revision, "release_url": release["html_url"], "source_url": f"https://github.com/{UPSTREAM}/tree/{revision}", "binaries": binaries}
    (dist / "upstream.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write(f"version={version}\nrevision={revision}\n")
    print(f"Prepared official release {version} ({revision}).")


if __name__ == "__main__":
    main()

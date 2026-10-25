#!/usr/bin/env python3
"""Download unchanged official Release binaries for image packaging."""

import hashlib
import json
import os
from pathlib import Path
import subprocess

UPSTREAM = "heiher/hev-socks5-server"
ASSETS = {"amd64": "hev-socks5-server-linux-x86_64", "arm64": "hev-socks5-server-linux-arm64"}


def api(path):
    return json.loads(subprocess.check_output(["gh", "api", path], text=True))


def main():
    project = Path(__file__).resolve().parents[1]
    dist = project / "dist"
    dist.mkdir(exist_ok=True)
    release = api(f"repos/{UPSTREAM}/releases/latest")
    version = release["tag_name"]
    revision = api(f"repos/{UPSTREAM}/commits/{version}")["sha"]
    binaries = {}
    for arch, name in ASSETS.items():
        asset = next(item for item in release["assets"] if item["name"] == name)
        target = dist / arch / "hev-socks5-server"
        target.parent.mkdir(exist_ok=True)
        subprocess.run(["curl", "--fail", "--location", "--silent", "--show-error", "--retry", "3", asset["browser_download_url"], "--output", str(target)], check=True)
        digest = "sha256:" + hashlib.sha256(target.read_bytes()).hexdigest()
        if digest != asset["digest"]:
            raise RuntimeError(f"Official binary digest mismatch: {name}")
        target.chmod(0o755)
        binaries[arch] = {"asset": name, "sha256": digest, "url": asset["browser_download_url"]}
        print(f"MATCH {name} = {digest}", flush=True)
    license_text = subprocess.check_output(["gh", "api", f"repos/{UPSTREAM}/contents/LICENSE?ref={revision}", "-H", "Accept: application/vnd.github.raw+json"])
    (dist / "LICENSE").write_bytes(license_text)
    metadata = {"version": version, "revision": revision, "release_url": release["html_url"], "source_url": f"https://github.com/{UPSTREAM}/tree/{revision}", "binaries": binaries}
    (dist / "upstream.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write(f"version={version}\nrevision={revision}\n")
    print(f"Prepared official release {version} ({revision}).")


if __name__ == "__main__":
    main()

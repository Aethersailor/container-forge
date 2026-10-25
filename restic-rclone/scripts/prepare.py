#!/usr/bin/env python3
"""Package unchanged official restic and rclone Release binaries."""

import base64
import bz2
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import zipfile

PROJECTS = {"restic": ("restic/restic", "LICENSE"), "rclone": ("rclone/rclone", "COPYING")}
ARCHES = ("amd64", "arm64")


def api(path):
    return json.loads(subprocess.check_output(["gh", "api", path], text=True, encoding="utf-8"))


def main():
    dist = Path(__file__).resolve().parents[1] / "dist"
    (dist / "licenses").mkdir(parents=True, exist_ok=True)
    components = {}
    for name, (repository, license_path) in PROJECTS.items():
        release = api(f"repos/{repository}/releases/latest")
        tag = release["tag_name"]
        version = tag.removeprefix("v")
        revision = api(f"repos/{repository}/commits/{tag}")["sha"]
        license_data = api(f"repos/{repository}/contents/{license_path}?ref={revision}")
        (dist / "licenses" / f"{name}.LICENSE").write_bytes(base64.b64decode(license_data["content"]))
        binaries = {}
        for arch in ARCHES:
            filename = f"restic_{version}_linux_{arch}.bz2" if name == "restic" else f"rclone-{tag}-linux-{arch}.zip"
            asset = next(item for item in release["assets"] if item["name"] == filename)
            archive_path = dist / filename
            subprocess.run(["curl", "--fail", "--location", "--silent", "--show-error", "--retry", "3", asset["browser_download_url"], "--output", str(archive_path)], check=True)
            archive_digest = "sha256:" + hashlib.sha256(archive_path.read_bytes()).hexdigest()
            if archive_digest != asset["digest"]:
                raise RuntimeError(f"Official archive digest mismatch: {filename}")
            output = dist / arch
            output.mkdir(exist_ok=True)
            if name == "restic":
                binary = bz2.decompress(archive_path.read_bytes())
            else:
                with zipfile.ZipFile(archive_path) as archive:
                    member = next(item for item in archive.namelist() if PurePosixPath(item).name == "rclone")
                    binary = archive.read(member)
            executable = output / name
            executable.write_bytes(binary)
            executable.chmod(0o755)
            archive_path.unlink()
            binaries[arch] = {"archive": filename, "archive_sha256": archive_digest, "binary_sha256": "sha256:" + hashlib.sha256(binary).hexdigest(), "url": asset["browser_download_url"]}
            print(f"MATCH {filename} = {archive_digest}", flush=True)
        components[name] = {"version": version, "tag": tag, "revision": revision, "release_url": release["html_url"], "source_url": f"https://github.com/{repository}/tree/{revision}", "binaries": binaries}
    version = f"restic-{components['restic']['version']}-rclone-{components['rclone']['version']}"
    (dist / "upstream.json").write_text(json.dumps({"version": version, "components": components}, indent=2) + "\n", encoding="utf-8")
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write(f"version={version}\n")
        for name, component in components.items():
            output.write(f"{name}_version={component['version']}\n{name}_revision={component['revision']}\n")
    print(f"Prepared {version}.")


if __name__ == "__main__":
    main()

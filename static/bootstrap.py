from pathlib import Path
import subprocess
import shutil
import sys
import os
import xml.etree.ElementTree as ET

MANIFEST_REPO = "https://github.com/fuquery/.github.git"

def _clone_manifest(repo_url: str, target_dir: Path) -> Path:
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    if not target_dir.exists() or not any(target_dir.iterdir()):
        subprocess.check_call(["git", "clone", repo_url, str(target_dir)])
    return target_dir / "default.xml"

def _clone_projects(manifest_file: Path, topdir: Path):
    tree = ET.parse(manifest_file)
    root = tree.getroot()

    # Map remote name → fetch URL
    remotes = {r.get("name"): r.get("fetch") for r in root.findall("remote")}

    default_remote = root.find("default")
    default_remote_name = default_remote.get("remote") if default_remote is not None else None

    for proj in root.findall("project"):
        name = proj.get("name")
        if not name:
            continue
        path = topdir / (proj.get("path") or name)
        if path.exists() and any(path.iterdir()):
            continue
        remote_name = proj.get("remote") or default_remote_name
        fetch = proj.get("fetch") or remotes.get(remote_name)
        url = f"{fetch}/{name}.git" if fetch else f"https://github.com/fuquery/{name}.git"
        revision = proj.get("revision")
        path.parent.mkdir(parents=True, exist_ok=True)
        cmd = ["git", "clone", url, str(path)]
        if revision:
            cmd += ["--branch", revision]
        subprocess.check_call(cmd)

def _run_post_sync(manifests_dir: Path, topdir: Path):
    script = manifests_dir / "post-sync.py"
    if script.exists():
        subprocess.check_call([sys.executable, str(script), str(topdir)], cwd=str(topdir))

def main():
    topdir = Path.cwd()
    if shutil.which("repo"):
        subprocess.check_call(["repo", "init", "-u", MANIFEST_REPO], cwd=str(topdir))
        subprocess.check_call(
            ["repo", "sync", "-c", f"-j{os.cpu_count() or 1}", "--verify"], cwd=str(topdir)
        )
        return

    if shutil.which("git") is None:
        print("ERROR: Neither 'repo' nor 'git' is installed.", file=sys.stderr)
        sys.exit(1)

    manifests_dir = topdir / ".repo" / "manifests"
    manifest_file = _clone_manifest(MANIFEST_REPO, manifests_dir)
    _clone_projects(manifest_file, topdir)
    _run_post_sync(manifests_dir, topdir)

if __name__ == "__main__":
    main()

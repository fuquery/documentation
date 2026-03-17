# REQUIREMENTS: pyyaml, watchdog (optional for preview)


import argparse
import subprocess
import sys
import time
import threading
import http.server
import socketserver
import shutil
import os
from pathlib import Path

try:
    import yaml
except Exception:
    print("Missing required dependency 'PyYAML'. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


def parse_playbook(playbook_path: Path):
    data = yaml.safe_load(playbook_path.read_text(encoding='utf-8')) or {}
    paths = set()
    content = data.get('content', {})
    sources = []
    if isinstance(content, dict):
        sources = content.get('sources', []) or []
    for src in sources:
        if not isinstance(src, dict):
            continue
        for sp in src.get('start_paths', []) or src.get('start-paths', []) or []:
            paths.add((playbook_path.parent / sp).resolve())
    ui = data.get('ui', {}) or {}
    bundle = ui.get('bundle', {}) or {}
    url = bundle.get('url')
    if url:
        paths.add((playbook_path.parent / url).resolve())
    return sorted(paths)


def run_build(playbook: Path):
    print('Running: npx antora', playbook)
    try:
        subprocess.run(['npx', 'antora', str(playbook), "--stacktrace"], check=True, cwd=str(playbook.parent))
        subprocess.run(['ruby', str(Path(__file__).parent / 'rehighlight.rb'), 'build'], 
                        check=True, cwd=str(playbook.parent))
        shutil.copytree(
            playbook.parent / "static",
            playbook.parent / "build",
            dirs_exist_ok=True
        )
    except subprocess.CalledProcessError as e:
        print('Build failed with exit code', e.returncode)


def clean_site(site_dir: Path):
    if site_dir.exists():
        print('Removing', site_dir)
        shutil.rmtree(site_dir)
    else:
        print('Nothing to remove at', site_dir)


def find_site_dir(base: Path):
    if (path := base / 'build' / 'site').exists():
        return path
    return base / 'build'


def main():
    parser = argparse.ArgumentParser(description='Antora helper')
    parser.add_argument('--playbook', type=Path, default=Path.cwd() / 'antora-playbook.yml')
    parser.add_argument('--site-dir', type=Path)
    sub = parser.add_subparsers(dest='cmd')
    sub.add_parser('build')
    sub.add_parser('clean')
  
    args = parser.parse_args()
    playbook = args.playbook
    if not playbook.exists():
        print('Playbook not found at', playbook)
        sys.exit(2)
    site_dir = args.site_dir or find_site_dir(playbook.parent)

    if args.cmd == 'build':
        run_build(playbook)
    elif args.cmd == 'clean':
        clean_site(site_dir)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

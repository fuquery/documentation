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

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except Exception:
    Observer = None
    FileSystemEventHandler = None


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


def serve_dir(site_dir: Path, host: str, port: int):
    handler = http.server.SimpleHTTPRequestHandler
    os.chdir(site_dir)
    with socketserver.ThreadingTCPServer((host, port), handler) as httpd:
        print(f'Serving {site_dir} at http://{host}:{port}/')
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


def preview(playbook: Path, site_dir: Path, paths_to_watch, interval, host, port):
    if Observer is None or FileSystemEventHandler is None:
        print("Missing optional dependency 'watchdog'. Install with: pip3 install watchdog", file=sys.stderr)
        sys.exit(1)

    if not site_dir.exists():
        run_build(playbook)
    chosen_site = site_dir

    class Handler(FileSystemEventHandler):
        def __init__(self, build_cb, debounce=0.5):
            self.build_cb = build_cb
            self.debounce = debounce
            self._timer = None
            self._lock = threading.Lock()

        def _trigger_build(self):
            try:
                self.build_cb()
            finally:
                with self._lock:
                    self._timer = None

        def _debounce(self):
            with self._lock:
                if self._timer:
                    self._timer.cancel()
                t = threading.Timer(self.debounce, self._trigger_build)
                self._timer = t
                t.daemon = True
                t.start()

        # Trigger rebuild on create/delete/move/modify for files
        def on_created(self, event):
            if not event.is_directory:
                self._debounce()

        def on_deleted(self, event):
            if not event.is_directory:
                self._debounce()

        def on_moved(self, event):
            if not event.is_directory:
                self._debounce()

        def on_modified(self, event):
            if not event.is_directory:
                self._debounce()

    observer = Observer()
    handler = Handler(lambda *args: run_build(playbook), debounce=interval)
    for p in paths_to_watch:
        if p.exists() and p.is_dir():
            target = p
        elif p.exists():
            target = p.parent
        else:
            target = p
        try:
            print(p, paths_to_watch)
            observer.schedule(handler, str(target), recursive=True)
        except Exception:
            print(f'Warning: failed to watch {target}')

    os.chdir(chosen_site)
    httpd = socketserver.ThreadingTCPServer((host, port), http.server.SimpleHTTPRequestHandler)
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.start()
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('Shutting down...')
        observer.stop()
        observer.join()
        try:
            httpd.shutdown()
        except Exception:
            pass
        server_thread.join()
        try:
            httpd.server_close()
        except Exception:
            pass
        print('Stopping preview')


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
    preview_p = sub.add_parser('preview')
    preview_p.add_argument('--interval', type=float, default=1.0)
    preview_p.add_argument('--host', default='0.0.0.0')
    preview_p.add_argument('--port', type=int, default=8000)

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
    elif args.cmd == 'preview':
        paths = parse_playbook(playbook)
        preview(playbook, site_dir, paths, args.interval, args.host, args.port)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

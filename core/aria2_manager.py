import os
import shutil
import subprocess
import secrets
import time
from typing import Optional

try:
    import aria2p
    HAS_ARIA2P = True
except ImportError:
    HAS_ARIA2P = False


DEFAULT_RPC_PORT = 6800


def _find_aria2c() -> Optional[str]:
    # 1. Bundled binary next to this file's package root
    bin_path = os.path.join(
        os.path.dirname(__file__), '..', 'bin', 'aria2c.exe'
    )
    bin_path = os.path.normpath(bin_path)
    if os.path.isfile(bin_path):
        return bin_path
    # 2. System PATH
    return shutil.which('aria2c') or shutil.which('aria2c.exe')


class Aria2Manager:
    def __init__(
        self,
        rpc_port: int = DEFAULT_RPC_PORT,
        rpc_secret: str = '',
        max_concurrent: int = 3,
        connections_per_file: int = 16,
        speed_limit: int = 0,       # KB/s, 0 = unlimited
        proxy: str = '',
    ):
        self.rpc_port = rpc_port
        self.rpc_secret = rpc_secret or secrets.token_hex(16)
        self.max_concurrent = max_concurrent
        self.connections_per_file = connections_per_file
        self.speed_limit = speed_limit
        self.proxy = proxy
        self._proc: Optional[subprocess.Popen] = None
        self._api: Optional['aria2p.API'] = None
        self._aria2c_path: Optional[str] = None

    def start(self) -> None:
        if not HAS_ARIA2P:
            raise RuntimeError('aria2p is not installed. Run: pip install aria2p')

        self._aria2c_path = _find_aria2c()
        if not self._aria2c_path:
            raise FileNotFoundError(
                'aria2c not found. Place aria2c.exe in bin/ or add it to PATH.'
            )

        cmd = [
            self._aria2c_path,
            f'--enable-rpc=true',
            f'--rpc-listen-port={self.rpc_port}',
            f'--rpc-secret={self.rpc_secret}',
            f'--max-concurrent-downloads={self.max_concurrent}',
            f'--split={self.connections_per_file}',
            f'--max-connection-per-server={self.connections_per_file}',
            '--max-tries=3',
            '--retry-wait=5',
            '--continue=true',
            '--allow-overwrite=false',
            '--auto-file-renaming=true',
            '--check-certificate=false',
        ]
        if self.speed_limit > 0:
            cmd.append(f'--max-download-limit={self.speed_limit}K')
        if self.proxy:
            cmd.append(f'--all-proxy={self.proxy}')

        self._proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Give aria2c a moment to start RPC server
        time.sleep(1.0)
        self._api = aria2p.API(
            aria2p.Client(
                host='http://127.0.0.1',
                port=self.rpc_port,
                secret=self.rpc_secret,
            )
        )

    def stop(self) -> None:
        if self._proc and self._proc.poll() is None:
            try:
                if self._api:
                    self._api.client.call('aria2.shutdown', [])
            except Exception:
                pass
            self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        self._proc = None
        self._api = None

    def _check(self):
        if not self._api:
            raise RuntimeError('Aria2Manager not started. Call start() first.')

    def add(self, url: str, out_dir: str, filename: str = '', referer: str = '') -> str:
        """Add a download job. Returns aria2 GID."""
        self._check()
        options = {'dir': out_dir}
        if filename:
            options['out'] = filename
        if referer:
            options['referer'] = referer
        download = self._api.add_uris([url], options=options)
        return download.gid

    def apply_options(self, max_concurrent: int = None, connections_per_file: int = None, speed_limit: int = None, proxy: str = None) -> None:
        """Apply changed settings to the running aria2 process via RPC without restart."""
        self._check()
        global_opts = {}
        per_download_opts = {}
        if max_concurrent is not None:
            self.max_concurrent = max_concurrent
            global_opts['max-concurrent-downloads'] = str(max_concurrent)
        if speed_limit is not None:
            self.speed_limit = speed_limit
            global_opts['max-download-limit'] = f'{speed_limit}K' if speed_limit > 0 else '0'
        if proxy is not None:
            self.proxy = proxy
            global_opts['all-proxy'] = proxy
        if connections_per_file is not None:
            self.connections_per_file = connections_per_file
            per_download_opts['split'] = str(connections_per_file)
            per_download_opts['max-connection-per-server'] = str(connections_per_file)
        if global_opts:
            try:
                self._api.client.call('aria2.changeGlobalOption', [global_opts])
            except Exception:
                pass
        # Apply connections per file to all waiting/paused downloads
        if per_download_opts:
            try:
                downloads = self._api.get_downloads()
                for d in downloads:
                    if d.status in ('waiting', 'paused'):
                        self._api.client.call('aria2.changeOption', [d.gid, per_download_opts])
            except Exception:
                pass

    def pause(self, gid: str) -> None:
        self._check()
        try:
            self._api.client.call('aria2.pause', [gid])
        except Exception:
            pass

    def resume(self, gid: str) -> None:
        self._check()
        try:
            self._api.client.call('aria2.unpause', [gid])
        except Exception:
            pass

    def remove(self, gid: str, delete_file: bool = False) -> None:
        self._check()
        try:
            downloads = self._api.get_downloads()
            target = next((d for d in downloads if d.gid == gid), None)
            if target:
                file_path = target.files[0].path if target.files else None
                self._api.remove([target])
                if delete_file and file_path and os.path.exists(file_path):
                    os.remove(file_path)
                # Also remove .aria2 control file
                if file_path:
                    ctrl = file_path + '.aria2'
                    if os.path.exists(ctrl):
                        os.remove(ctrl)
        except Exception:
            pass

    def get_status(self, gid: str) -> dict:
        self._check()
        try:
            downloads = self._api.get_downloads()
            target = next((d for d in downloads if d.gid == gid), None)
            if target:
                return self._download_to_dict(target)
        except Exception:
            pass
        return {}

    def get_all(self) -> list:
        self._check()
        try:
            downloads = self._api.get_downloads()
            return [self._download_to_dict(d) for d in downloads]
        except Exception:
            return []

    @staticmethod
    def _download_to_dict(d) -> dict:
        total = d.total_length or 0
        completed = d.completed_length or 0
        speed = d.download_speed or 0
        eta = int((total - completed) / speed) if speed > 0 and total > completed else 0
        return {
            'gid': d.gid,
            'status': d.status,       # active|waiting|paused|error|complete|removed
            'filename': d.name,
            'total': total,
            'completed': completed,
            'speed': speed,           # bytes/s
            'eta': eta,               # seconds
            'percent': int(completed * 100 / total) if total > 0 else 0,
            'error': d.error_message or '',
        }

    @property
    def is_running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None
